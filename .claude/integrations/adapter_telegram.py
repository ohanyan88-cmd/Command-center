# -*- coding: utf-8 -*-
"""ADAPTER INT-TG — Telegram official Bot API (https://api.telegram.org/bot<token>/<method>), READ side.
No client session, no scraping, no UI automation. Long polling (getUpdates) by default so no public webhook is needed; webhook mode
is supported through `webhook_ingest()` (secret-token header check). The bot token lives OUTSIDE Git (int_secrets) and is
redacted from every error. Message content is UNTRUSTED DATA: it is normalized into records and flagged `trusted` only when the
chat/user is on the configured allowlist — it can never become an instruction or an approval.
Offset safety: every update is deduplicated by update_id in the local store (channel_events) and the confirmed offset is
acknowledged to Telegram (getUpdates offset) and persisted in the store's meta table, so a restart never replays old updates as new."""
import sys, pathlib, json, urllib.request, urllib.error, socket, re, datetime
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "skills"))
from contracts import IntegrationError
import normalize, int_secrets as _secrets

OPS = {"identity": "chat_identity", "chat.messages": "chat_message"}
API = "https://api.telegram.org"
TOKEN_RX = re.compile(r"bot\d{6,}:[A-Za-z0-9_-]{20,}")
OFFSET_KEY = "tg_update_offset"

def default_transport(url, body=None, timeout=35):
    """POST JSON (or GET). Returns (http_status, text). Token in the URL is redacted from every raised error."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET", headers={"Content-Type": "application/json", "User-Agent": "Deputy-Command-center"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try: body_t = e.read().decode("utf-8", "replace")
        except Exception: body_t = ""
        return e.code, body_t
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        raise IntegrationError("UNAVAILABLE", f"Telegram API unreachable: {redact(str(e))[:160]}", retryable=True)

def redact(text): return TOKEN_RX.sub("bot<secret>", _secrets.redact(text))

def _cfg(cfg):
    cfg = cfg if cfg is not None else _secrets.load_config("INT-TG")
    tok = str(cfg.get("bot_token") or "").strip()
    if not tok: raise IntegrationError("NOT_CONFIGURED", "no bot_token for INT-TG (CC_INT_TG_BOT_TOKEN or ~/.command-center/integrations/INT-TG.json)")
    if not re.match(r"^\d{6,}:[A-Za-z0-9_-]{20,}$", tok): raise IntegrationError("NOT_CONFIGURED", "bot_token has an unexpected shape")
    _secrets.register({"bot_token": tok}, "INT-TG")
    return cfg

def _ids(v):
    if v is None or v == "": return set()
    if isinstance(v, (list, tuple, set)): return {str(x).strip() for x in v if str(x).strip()}
    return {x.strip() for x in str(v).split(",") if x.strip()}

def call(method, params=None, cfg=None, transport=None):
    cfg = _cfg(cfg); url = f"{API}/bot{cfg['bot_token']}/{method}"
    status, text = (transport or default_transport)(url, params or {})
    if status >= 500: raise IntegrationError("UNAVAILABLE", f"Telegram API error http {status}", retryable=True)
    try: d = json.loads(text) if text else {}
    except ValueError: raise IntegrationError("MALFORMED_RESPONSE", f"non-JSON response (http {status}): {redact(text)[:80]}")
    if not isinstance(d, dict): raise IntegrationError("MALFORMED_RESPONSE", "response is not an object")
    if status == 401 or (d.get("error_code") == 401): raise IntegrationError("AUTH_FAILED", f"401: {redact(str(d.get('description')))[:120]}")
    if status == 403 or d.get("error_code") == 403: raise IntegrationError("PERMISSION_DENIED", f"403: {redact(str(d.get('description')))[:120]}")
    if status == 429 or d.get("error_code") == 429: raise IntegrationError("RATE_LIMITED", f"429: retry after {((d.get('parameters') or {}).get('retry_after'))}", retryable=True)
    if status >= 500: raise IntegrationError("UNAVAILABLE", f"Telegram API error http {status}", retryable=True)
    if not d.get("ok"): raise IntegrationError("UNAVAILABLE", f"{d.get('error_code')}: {redact(str(d.get('description')))[:120]}")
    if "result" not in d: raise IntegrationError("SCHEMA_CHANGED", "response without 'result'")
    return d["result"]

def identity(cfg=None, transport=None):
    cfg = _cfg(cfg); me = call("getMe", {}, cfg, transport)
    if not isinstance(me, dict) or "id" not in me or "username" not in me: raise IntegrationError("SCHEMA_CHANGED", "getMe result lacks id/username")
    exp = str(cfg.get("expected_bot_username") or "").lstrip("@").lower()
    if exp and str(me.get("username", "")).lower() != exp: raise IntegrationError("WRONG_TENANT", f"bot @{me.get('username')} ≠ expected @{exp}")
    return {"account_id": str(me["id"]), "display": f"@{me.get('username')}", "verified": bool(exp), "is_bot": bool(me.get("is_bot")), "note": None if exp else "expected_bot_username not configured — identity observed, not verified"}

def _store():
    import engine; return engine._store()

def _offset_get():
    try:
        con = _store()._connect()
        try:
            row = con.execute("SELECT value FROM meta WHERE key=?", (OFFSET_KEY,)).fetchone(); return int(row[0]) if row else None
        finally: con.close()
    except Exception: return None

def _offset_store(v):
    con = _store()._connect()
    try:
        con.execute("BEGIN IMMEDIATE"); con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (OFFSET_KEY, str(int(v)))); con.execute("COMMIT")
    finally: con.close()

def _attachments(m):
    out = []
    for k in ("document", "photo", "audio", "video", "voice", "sticker", "animation"):
        v = m.get(k)
        if v is None: continue
        if k == "photo" and isinstance(v, list): v = v[-1] if v else {}
        if isinstance(v, dict): out.append({"kind": k, "name": v.get("file_name"), "size": v.get("file_size"), "mime": v.get("mime_type")})
    return out

def parse_message(u, cfg):
    """One Telegram update → raw chat message dict (or None for non-message updates). Trust is decided here from the allowlist only."""
    m = u.get("message") or u.get("edited_message") or u.get("channel_post")
    if not isinstance(m, dict): return None
    chat = m.get("chat") or {}; frm = m.get("from") or {}
    chat_id = str(chat.get("id", "")); user_id = str(frm.get("id", ""))
    allowed_chats, allowed_users = _ids(cfg.get("allowed_chat_ids")), _ids(cfg.get("allowed_user_ids"))
    trusted = (chat_id in allowed_chats) or (user_id in allowed_users and chat.get("type") == "private")
    ts = m.get("date"); received = datetime.datetime.fromtimestamp(int(ts)).isoformat(timespec="seconds") if isinstance(ts, (int, float)) else None
    return {"chat_id": chat_id, "chat_title": chat.get("title") or (" ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x)) or chat.get("username"), "message_id": m.get("message_id"),
            "sender_id": user_id, "sender_name": " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x) or frm.get("username") or "", "text": m.get("text") or m.get("caption") or "",
            "message_type": "text" if m.get("text") else ("caption" if m.get("caption") else next((k for k in ("document", "photo", "audio", "video", "voice", "sticker", "animation", "location", "contact") if m.get(k)), "other")),
            "reply_to": str((m.get("reply_to_message") or {}).get("message_id") or "") or None, "received": received, "attachments": _attachments(m), "trusted": trusted, "update_id": u.get("update_id"), "edited": "edited_message" in u}

def _dedupe(records, channel="INT-TG"):
    """Persist each update once (INSERT OR IGNORE by update id) — the local evidence log carries ids, sender refs, timestamps and a short excerpt only."""
    st = _store(); fresh = []
    for r in records:
        oid = f"{channel}:upd:{r.get('update_id')}"
        res = st.record("channel_events", oid, {"channel": channel, "kind": "message", "update_id": r.get("update_id"), "chat_id": r["chat_id"], "message_id": r["message_id"], "sender_id": r["sender_id"], "received": r["received"], "trusted": r["trusted"], "excerpt": str(r.get("text") or "")[:300], "message_type": r["message_type"]})
        if res["status"] == "RECORDED": fresh.append(r)
    return fresh

def read(op, params=None, cfg=None, transport=None):
    params = params or {}
    if op not in OPS: raise IntegrationError("UNKNOWN_OPERATION", f"INT-TG has no operation {op}")
    cfg = _cfg(cfg); now = datetime.datetime.now().isoformat(timespec="seconds")
    if op == "identity":
        ident = identity(cfg, transport)
        return {"records": [normalize.chat_identity("INT-TG", ident, now)], "source_updated_at": now, "identity": {"addresses": [ident["display"]], "verified": ident["verified"], "note": ident.get("note")}, "partial": False, "notes": [], "kind": "chat_identity"}
    limit = int(params.get("limit") or 100)
    if limit < 1 or limit > 100: raise IntegrationError("BAD_PARAMS", "limit must be 1..100")
    if str(cfg.get("mode") or "polling").lower() == "webhook": raise IntegrationError("NOT_CONFIGURED", "INT-TG is in webhook mode: updates arrive through webhook_ingest(), not getUpdates")
    q = {"limit": limit, "timeout": int(params.get("timeout") or 0), "allowed_updates": ["message", "edited_message", "channel_post"]}
    off = _offset_get()
    if off is not None: q["offset"] = off
    res = call("getUpdates", q, cfg, transport)
    if not isinstance(res, list): raise IntegrationError("SCHEMA_CHANGED", "getUpdates result is not a list")
    raw = [parse_message(u, cfg) for u in res if isinstance(u, dict)]; raw = [r for r in raw if r]
    if res:
        newest = max(int(u.get("update_id", 0)) for u in res if isinstance(u, dict))
        _offset_store(newest + 1)                                         # acknowledged to Telegram on the NEXT poll: never replayed after a restart
    fresh = _dedupe(raw)
    trusted = [r for r in fresh if r["trusted"]]; untrusted = [r for r in fresh if not r["trusted"]]
    observe = bool(cfg.get("observe_unknown"))
    recs = [normalize.chat_message("INT-TG", r, now) for r in (fresh if observe else trusted)]
    notes = [f"{len(untrusted)} message(s) from chats/users outside the allowlist — {'observed as UNTRUSTED (observe_unknown=true)' if observe else 'dropped (not business evidence)'}"] if untrusted else []
    if len(res) - len(raw): notes.append(f"{len(res) - len(raw)} non-message update(s) ignored")
    ident = None
    return {"records": recs, "source_updated_at": max([r.get("source_updated_at") or "" for r in recs] or [""]) or None, "identity": ident, "partial": len(res) >= limit, "notes": notes, "kind": "chat_message", "retrieved_at": now}

def webhook_ingest(payload, headers=None, cfg=None):
    """Webhook mode ingestion: the X-Telegram-Bot-Api-Secret-Token header must equal the configured webhook_secret; then the update is deduplicated exactly like polling."""
    cfg = _cfg(cfg); headers = {str(k).lower(): v for k, v in (headers or {}).items()}
    secret = str(cfg.get("webhook_secret") or "")
    if not secret: raise IntegrationError("NOT_CONFIGURED", "webhook mode needs webhook_secret")
    if headers.get("x-telegram-bot-api-secret-token") != secret: raise IntegrationError("SIGNATURE_INVALID", "webhook secret token mismatch — update rejected")
    if not isinstance(payload, dict) or "update_id" not in payload: raise IntegrationError("MALFORMED_RESPONSE", "update lacks update_id")
    r = parse_message(payload, cfg)
    if not r: return {"accepted": False, "reason": "non-message update"}
    fresh = _dedupe([r])
    return {"accepted": bool(fresh), "duplicate": not fresh, "trusted": r["trusted"], "record": normalize.chat_message("INT-TG", r) if fresh and (r["trusted"] or cfg.get("observe_unknown")) else None}

def probe(cfg=None, transport=None): return identity(cfg, transport)
