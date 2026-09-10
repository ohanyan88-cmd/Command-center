# -*- coding: utf-8 -*-
"""INTEGRATION HEALTH — per-integration status persisted in the runtime state dir (.claude/state/integrations_health.json):
AVAILABLE · DEGRADED · UNAVAILABLE · AUTH_FAILED · PERMISSION_DENIED · SCHEMA_CHANGED · NOT_CONFIGURED, with last_check,
last_success (REAL reads only), last_error (redacted), consecutive_failures, success_count and distinct success days.
Fixture reads (tests/evals) are counted separately and never become evidence of a real connection."""
import json, pathlib, datetime, os, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import int_secrets as _secrets

def state_dir():
    try:
        sys.path.insert(0, str(HERE.parent / "skills")); import engine
        return pathlib.Path(engine.STATE_DIR)
    except Exception:
        return pathlib.Path(os.environ.get("SKILL_STATE_DIR") or (HERE.parent / "state"))

def _path(): return state_dir() / "integrations_health.json"

def load():
    p = _path()
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}

def _save(d):
    p = _path(); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8"); os.replace(tmp, p)

def record(integration_id, ok, *, status="AVAILABLE", code=None, reason=None, op=None, mode="REAL"):
    d = load(); now = datetime.datetime.now().isoformat(timespec="seconds"); today = now[:10]
    h = d.setdefault(integration_id, {"status": "NOT_CONFIGURED", "last_check": None, "last_success": None, "last_success_op": None, "last_error": None,
                                      "consecutive_failures": 0, "success_count": 0, "success_days": [], "fixture_reads": 0, "last_fixture_success": None})
    h["last_check"] = now; h["last_mode"] = mode
    if ok:
        h["status"] = status if status in ("AVAILABLE", "DEGRADED") else "AVAILABLE"
        if mode == "REAL":
            h["last_success"] = now; h["last_success_op"] = op; h["consecutive_failures"] = 0; h["success_count"] = h.get("success_count", 0) + 1
            if today not in h["success_days"]: h["success_days"] = (h["success_days"] + [today])[-30:]
        else:
            h["fixture_reads"] = h.get("fixture_reads", 0) + 1; h["last_fixture_success"] = now
    else:
        h["status"] = status; h["last_error"] = {"code": code, "reason": _secrets.redact(reason or "")[:300], "at": now, "op": op, "mode": mode}
        if mode == "REAL": h["consecutive_failures"] = h.get("consecutive_failures", 0) + 1
    _save(d); return h

def get(integration_id): return load().get(integration_id)

def snapshot():
    return {k: {kk: vv for kk, vv in v.items()} for k, v in load().items()}
