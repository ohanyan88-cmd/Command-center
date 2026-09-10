# -*- coding: utf-8 -*-
"""INTEGRATION LAYER — the ONLY path from a business skill to a live system:
    BUSINESS SKILL → BUSINESS QUERY → layer.query(integration_id, op, params) → adapter (fixed read op) → NORMALIZED envelope → PROVENANCE
Guarantees: read allowlist per integration (READ_ONLY_VIOLATION otherwise) · write intents blocked structurally (capability()) ·
health + last successful read persisted · minimal cache with visible freshness (LIVE/CACHED/STALE/UNAVAILABLE) · audit records
"what was queried" (op, param keys, counts, status) and never the payload · secret leakage fails closed (LEAK_PREVENTED) ·
fixture mode (COMMAND_CENTER_INTEGRATIONS_FIXTURE) for tests/evals, always labelled mode=FIXTURE and never counted as a real read."""
import sys, os, json, pathlib, hashlib, datetime, importlib, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "skills")); sys.path.insert(0, str(HERE.parent / "policy"))
import contracts as C, registry, health, int_secrets as _secrets

_CACHE = {}
_FIXTURE = {"path": None, "mtime": None, "data": None}

def _fixture():
    p = os.environ.get("COMMAND_CENTER_INTEGRATIONS_FIXTURE")
    if not p: return None
    pp = pathlib.Path(p)
    if not pp.exists(): return {}
    raw = pp.read_bytes(); m = hashlib.sha256(raw).hexdigest()          # content-addressed: two writes within one mtime tick never serve stale fixtures
    if _FIXTURE["path"] != p or _FIXTURE["mtime"] != m:
        try: _FIXTURE.update(path=p, mtime=m, data=json.loads(raw.decode("utf-8")))
        except ValueError: _FIXTURE.update(path=p, mtime=m, data={})
    return _FIXTURE["data"] or {}

def _audit(rec):
    try:
        import engine
        engine.audit({"execution_id": rec.get("execution_id") or hashlib.sha256(json.dumps(rec, sort_keys=True, default=str).encode()).hexdigest()[:12], "skill_id": f"<integration:{rec.get('integration_id')}>", **rec})
    except Exception: pass

def _cache_path(): return health.state_dir() / "integrations_cache.json"

def _cache_load():
    p = _cache_path()
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}

def _cache_save(d):
    p = _cache_path(); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(d, ensure_ascii=False, default=str), encoding="utf-8"); os.replace(tmp, p)

def _key(iid, op, params): return f"{iid}|{op}|" + hashlib.sha256(json.dumps(params or {}, sort_keys=True, default=str).encode()).hexdigest()[:16]

def _age(iso, default=10**9):
    """Seconds since iso (0 is a valid age); default when unparsable."""
    try: return int((datetime.datetime.now() - datetime.datetime.fromisoformat(iso)).total_seconds())
    except Exception: return default

def _pii_flags(records):
    """Unexpected RESTRICTED content inside live records (secrets, subscriber ids, private phone numbers) — flagged, never hidden."""
    try:
        import sensitive_scan as ss
        pol = ss.load_policy(); blob = json.dumps(records, ensure_ascii=False, default=str)
        fs = ss.scan_content("live-record", blob, pol, names=[])
        return sorted({f["rule"] for f in fs if f["class"] == "RESTRICTED" and not f["rule"].startswith("email_")})
    except Exception: return []

def capability(intent_text, integration_id=None):
    """Structured authority/capability verdict for an intent. Mission 4: every write intent → BLOCKED (AUTHORITY_EXCEEDED, WRITE_DISABLED)."""
    wi = C.detect_write_intent(intent_text)
    if wi:
        r = {"status": "BLOCKED", "code": "AUTHORITY_EXCEEDED", "capability": "WRITE_DISABLED", "write_intent": wi, "integration_id": integration_id, "mission": "READ_ONLY",
             "reason": f"{wi}: Deputy has no write capability toward any external system (Mission 4 READ-ONLY); the integration layer exposes no write operation — prepare it for Gev instead"}
        _audit({"integration_id": integration_id or "*", "op": "capability", "result_status": "BLOCKED", "code": "AUTHORITY_EXCEEDED", "write_intent": wi}); return r
    return {"status": "OK", "write_intent": None, "capability": "READ"}

def query(integration_id, op, params=None, *, use_cache=True, transport=None, intent=None, execution_id=None):
    params = dict(params or {})
    spec = registry.get(integration_id)
    if not spec:
        env = C.failure(integration_id, "UNKNOWN", op, "NOT_REGISTERED", f"integration {integration_id} is not declared in the registry")
        _audit({"integration_id": integration_id, "op": op, "result_status": "FAILED", "code": "NOT_REGISTERED"}); return env
    system = spec["system"]
    if intent:
        cap = capability(intent, integration_id)
        if cap["status"] == "BLOCKED": return {**C.failure(integration_id, system, op, "READ_ONLY_VIOLATION", cap["reason"]), **{"capability": cap}}
    if op not in spec["read_ops"]:
        code = "READ_ONLY_VIOLATION" if C.WRITE_OP_RX.search(op or "") else "UNKNOWN_OPERATION"
        env = C.failure(integration_id, system, op, code, f"{integration_id} exposes read operations {sorted(spec['read_ops'])} only; {op!r} refused")
        _audit({"integration_id": integration_id, "op": op, "result_status": "FAILED", "code": code, "execution_id": execution_id}); return env
    kind = spec["read_ops"][op]["kind"]; fr = spec["freshness"]; ttl = fr.get("cache_ttl_seconds") or 0; max_age = fr.get("max_age_seconds")
    k = _key(integration_id, op, params); h = health.get(integration_id) or {}
    fx = _fixture(); fixture_active = bool(fx) and integration_id in fx           # fixtures always win over the cache and are never written into it
    if use_cache and ttl and not fixture_active:
        c = _cache_load().get(k)
        if c and _age(c["retrieved_at"]) <= ttl:
            age = _age(c["retrieved_at"]); fresh = "STALE" if (max_age is not None and age > max_age) else "CACHED"
            env = C.envelope(integration_id, system, op, kind, c["records"], authority=spec["authority"], classification=spec["classification"], retrieved_at=c["retrieved_at"],
                             source_updated_at=c.get("source_updated_at"), freshness=fresh, identity=c.get("identity"), mode=c.get("mode", "REAL"), cache_age_seconds=age, notes=[f"served from cache ({age}s old)"])
            _audit({"integration_id": integration_id, "op": op, "param_keys": sorted(params), "result_status": "OK", "count": env["count"], "freshness": fresh, "execution_id": execution_id}); return env
    mode = "REAL"
    try:
        if fixture_active:
            mode = "FIXTURE"; entry = fx[integration_id]; entry = entry.get(op, entry) if isinstance(entry, dict) and (op in entry or "records" in entry or "error" in entry) else entry
            if not isinstance(entry, dict): raise C.IntegrationError("MALFORMED_RESPONSE", "fixture entry is not an object")
            if entry.get("error"): raise C.IntegrationError(entry["error"], entry.get("reason") or f"fixture-injected {entry['error']}", retryable=bool(entry.get("retryable")))
            if entry.get("exception"): raise RuntimeError(entry["exception"])
            raw = {"records": entry.get("records", []), "source_updated_at": entry.get("source_updated_at"), "identity": entry.get("identity"), "partial": bool(entry.get("partial")), "notes": list(entry.get("notes", []))}
        else:
            ad = importlib.import_module(spec["adapter"])
            cfg = _secrets.load_config(integration_id) if spec["auth"].get("secrets") else {}
            raw = ad.read(op, params, cfg, transport=transport) if spec["adapter"] == "adapter_bitrix24" else (ad.read(op, params, cfg, integration_id=integration_id) if spec["adapter"] == "adapter_outlook" else ad.read(op, params, cfg))
        records = raw.get("records", [])
        probs = C.check_records(kind, records)
        if probs: raise C.IntegrationError("SCHEMA_CHANGED", f"normalized records do not match schema {kind}: {probs[:2]}")
        records, dups = C.dedupe(records)
        flags = _pii_flags(records)
        notes = list(raw.get("notes", [])) + ([f"{len(dups)} duplicate record(s) removed"] if dups else []) + ([f"UNEXPECTED_PII flagged: {flags}"] if flags else [])
        env = C.envelope(integration_id, system, op, kind, records, authority=spec["authority"], classification=spec["classification"], retrieved_at=raw.get("retrieved_at") or C.now_iso(),
                         source_updated_at=raw.get("source_updated_at"), freshness="LIVE", partial=raw.get("partial"), notes=notes, pii_flags=flags, duplicates=dups, identity=raw.get("identity"), mode=mode)
        if _secrets.leaks(env):
            raise C.IntegrationError("LEAK_PREVENTED", "a configured secret value appeared in the envelope — result discarded")
        health.record(integration_id, True, status="DEGRADED" if raw.get("partial") else "AVAILABLE", op=op, mode=mode)
        if ttl and use_cache and mode == "REAL":
            cache = _cache_load(); cache[k] = {"retrieved_at": env["retrieved_at"], "records": records, "source_updated_at": env["source_updated_at"], "identity": env["identity"], "mode": mode}
            for kk in [x for x in cache if _age(cache[x]["retrieved_at"]) > max(ttl * 4, 3600)]: cache.pop(kk, None)
            _cache_save(cache)
        _audit({"integration_id": integration_id, "op": op, "param_keys": sorted(params), "result_status": "OK", "count": env["count"], "freshness": "LIVE", "mode": mode, "partial": env["partial"], "pii_flags": flags, "execution_id": execution_id})
        return env
    except C.IntegrationError as e:
        hs = C.HEALTH_FOR_CODE.get(e.code, "UNAVAILABLE"); reason = _secrets.redact(e.reason)
        health.record(integration_id, False, status=hs, code=e.code, reason=reason, op=op, mode=mode)
        stale = _cache_load().get(k)          # the last good read is always surfaced explicitly (stale_*), never as current data
        env = C.failure(integration_id, system, op, e.code, reason, health=hs, last_success=(health.get(integration_id) or {}).get("last_success"), detail=_secrets.redact(str(e.detail)) if e.detail else None,
                        retryable=e.retryable, stale_records=(stale or {}).get("records"), stale_retrieved_at=(stale or {}).get("retrieved_at"), mode=mode)
        _audit({"integration_id": integration_id, "op": op, "param_keys": sorted(params), "result_status": "FAILED", "code": e.code, "health": hs, "mode": mode, "execution_id": execution_id}); return env
    except Exception as e:
        reason = _secrets.redact(f"{type(e).__name__}: {e}")[:200]
        health.record(integration_id, False, status="UNAVAILABLE", code="UNAVAILABLE", reason=reason, op=op, mode=mode)
        env = C.failure(integration_id, system, op, "UNAVAILABLE", reason, last_success=(health.get(integration_id) or {}).get("last_success"), mode=mode)
        _audit({"integration_id": integration_id, "op": op, "param_keys": sorted(params), "result_status": "FAILED", "code": "UNAVAILABLE", "mode": mode, "execution_id": execution_id}); return env

def certification():
    p = HERE / "certification.json"
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None

def status():
    """Registry × health × certification — one line per integration, no payloads."""
    cert = (certification() or {}).get("integrations", {})
    out = []
    for iid, spec in registry.INTEGRATIONS.items():
        h = health.get(iid) or {}
        cfg_ok = True
        if spec["auth"].get("secrets"):
            try: cfg = _secrets.load_config(iid); cfg_ok = all(cfg.get(s) for s in spec["auth"]["secrets"]) if spec["adapter"] != "adapter_mikrobill" else False
            except Exception: cfg_ok = False
        out.append({"integration_id": iid, "system": spec["system"], "critical": spec["critical"], "read_ops": sorted(spec["read_ops"]), "write_ops": [], "configured": cfg_ok,
                    "health": h.get("status") or "NOT_CONFIGURED", "last_check": h.get("last_check"), "last_success": h.get("last_success"), "consecutive_failures": h.get("consecutive_failures", 0),
                    "last_error": h.get("last_error"), "certification": (cert.get(iid) or {}).get("state", "DECLARED"), "authority": spec["authority"]["name"], "classification": spec["classification"],
                    "freshness_rule": spec["freshness"]["rule"], "unblock": spec["unblock"]})
    return out

def health_line(env, spec=None):
    """Human line for the brief: never presents old data as current."""
    spec = spec or registry.get(env.get("integration_id")) or {}
    name = spec.get("system", env.get("integration_id"))
    if env.get("status") == "OK":
        f = env["freshness"]; ex = f" ({env.get('cache_age_seconds')}s cache)" if f == "CACHED" else (" STALE" if f == "STALE" else "")
        return f"{env['integration_id']} {name}: {f}{ex} · {env['count']} · read {env['retrieved_at'][11:16] if env.get('retrieved_at') else '?'}" + (" · FIXTURE" if env.get("mode") == "FIXTURE" else "")
    ls = env.get("last_success")
    return f"{env['integration_id']} {name}: {env.get('health', 'UNAVAILABLE')} ({env.get('code')}) — last successful read {ls[:16].replace('T', ' ') if ls else 'never'}"

def brief_context(today=None, *, horizon_days=3, mail_days=3, mail_limit=40, use_cache=True):
    """Live context for the Daily Brief / open loops: calendar (today + horizon), mail (recent), health of every critical integration."""
    today = today or datetime.date.today()
    if isinstance(today, str): today = datetime.date.fromisoformat(today)
    cal = query("INT-OL-CAL", "calendar.events", {"from": f"{today}T00:00:00", "to": f"{today + datetime.timedelta(days=horizon_days)}T23:59:59", "limit": 100}, use_cache=use_cache)
    mail = query("INT-OL-MAIL", "mail.list", {"folder": "Inbox", "since": f"{today - datetime.timedelta(days=mail_days)}T00:00:00", "limit": mail_limit}, use_cache=use_cache)
    envs = {"INT-OL-CAL": cal, "INT-OL-MAIL": mail}
    lines = [health_line(e) for e in envs.values()]
    unavailable = [iid for iid, e in envs.items() if e["status"] != "OK"]
    return {"today": today.isoformat(), "calendar": cal, "mail": mail, "health_lines": lines, "unavailable": unavailable, "critical_unavailable": [iid for iid in unavailable if (registry.get(iid) or {}).get("critical")],
            "declared_not_connected": [iid for iid, s in registry.INTEGRATIONS.items() if not (health.get(iid) or {}).get("last_success") and iid not in envs and iid != "INT-TASKS"],
            "mode": "FIXTURE" if any(e.get("mode") == "FIXTURE" for e in envs.values()) else "REAL"}

def live_source_status(kinds=("sales", "operations")):
    """Which live sources could answer a sales/operations question and where each stands — for honest BLOCKED answers."""
    want = {"sales": ["INT-B24", "INT-MB"], "operations": ["INT-B24", "INT-MB", "INT-TASKS"]}
    st = {s["integration_id"]: s for s in status()}
    out = {}
    for k in kinds:
        out[k] = [{"integration_id": i, "system": st[i]["system"], "certification": st[i]["certification"], "health": st[i]["health"], "last_success": st[i]["last_success"], "unblock": st[i]["unblock"]} for i in want.get(k, []) if i in st]
    return out
