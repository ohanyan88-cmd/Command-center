# -*- coding: utf-8 -*-
"""WRITE ADAPTER INT-OL-CAL / INT-OL-MAIL — Outlook desktop mutations through the integrity-pinned outlook_write.ps1.
Reached ONLY by the Action Runtime after Gev's approval. Verification never trusts the writer: it re-reads through the READ-ONLY reader
(outlook_read.ps1 -Op get / mail Sent folder). Timeouts and ambiguous COM outcomes raise ProviderUnknown (→ RESULT_UNKNOWN, reconcile first).
IMPLEMENTED ≠ VERIFIED_WRITE: no operation here is certified until a Gev-approved live action is executed and read back."""
import sys, os, json, pathlib, subprocess, hashlib, datetime, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "skills"))
import adapter_outlook, registry
from contracts import IntegrationError

WRITER = HERE / "outlook_write.ps1"
WRITER_SHA256 = "51bfec7a37d76364f9f772a37f28a07a2b39a1f6a3483af2055854b038c77f43"
OPS = ("calendar.create", "calendar.update", "calendar.cancel", "mail.draft", "mail.send")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")

def writer_sha256(): return hashlib.sha256(WRITER.read_bytes()).hexdigest() if WRITER.exists() else None
def writer_problems():
    if not WRITER.exists(): return ["outlook_write.ps1 missing"]
    if WRITER_SHA256 == "PIN_PENDING": return ["writer integrity pin not set"]
    if writer_sha256() != WRITER_SHA256: return ["outlook_write.ps1 does not match its integrity pin — modified writer refused"]
    return []

def _err():
    from actions import ProviderError, ProviderUnknown; return ProviderError, ProviderUnknown

def _run(args, timeout=90):
    ProviderError, ProviderUnknown = _err()
    ps = adapter_outlook.pwsh()
    if not ps: raise ProviderError("PowerShell not available — Outlook writer cannot run")
    wp = writer_problems()
    if wp: raise ProviderError("; ".join(wp))
    try: p = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(WRITER), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired: raise ProviderUnknown(f"Outlook writer exceeded {timeout}s — the mutation may or may not have happened")
    lines = [l for l in (p.stdout or "").splitlines() if l.strip()]
    if not lines: raise ProviderUnknown(f"writer produced no output (rc={p.returncode}) — outcome unknown")
    try: d = json.loads(lines[-1])
    except ValueError: raise ProviderUnknown("writer output not JSON — outcome unknown")
    if not d.get("ok"):
        if d.get("code") == "BAD_PARAMS": raise ProviderError(str(d.get("error")))
        raise ProviderError(f"Outlook refused: {str(d.get('error'))[:160]}")
    return d

def _get(entry_id):
    """Read-back through the READ-ONLY reader."""
    d = adapter_outlook._run(["-Op", "get", "-EntryId", entry_id])
    return d.get("item")

def precondition(op, params):
    eid = params.get("target_object_id")
    if not eid: return {"exists": False, "object": None}
    try: it = _get(eid)
    except IntegrationError as e:
        if e.code in ("UNAVAILABLE", "TOOL_UNAVAILABLE"): raise
        it = None
    if not it: return {"exists": False, "object": None}
    keys = ("subject", "start", "end", "location", "required", "to", "unread")
    return {"exists": True, "object": {k: it.get(k) for k in keys if k in it}}

def find_existing(op, params):
    """Idempotency / reconciliation through read-only ops: same subject+start in the calendar; same subject+recipient in Drafts/Sent."""
    try:
        if op == "calendar.create":
            f = params["start"][:10]; d = adapter_outlook.read("calendar.events", {"from": f"{f}T00:00:00", "to": f"{f}T23:59:59", "limit": 100}, {}, integration_id="INT-OL-CAL")
            for r in d["records"]:
                if r["title"].strip().lower() == str(params.get("subject", "")).strip().lower() and (r["start"] or "")[:16] == params["start"][:16]: return {"id": r["source_record_id"], **r}
            return None
        if op in ("mail.draft", "mail.send"):
            folder = "Sent" if op == "mail.send" else "Drafts"
            if folder == "Drafts": return None                       # the reader exposes Inbox/Sent only; drafts are verified by EntryID after execution
            d = adapter_outlook.read("mail.search", {"folder": folder, "query": str(params.get("subject", ""))[:60], "limit": 20}, {}, integration_id="INT-OL-MAIL")
            for r in d["records"]:
                if r["subject"].strip().lower() == str(params.get("subject", "")).strip().lower() and str(params.get("to", "")).lower() in (r.get("to") or "").lower(): return {"id": r["source_record_id"], **r}
            return None
        if op in ("calendar.update", "calendar.cancel"):
            it = _get(params.get("target_object_id"))
            if op == "calendar.cancel": return None if it and not it.get("cancelled") else ({"id": params.get("target_object_id"), "cancelled": True} if it is None or it.get("cancelled") else None)
            if it and all(str(it.get(k)) == str(v) for k, v in params.items() if k in ("subject", "start", "end", "location")): return {"id": params.get("target_object_id"), **it}
            return None
    except IntegrationError as e:
        raise RuntimeError(f"reconciliation read failed: {e.code}")
    return None

def execute(op, params):
    ProviderError, _ = _err()
    if op not in OPS: raise ProviderError(f"unknown Outlook operation {op}")
    args = ["-Op", op]
    if op.startswith("calendar."):
        for k, flag in (("subject", "-Subject"), ("start", "-Start"), ("end", "-End"), ("location", "-Location"), ("body", "-Body")):
            if params.get(k): args += [flag, str(params[k])]
        if params.get("participants"): args += ["-Participants", ";".join(params["participants"]) if isinstance(params["participants"], list) else str(params["participants"])]
        if params.get("target_object_id"): args += ["-EntryId", str(params["target_object_id"])]
        for k in ("start", "end"):
            if params.get(k) and not _ISO.match(str(params[k])): raise ProviderError(f"{k} must be ISO local time")
    else:
        if params.get("to"): args += ["-To", ";".join(params["to"]) if isinstance(params["to"], list) else str(params["to"])]
        if params.get("cc"): args += ["-Cc", ";".join(params["cc"]) if isinstance(params["cc"], list) else str(params["cc"])]
        if params.get("subject"): args += ["-Subject", str(params["subject"])]
        if params.get("body"): args += ["-Body", str(params["body"])]
        if params.get("reply_to_entry_id"): args += ["-ReplyToEntryId", str(params["reply_to_entry_id"])]
    d = _run(args)
    return {"ok": True, "id": d.get("entry_id") or d.get("conversation_id"), "subject": d.get("subject"), "start": d.get("start"), "end": d.get("end"), "to": d.get("to"), "submitted": d.get("submitted"), "cancelled": d.get("cancelled")}

def verify(op, params, result):
    """Independent read-back via the read-only reader; provider success alone never verifies."""
    try:
        if op == "mail.send":
            found = find_existing("mail.send", params)
            return {"verified": bool(found), "reason": "Sent Items evidence found" if found else "no Sent Items evidence for this recipient/subject", "evidence": found}
        eid = (result or {}).get("id") or params.get("target_object_id")
        it = _get(eid) if eid else None
        if op == "calendar.cancel":
            ok = it is None or bool(it.get("cancelled")); return {"verified": ok, "reason": "event absent/cancelled on read-back" if ok else "event still present", "evidence": {"id": eid, "cancelled": ok}}
        if not it: return {"verified": False, "reason": f"item {eid} not found on read-back", "evidence": None}
        checks = {"subject": params.get("subject"), "start": params.get("start"), "end": params.get("end")} if op.startswith("calendar") else {"subject": params.get("subject"), "to": ";".join(params["to"]) if isinstance(params.get("to"), list) else params.get("to")}
        diffs = {k: (v, it.get(k)) for k, v in checks.items() if v and str(it.get(k, ""))[:len(str(v))].lower() != str(v).lower()}
        return {"verified": not diffs, "reason": ("field mismatch: " + ", ".join(diffs)) if diffs else "read-back matches", "evidence": {"id": eid, **{k: it.get(k) for k in ("subject", "start", "end", "to", "location")}}}
    except IntegrationError as e:
        return {"verified": False, "reason": f"read-back unavailable ({e.code}) — cannot verify", "evidence": None}
