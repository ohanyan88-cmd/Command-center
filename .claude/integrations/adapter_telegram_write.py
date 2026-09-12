# -*- coding: utf-8 -*-
"""WRITE ADAPTER INT-TG — outbound Telegram messages through the official Bot API (sendMessage). Reached ONLY by the Action Runtime
after Gev's approval; the exact chat, reply target and text are bound to the approval fingerprint.
VERIFICATION TRUTH: the Bot API returns the sent Message object (message_id) — that is PROVIDER ACCEPTANCE, not independent evidence:
a bot cannot read back its own sent messages. verify() therefore returns independent=False and the runtime records the action as
EXECUTED_UNVERIFIED with code NO_INDEPENDENT_READBACK (canonical PARTIAL). Full VERIFIED_WRITE would require a second source
(a human/second-account confirmation of the message in the chat) — documented, never faked."""
import sys, pathlib, datetime
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "skills"))
import adapter_telegram as R
from contracts import IntegrationError

OPS = ("chat.send", "chat.reply")

def _err():
    from actions import ProviderError, ProviderUnknown; return ProviderError, ProviderUnknown

def _cfg(params):
    cfg = R._cfg(None) if not params.get("_cfg") else params["_cfg"]
    return cfg

def _allowed(cfg, chat_id):
    return str(chat_id) in R._ids(cfg.get("allowed_chat_ids")) or str(chat_id) in R._ids(cfg.get("allowed_user_ids"))

def precondition(op, params):
    """The target chat must be on the allowlist (no message to an arbitrary chat); a reply target must be known."""
    ProviderError, _ = _err()
    try: cfg = R._cfg(None)
    except IntegrationError as e: raise ProviderError(f"{e.code}: {e.reason}")
    chat = str(params.get("chat_id") or "")
    if not chat: return {"exists": False, "object": None}
    if not _allowed(cfg, chat): raise ProviderError(f"PERMISSION_DENIED: chat {chat} is not on the configured allowlist — no outbound message to unknown chats")
    obj = {"chat_id": chat, "allowed": True}
    if op == "chat.reply": obj["reply_to"] = str(params.get("reply_to_message_id") or "")
    return {"exists": True, "object": obj}

def find_existing(op, params):
    """No provider read-back for sent bot messages: idempotency is enforced by the runtime key; reconciliation looks at the local outbound log only."""
    try:
        import engine; st = engine._store()
        rows = st.list("channel_events", where="op_id LIKE ?", args=(f"INT-TG:out:%",))
        for r in rows:
            if r.get("idem_key") and r["idem_key"] == params.get("_idem_key") and r.get("provider_message_id"): return {"id": r["provider_message_id"], "provider_accepted": True, "independent": False, **{k: r.get(k) for k in ("chat_id", "at")}}
    except Exception: pass
    return None

def execute(op, params):
    ProviderError, ProviderUnknown = _err()
    if op not in OPS: raise ProviderError(f"unknown Telegram operation {op}")
    try: cfg = R._cfg(None)
    except IntegrationError as e: raise ProviderError(f"{e.code}: {e.reason}")
    chat = str(params.get("chat_id") or ""); text = str(params.get("text") or "")
    if not chat or not text: raise ProviderError("BAD_PARAMS: chat_id and text are required")
    if not _allowed(cfg, chat): raise ProviderError(f"PERMISSION_DENIED: chat {chat} not on the allowlist")
    body = {"chat_id": chat, "text": text[:4096], "disable_web_page_preview": True}
    if op == "chat.reply":
        if not params.get("reply_to_message_id"): raise ProviderError("BAD_PARAMS: reply_to_message_id required for chat.reply")
        body["reply_parameters"] = {"message_id": int(params["reply_to_message_id"])}
    at = datetime.datetime.now().isoformat(timespec="seconds")
    try: res = R.call("sendMessage", body, cfg, params.get("_transport"))
    except IntegrationError as e:
        if e.code in ("UNAVAILABLE", "TIMEOUT", "RATE_LIMITED"): raise ProviderUnknown(f"{e.code}: {e.reason} — the message may or may not have been accepted")
        raise ProviderError(f"{e.code}: {e.reason}")
    mid = str((res or {}).get("message_id") or "")
    if not mid: raise ProviderUnknown("Telegram accepted the request but returned no message_id — outcome unknown")
    try:
        import engine; engine._store().record("channel_events", f"INT-TG:out:{chat}:{mid}", {"channel": "INT-TG", "kind": "outbound", "chat_id": chat, "provider_message_id": mid, "idem_key": params.get("_idem_key"), "at": at, "op": op, "excerpt": text[:300]})
    except Exception: pass
    return {"ok": True, "id": mid, "chat_id": chat, "at": at, "provider_accepted": True}

def verify(op, params, result):
    """Honest: provider acceptance only. No independent read-back exists for a bot's own sent message."""
    mid = (result or {}).get("id")
    return {"verified": False, "independent": False, "provider_accepted": bool(mid),
            "reason": "PROVIDER_ACCEPTED — Telegram Bot API returned message_id but offers no independent read-back of a bot's sent message; full certification needs a second-source confirmation (recipient or Gev sees the message in the chat)",
            "evidence": {"provider_message_id": mid, "chat_id": (result or {}).get("chat_id"), "at": (result or {}).get("at")}}
