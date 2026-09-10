# -*- coding: utf-8 -*-
"""Skill executors — REAL logic over real data (Tasks.xlsx, hardened SQLite state store, memory files).
Contract: fn(inputs: dict, skill: dict, reg: dict) -> dict with 'status' in
  EXECUTED | VERIFIED | RECORDED | DUPLICATE | BLOCKED | ASSISTED  (+ data).
Never fabricates numbers: skills needing data the runtime lacks return BLOCKED with a reason.
"""
import json, re, datetime, pathlib, hashlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def _st():
    import engine
    return engine._store()
XLSX = ROOT / "Tasks.xlsx"
SHEET = "ԱՌԱՋԱԴՐԱՆՔՆԵՐ"
HDR_ROW, FIRST_ROW = 12, 13
COL = {"id": 2, "task": 3, "status": 6, "comment": 7, "due": 11, "owner": 12}
OPEN_STATUSES = {"Ընթացքում", "Չսկսված", "Պարզ չէ", "Սպասում"}
CLOSED_STATUSES = {"Արված", "Չեղարկված"}
HEAD = "Գև"
HY = ["երկուշաբթի","երեքշաբթի","չորեքշաբթի","հինգշաբթի","ուրբաթ","շաբաթ","կիրակի"]
CAUSE_TYPES = ["PERSON","PROCESS","SYSTEM","POLICY","CAPACITY","TRAINING","MANAGEMENT","INCENTIVE","DATA"]
MATERIAL = re.compile(r"(price|pricing|սակագ|salary|comp|աշխատավարձ|hire|fire|terminat|ազատ|contract|պայմանագ|public|հրապարակ|refund|concession|discount|զեղչ|policy|irreversib)", re.I)

class ExecError(Exception): pass

def _today(inputs):
    t = inputs.get("today")
    return datetime.date.fromisoformat(t) if isinstance(t, str) else (t or datetime.date.today())

def _norm(t): return re.sub(r"\s+", " ", str(t).lower().strip())
def _opid(*p): return hashlib.sha256("|".join(_norm(x) for x in p).encode("utf-8")).hexdigest()[:16]
def _date(v):
    if isinstance(v, datetime.datetime): return v.date()
    if isinstance(v, datetime.date): return v
    if isinstance(v, str):
        try: return datetime.date.fromisoformat(v[:10])
        except ValueError: return None
    return None

# ───────────────────────── source of truth ─────────────────────────
def load_tasks(path=None):
    import openpyxl
    p = pathlib.Path(path) if path else XLSX
    if not p.exists(): raise ExecError(f"source missing: {p.name}")
    wb = openpyxl.load_workbook(p, data_only=True)
    if SHEET not in wb.sheetnames: raise ExecError(f"sheet {SHEET} missing")
    ws = wb[SHEET]
    hdr = [ws.cell(row=HDR_ROW, column=c).value for c in (COL["id"], COL["task"], COL["status"], COL["due"], COL["owner"])]
    if hdr[0] != "№" or not hdr[1] or not hdr[2]:
        raise ExecError(f"schema drift at header row {HDR_ROW}: {hdr}")
    tasks = []
    for r in range(FIRST_ROW, ws.max_row + 1):
        n = ws.cell(row=r, column=COL["id"]).value
        task = ws.cell(row=r, column=COL["task"]).value
        if not isinstance(n, int) or not task: continue
        st = str(ws.cell(row=r, column=COL["status"]).value or "").strip()
        tasks.append({"id": n, "task": str(task).strip(), "status": st,
                      "comment": str(ws.cell(row=r, column=COL["comment"]).value or "").strip(),
                      "due": _date(ws.cell(row=r, column=COL["due"]).value),
                      "owner": str(ws.cell(row=r, column=COL["owner"]).value or "").strip(),
                      "open": st not in CLOSED_STATUSES, "row": r})
    return tasks

def _tasks(inputs):
    """Tasks from inputs (user-supplied OR merged back from an earlier chain step, where dates
    arrive as ISO strings) are normalized to the canonical shape; otherwise loaded from the xlsx."""
    if "tasks" in inputs and isinstance(inputs["tasks"], list):
        out = []
        for t in inputs["tasks"]:
            if not isinstance(t, dict) or "task" not in t: continue
            st = str(t.get("status", "")).strip()
            out.append({**t, "due": _date(t.get("due")), "status": st,
                        "owner": str(t.get("owner", "")).strip(), "open": st not in CLOSED_STATUSES})
        return out
    return load_tasks(inputs.get("path"))

def _ser(t): return {**t, "due": t["due"].isoformat() if t["due"] else None}

# ───────────────────────── A. executive control ─────────────────────────
def task_management(inputs, skill=None, reg=None):
    tasks = _tasks(inputs)
    if inputs.get("task_id") is not None:
        t = next((x for x in tasks if x["id"] == int(inputs["task_id"])), None)
        if not t: return {"status": "BLOCKED", "reason": f"task {inputs['task_id']} not found"}
        return {"status": "EXECUTED", "task": _ser(t), "source": XLSX.name}
    f = inputs.get("status_filter")
    sel = [t for t in tasks if (not f or t["status"] == f)]
    return {"status": "EXECUTED", "count": len(sel), "open": sum(t["open"] for t in sel),
            "tasks": [_ser(t) for t in sel], "source": XLSX.name}

def deadline_management(inputs, skill=None, reg=None):
    today = _today(inputs); tasks = [t for t in _tasks(inputs) if t["open"]]
    b = {"overdue": [], "today": [], "tomorrow": [], "upcoming": [], "no_deadline": []}
    for t in tasks:
        if not t["due"]: b["no_deadline"].append(_ser(t)); continue
        n = (t["due"] - today).days
        key = "overdue" if n < 0 else "today" if n == 0 else "tomorrow" if n == 1 else "upcoming"
        b[key].append({**_ser(t), "days": n})
    for k in b: b[k].sort(key=lambda x: (x.get("due") or "9999", x["id"]))
    return {"status": "EXECUTED", "today": today.isoformat(), "buckets": b,
            "counts": {k: len(v) for k, v in b.items()}, "source": XLSX.name}

def _counterpart(owner):
    """Who holds the ball. Returns (holder, is_other)."""
    o = owner.strip()
    if not o or o == "—": return ("", False)
    if "→" in o: holder = o.split("→")[0].strip()
    else: holder = o
    is_other = HEAD not in holder or o.isupper()
    if o.isupper(): holder = o
    if is_other and not holder: holder = "UNKNOWN"
    return (holder, is_other)

def waiting_for_tracking(inputs, skill=None, reg=None):
    today = _today(inputs); items = []
    for t in _tasks(inputs):
        if not t["open"]: continue
        holder, other = _counterpart(t["owner"])
        if other:
            items.append({**_ser(t), "from": holder, "expected_by": t["due"].isoformat() if t["due"] else None,
                          "days_left": (t["due"] - today).days if t["due"] else None})
    groups = {}
    for it in items: groups.setdefault(it["from"], []).append(it)
    return {"status": "EXECUTED", "count": len(items), "waiting_for": items, "by_counterpart": groups}

def executive_prioritization(inputs, skill=None, reg=None):
    today = _today(inputs); ranked = []
    for t in _tasks(inputs):
        if not t["open"]: continue
        score, why = 0, []
        if t["due"]:
            n = (t["due"] - today).days
            if n < 0: score += 100 + min(-n, 30); why.append(f"overdue {-n}d")
            elif n == 0: score += 80; why.append("due today")
            elif n == 1: score += 60; why.append("due tomorrow")
            else: score += max(0, 40 - n); why.append(f"due in {n}d")
        else: score += 10; why.append("no deadline")
        if "ԿՐԻՏԻԿ" in t["task"].upper() or "CRITICAL" in t["task"].upper(): score += 50; why.append("marked critical")
        holder, other = _counterpart(t["owner"])
        if other and t["owner"].isupper(): score += 15; why.append(f"ball with {holder}")
        ranked.append({**_ser(t), "score": score, "why": ", ".join(why)})
    ranked.sort(key=lambda x: (-x["score"], x["id"]))
    for i, r in enumerate(ranked):
        r["P"] = "P1" if (i < 5 and r["score"] >= 60) else "P2" if r["score"] >= 40 else "P3" if r["score"] >= 15 else "P4"
    return {"status": "EXECUTED", "ranked": ranked, "p1_count": sum(r["P"]=="P1" for r in ranked)}

def daily_briefing(inputs, skill=None, reg=None):
    today = _today(inputs)
    dl = deadline_management(inputs); wf = waiting_for_tracking(inputs); pr = executive_prioritization(inputs)
    b = dl["buckets"]
    head_actions = [r for r in pr["ranked"] if r["P"] == "P1" and not _counterpart(r["owner"])[1]]
    decisions = [r for r in pr["ranked"] if r["owner"].isupper()]
    brief = {"status": "EXECUTED", "date": today.isoformat(), "weekday": HY[today.weekday()],
             "top_priorities": pr["ranked"][:5], "head_actions": head_actions[:5], "decisions_pending": decisions,
             "deadlines_today": b["today"], "overdue": b["overdue"], "tomorrow": b["tomorrow"],
             "waiting_for": wf["waiting_for"], "no_deadline": b["no_deadline"],
             "counts": dl["counts"], "source": XLSX.name,
             "data_gaps": ["sales KPIs: UNKNOWN (no live feed)", "ops KPIs: UNKNOWN (no live feed)"]}
    return brief

def end_of_day_control(inputs, skill=None, reg=None):
    today = _today(inputs); tasks = _tasks(inputs); dl = deadline_management(inputs)
    done_today = [_ser(t) for t in tasks if not t["open"] and t["due"] == today]
    slipped = dl["buckets"]["overdue"] + [x for x in dl["buckets"]["today"]]
    return {"status": "EXECUTED", "date": today.isoformat(), "completed_today": done_today, "not_completed": slipped,
            "decisions_pending": [_ser(t) for t in tasks if t["open"] and t["owner"].isupper()],
            "waiting_for": waiting_for_tracking(inputs)["waiting_for"], "tomorrow": dl["buckets"]["tomorrow"]}

def weekly_review(inputs, skill=None, reg=None):
    dl = deadline_management(inputs)
    return {"status": "ASSISTED", "actions_overdue": dl["buckets"]["overdue"], "open_count": sum(dl["counts"].values()),
            "sales": "UNKNOWN — no sales data source", "operations": "UNKNOWN — no ops data source",
            "note": "Skeleton only; sales/ops sections require supplied datasets."}

def meeting_preparation(inputs, skill=None, reg=None):
    if not inputs.get("meeting"): return {"status": "BLOCKED", "reason": "required input 'meeting' missing"}
    dl = deadline_management(inputs); wf = waiting_for_tracking(inputs); pr = executive_prioritization(inputs)
    topic = _norm(inputs.get("topic", inputs["meeting"]))
    related = [r for r in pr["ranked"] if any(w in _norm(r["task"]) for w in topic.split() if len(w) > 3)]
    return {"status": "EXECUTED", "meeting": inputs["meeting"], "purpose": inputs.get("purpose", "UNKNOWN — supply"),
            "participants": inputs.get("participants", "UNKNOWN — supply"),
            "previous_decisions": decision_memory({}, None, None)["decisions"][-5:],
            "open_actions": related or pr["ranked"][:5], "overdue": dl["buckets"]["overdue"],
            "waiting_for": wf["waiting_for"], "decisions_required": [r for r in pr["ranked"] if r["owner"].isupper()],
            "numbers": "UNKNOWN — no KPI feed; supply if required",
            "talking_points": [f"Close: {r['task']}" for r in (related or pr['ranked'][:3])]}

def delegation_design(inputs, skill=None, reg=None):
    instr = inputs.get("instruction") or inputs.get("notes") or inputs.get("recommendation")
    if not instr: return {"status": "BLOCKED", "reason": "instruction missing"}
    owner = (inputs.get("owner") or "").strip(); issues = []
    vague = {"sales team","operations","management","it","թիմ","բաժին"}
    if not owner: issues.append("owner missing — one named person required")
    elif _norm(owner) in vague or len(owner.split()) > 3: issues.append(f"owner '{owner}' is not a single named person")
    due = _date(inputs.get("deadline"))
    if not due: issues.append("deadline missing")
    draft = {"task": instr.strip(), "owner": owner or "<NAME REQUIRED>", "deadline": due.isoformat() if due else "<DATE REQUIRED>",
             "expected_output": inputs.get("expected_output", "<define: what is delivered, in what form>"),
             "bitrix_ready": not issues}
    return {"status": "EXECUTED" if not issues else "ASSISTED", "draft": draft, "issues": issues}

def _append_state(table, record, key_fields):
    """Idempotent write through the hardened store: the DB decides RECORDED vs DUPLICATE (no read-then-append race)."""
    oid = _opid(*[record.get(k, "") for k in key_fields])
    r = _st().record(table, oid, record)
    return {"status": r["status"], "op_id": oid, "record": r.get("record"), "existing": r.get("existing"), "store": table}

def _read_state(table):
    return _st().list(table)

def commitment_tracking(inputs, skill=None, reg=None):
    text = (inputs.get("text") or "").strip()
    if not text: return {"status": "BLOCKED", "reason": "text missing"}
    due = _date(inputs.get("due"))
    rec = {"text": text, "owner": inputs.get("owner", HEAD), "due": due.isoformat() if due else None,
           "condition": inputs.get("condition"), "state": "OPEN"}
    r = _append_state("commitments", rec, ["text", "owner", "due"])
    r["scheduler_available"] = False
    r["note"] = "Recorded and will be surfaced by the session-start brief; no autonomous timer exists in this runtime."
    return r

def commitment_memory(inputs, skill=None, reg=None):
    items = [c for c in _read_state("commitments") if c.get("state", "OPEN") == "OPEN"]
    return {"status": "EXECUTED", "count": len(items), "commitments": items}

def decision_logging(inputs, skill=None, reg=None):
    d = (inputs.get("decision") or "").strip()
    if not d: return {"status": "BLOCKED", "reason": "decision missing"}
    rec = {"decision": d, "reason": inputs.get("reason", ""), "owner": inputs.get("owner", HEAD),
           "effective_date": inputs.get("effective_date"), "follow_up": inputs.get("follow_up"), "date": _today(inputs).isoformat()}
    return _append_state("decisions", rec, ["decision", "owner"])

def decision_memory(inputs, skill=None, reg=None):
    return {"status": "EXECUTED", "decisions": _read_state("decisions")}

def reminder_intelligence(inputs, skill=None, reg=None):
    due = _date(inputs.get("due")); item = inputs.get("item")
    if not item: return {"status": "BLOCKED", "reason": "item missing"}
    if not due: return {"status": "BLOCKED", "reason": "unparseable or missing due date"}
    today = _today(inputs); prep = inputs.get("prep_items") or []
    plan = []
    for off, label in ((7,"Preparation may be required"),(3,"Check readiness"),(1,"Confirm materials/people"),(0,"Action reminder")):
        d = due - datetime.timedelta(days=off)
        if d >= today: plan.append({"date": d.isoformat(), "label": label, "past": False})
    plan.append({"date": (due + datetime.timedelta(days=1)).isoformat(), "label": "Check completion; follow up if incomplete", "past": False})
    text = f"{item} — {due.isoformat()} ({HY[due.weekday()]})." + (" Preparation still required: " + "; ".join(prep) if prep else "")
    return {"status": "EXECUTED", "item": item, "due": due.isoformat(), "plan": plan, "reminder_text": text,
            "scheduler_available": False,
            "honesty": "No autonomous scheduler in this runtime: checkpoints are surfaced via the session-start brief, not fired automatically."}

def follow_up_management(inputs, skill=None, reg=None):
    dl = deadline_management(inputs); wf = waiting_for_tracking(inputs); today = _today(inputs)
    fu = []
    for t in dl["buckets"]["overdue"]:
        holder, other = _counterpart(t["owner"])
        fu.append({"id": t["id"], "item": t["task"], "owner": holder or HEAD, "since": t["due"], "days": -t["days"],
                   "next_action": f"Follow up with {holder or HEAD} today: status + new date"})
    for w in wf["waiting_for"]:
        if not any(f["id"] == w["id"] for f in fu):
            fu.append({"id": w["id"], "item": w["task"], "owner": w["from"], "since": w.get("expected_by"),
                       "next_action": f"Ask {w['from']} for status; escalate if no answer by {w.get('expected_by') or 'EOD'}"})
    return {"status": "EXECUTED", "count": len(fu), "follow_ups": fu}

def escalation_management(inputs, skill=None, reg=None):
    item = inputs.get("item")
    if not item: return {"status": "BLOCKED", "reason": "item missing"}
    block = {"problem": item, "impact": inputs.get("impact", "UNKNOWN — supply"), "owner": inputs.get("owner", "UNKNOWN"),
             "deadline_status": inputs.get("deadline_status", "UNKNOWN"), "done_so_far": inputs.get("done_so_far", "UNKNOWN"),
             "head_action": inputs.get("head_action", "Decide: escalate / re-assign / extend deadline")}
    return {"status": "EXECUTED", "escalation": block}

def decision_support(inputs, skill=None, reg=None):
    issue = inputs.get("issue") or inputs.get("analysis") or inputs.get("description")
    if not issue: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "issue (or analysis/description) missing"}
    if not isinstance(issue, str): issue = json.dumps(issue, ensure_ascii=False)[:400]
    opts = inputs.get("options") or []
    rec = inputs.get("recommendation") or ("INSUFFICIENT DATA — supply options/facts" if not opts else f"Evaluate {len(opts)} options against facts; recommendation pending facts")
    return {"status": "ASSISTED", "decision_needed": {"issue": issue, "context": inputs.get("context", "UNKNOWN"),
            "options": opts, "recommendation": rec, "risk_of_delay": inputs.get("risk_of_delay", "UNKNOWN"),
            "deadline": inputs.get("deadline", "UNKNOWN"), "approver": HEAD,
            "owner": inputs.get("owner", "<NAME>"), "head_action": inputs.get("head_action", "Decide/approve")}, "label": "DERIVED"}

def approval_management(inputs, skill=None, reg=None):
    lvl = inputs.get("action_level"); ladder = (reg or {}).get("authority_ladder", [])
    if lvl not in ladder: return {"status": "BLOCKED", "reason": f"unknown action_level {lvl!r}"}
    needs = lvl in ("EXECUTE_EXTERNAL", "EXECUTE_MATERIAL")
    if needs and not inputs.get("approval_token"):
        return {"status": "BLOCKED", "code": "APPROVAL_REQUIRED", "action_level": lvl, "approved": False}
    return {"status": "EXECUTED", "action_level": lvl, "approved": True, "approval_required": needs}

def authority_checking(inputs, skill=None, reg=None):
    import engine
    lvl = inputs.get("action_level"); target = inputs.get("skill_id", skill["skill_id"] if skill else None)
    s = (reg or {}).get("_index", {}).get(target) if reg else None
    if not s: return {"status": "BLOCKED", "reason": f"unknown skill {target}"}
    a = engine.authority_check(reg, s, lvl, inputs.get("approval_token"))
    return {"status": "EXECUTED" if a["ok"] else "BLOCKED", "allowed": a["ok"], "reason": a.get("reason"), "code": a.get("code")}

def policy_checking(inputs, skill=None, reg=None):
    a = inputs.get("action", "")
    hits = MATERIAL.findall(a)
    return {"status": "EXECUTED", "material": bool(hits), "matched": hits,
            "policy": "Requires explicit Head approval before execution" if hits else "No material-action policy triggered"}

def risk_classification(inputs, skill=None, reg=None):
    a = _norm(inputs.get("action", "")); mat = bool(MATERIAL.search(a))
    irreversible = any(w in a for w in ("delete","ջնջ","terminate","send","ուղարկ","publish","pay","վճար"))
    level = "CRITICAL" if (mat and irreversible) else "HIGH" if mat else "MEDIUM" if irreversible else "LOW"
    return {"status": "EXECUTED", "risk": level, "material": mat, "irreversible": irreversible}

def sensitivity_check(inputs, skill=None, reg=None):
    t = inputs.get("text", ""); import engine
    flagged = bool(engine.SENSITIVE.search(t)) or bool(re.search(r"\b\d{9,}\b", t))
    return {"status": "EXECUTED", "sensitive": flagged, "advice": "Redact before logging/sending" if flagged else "OK"}

def information_classification(inputs, skill=None, reg=None):
    items = inputs.get("items") or ([inputs["content"]] if inputs.get("content") else [])
    if isinstance(items, str): items = [items]
    if not items: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "content/items missing"}
    out = []
    rules = [("DECISION", r"(decide|approve|հաստատ|որոշ|should we|pros/cons)"),
             ("ACTION", r"(please|do|send|prepare|fix|արա|ուղարկ|պատրաստ|make|need you to|by (today|tomorrow))"),
             ("DELEGATE", r"(հանձնարար|assign|delegate|թող .* անի|let .* do)"),
             ("MONITOR", r"(watch|monitor|keep an eye|հետև|track)"),
             ("IGNORE", r"(spam|unsubscribe|lottery)")]
    for it in items:
        cls = "FYI"
        for name, pat in rules:
            if re.search(pat, it, re.I): cls = name; break
        out.append({"item": it, "class": cls})
    return {"status": "EXECUTED", "classified": out}

def source_verification(inputs, skill=None, reg=None):
    p = pathlib.Path(inputs.get("path") or XLSX)
    if not p.is_absolute(): p = ROOT / p
    if not p.exists(): return {"status": "BLOCKED", "code": "SOURCE_MISSING", "reason": f"source missing: {p.name}", "path": str(p)}
    age_h = (datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 3600
    res = {"status": "VERIFIED", "path": p.name, "exists": True, "age_hours": round(age_h, 1),
           "stale": age_h > 72, "schema_ok": None}
    if p.suffix == ".xlsx" and (p.name == XLSX.name or inputs.get("schema") == "tasks"):
        try: load_tasks(p); res["schema_ok"] = True
        except ExecError as e: res.update(status="BLOCKED", code="SCHEMA_DRIFT", schema_ok=False, reason=str(e))
        except Exception as e: res.update(status="BLOCKED", code="UNREADABLE_SOURCE", schema_ok=False, reason=f"{type(e).__name__}: {e}")
    return res

def source_reconciliation(inputs, skill=None, reg=None):
    srcs = inputs.get("sources")
    if not srcs or len(srcs) < 2: return {"status": "BLOCKED", "reason": "need >=2 sources: [{name,value,date?,authoritative?}]"}
    vals = {str(s.get("value")) for s in srcs}
    if len(vals) == 1: return {"status": "EXECUTED", "contradiction": False, "value": srcs[0]["value"]}
    dated = [s for s in srcs if s.get("date")]
    newest = max(dated, key=lambda s: s["date"]) if dated else None
    auth = next((s for s in srcs if s.get("authoritative")), None)
    return {"status": "EXECUTED", "contradiction": True,
            "report": [f"{s['name']} says {s['value']}" + (f" ({s['date']})" if s.get('date') else "") for s in srcs],
            "newest": newest["name"] if newest else "UNKNOWN", "authoritative": auth["name"] if auth else "UNKNOWN",
            "impact": inputs.get("impact", "UNKNOWN — assess"), "verify": "Confirm with source owner before using either figure",
            "chosen": None}

def confidence_labeling(inputs, skill=None, reg=None):
    claims = inputs.get("claims") or []
    if not claims: return {"status": "BLOCKED", "reason": "claims missing"}
    out = [{"claim": c.get("text", c) if isinstance(c, dict) else c,
            "label": (c.get("label") if isinstance(c, dict) and c.get("label") in ("CONFIRMED","DERIVED","UNVERIFIED","UNKNOWN") else "UNVERIFIED")}
           for c in claims]
    return {"status": "EXECUTED", "labeled": out}

def completion_verification(inputs, skill=None, reg=None):
    """evidence_spec: {type: file_exists|task_status|state_record, ...}. Returns ATTEMPTED/EXECUTED/VERIFIED."""
    spec = inputs.get("evidence_spec")
    if not spec: return {"status": "BLOCKED", "reason": "evidence_spec missing"}
    kind = spec.get("type")
    if kind == "file_exists":
        p = pathlib.Path(spec["path"]); p = p if p.is_absolute() else ROOT / p
        ok = p.exists()
        return {"status": "VERIFIED" if ok else "ATTEMPTED", "verified": ok, "evidence": {"path": str(p), "exists": ok}}
    if kind == "task_status":
        t = next((x for x in _tasks(inputs) if x["id"] == int(spec["task_id"])), None)
        if not t: return {"status": "BLOCKED", "reason": "task not found"}
        ok = t["status"] == spec.get("expected", "Արված")
        return {"status": "VERIFIED" if ok else "ATTEMPTED", "verified": ok, "evidence": {"task": t["id"], "status": t["status"]}}
    if kind == "state_record":
        table = str(spec["store"]).replace(".jsonl", ""); ok = _st().get(table, spec.get("op_id")) is not None
        return {"status": "VERIFIED" if ok else "ATTEMPTED", "verified": ok, "evidence": {"store": spec["store"], "found": ok}}
    return {"status": "BLOCKED", "reason": f"unknown evidence type {kind!r}"}

def audit_logging(inputs, skill=None, reg=None):
    import engine
    rec = inputs.get("record")
    if not isinstance(rec, dict): return {"status": "BLOCKED", "reason": "record must be a dict"}
    out = engine.audit({"skill_id": "audit_logging", "manual": True, **rec})
    return {"status": "RECORDED", "store": "audit", "op_id": out["audit_id"]}

def open_loops(inputs, skill=None, reg=None):
    dl = deadline_management(inputs); wf = waiting_for_tracking(inputs); cm = commitment_memory({}); dm = decision_memory({})
    pending = [t for t in _tasks(inputs) if t["open"] and t["owner"].isupper()]
    return {"status": "EXECUTED", "open_tasks": sum(dl["counts"].values()), "overdue": dl["buckets"]["overdue"],
            "waiting_for": wf["waiting_for"], "open_commitments": cm["commitments"],
            "decisions_pending": [_ser(t) for t in pending], "decisions_logged": len(dm["decisions"])}

def memory_retrieval(inputs, skill=None, reg=None):
    q = _norm(inputs.get("query", inputs.get("context", ""))); hits = []
    if not q: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "query missing (what to find)"}
    files = list((ROOT).glob("*.md")) + list((ROOT / ".claude" / "docs").glob("*.md")) + list((ROOT / "01_Active").rglob("*.md")) + [ROOT / "00_Inbox" / "Input.md"]
    mem = pathlib.Path.home() / ".claude/projects/c--Users-Admin-Desktop-Daily-check/memory"
    if mem.exists(): files += list(mem.glob("*.md"))
    for f in files:
        try: txt = f.read_text(encoding="utf-8")
        except Exception: continue
        for i, line in enumerate(txt.splitlines()):
            if q and q in _norm(line): hits.append({"file": f.name, "line": i + 1, "text": line.strip()[:160]})
    return {"status": "EXECUTED", "query": q, "hits": hits[:25], "count": len(hits)}

def document_extraction(inputs, skill=None, reg=None):
    p = inputs.get("path")
    if not p: return {"status": "BLOCKED", "reason": "path missing"}
    p = pathlib.Path(p); p = p if p.is_absolute() else ROOT / p
    if not p.exists(): return {"status": "BLOCKED", "code": "SOURCE_MISSING", "path": str(p)}
    if p.suffix == ".docx":
        import docx; d = docx.Document(p)
        paras = [x.text.strip() for x in d.paragraphs if x.text.strip()]
        return {"status": "EXECUTED", "paragraphs": len(paras), "tables": len(d.tables), "head": paras[:10]}
    if p.suffix == ".xlsx":
        import openpyxl; wb = openpyxl.load_workbook(p, read_only=True)
        return {"status": "EXECUTED", "sheets": wb.sheetnames}
    return {"status": "EXECUTED", "text_head": p.read_text(encoding="utf-8", errors="replace")[:1000]}

# ───────────────────────── analysis (supplied data only; never live) ─────────────────────────
def analysis_on_supplied_data(inputs, skill=None, reg=None):
    key = next((k for k in ("sales_data","ops_data","dataset","performance_data") if k in inputs), None)
    if not key or not inputs[key]:
        return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": f"{skill['skill_id'] if skill else 'analysis'}: no dataset supplied; this runtime has no live feed",
                "label": "UNKNOWN"}
    data = inputs[key]
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        return {"status": "BLOCKED", "code": "INVALID_DATA", "reason": "dataset must be a list of dict rows"}
    nums = {}
    for r in data:
        for k, v in r.items():
            if isinstance(v, (int, float)): nums.setdefault(k, []).append(v)
    stats = {k: {"n": len(v), "sum": round(sum(v), 2), "min": min(v), "max": max(v), "mean": round(sum(v)/len(v), 2)} for k, v in nums.items()}
    trend = {}
    for k, v in nums.items():
        if len(v) >= 2: trend[k] = {"first": v[0], "last": v[-1], "change_pct": round((v[-1]-v[0])/v[0]*100, 1) if v[0] else None}
    return {"status": "ASSISTED", "rows": len(data), "stats": stats, "trend": trend, "label": "DERIVED",
            "note": "Computed from supplied data only; interpretation requires domain confirmation."}

def performance_gap_diagnosis(inputs, skill=None, reg=None):
    d = inputs.get("performance_data") or inputs.get("description")
    if not d: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "performance_data/description required; never attribute cause without evidence"}
    text = _norm(json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d)
    signals = {"PROCESS": r"(process|ընթացակարգ|handoff|no procedure|unclear steps)", "SYSTEM": r"(system|համակարգ|tool|crm|billing|software|bug)",
               "CAPACITY": r"(overload|too much|ծանրաբեռն|capacity|no time)", "TRAINING": r"(training|doesn't know how|ուսուց|չգիտի)",
               "DATA": r"(data|wrong numbers|տվյալ|missing data)", "INCENTIVE": r"(bonus|incentive|commission|պրեմիա|no reason to)",
               "MANAGEMENT": r"(no feedback|unclear priorities|manager|ղեկավար)", "POLICY": r"(policy|rule|կանոն|not allowed)",
               "PERSON": r"(attitude|refus|absent|late again|չի ուզում)"}
    hits = {k: bool(re.search(p, text)) for k, p in signals.items()}
    likely = [k for k in CAUSE_TYPES if hits.get(k)]
    return {"status": "ASSISTED", "candidate_causes": likely or ["UNKNOWN — insufficient evidence"],
            "rule": "Do not assume a PERSON problem; verify PROCESS/SYSTEM/CAPACITY first.", "label": "DERIVED"}

def root_cause_analysis(inputs, skill=None, reg=None):
    desc = inputs.get("description") or inputs.get("symptom")
    if not desc: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "description/symptom required"}
    whys = inputs.get("whys") or []
    chain = [{"why": i + 1, "answer": w} for i, w in enumerate(whys[:5])]
    root = whys[-1] if len(whys) >= 3 else None
    return {"status": "ASSISTED", "symptom": desc, "why_chain": chain, "root_cause": root or "UNKNOWN — fewer than 3 whys supplied",
            "corrective_action": inputs.get("corrective_action", "PENDING root cause"),
            "cause_type_candidates": performance_gap_diagnosis({"description": " ".join([desc] + whys)})["candidate_causes"],
            "label": "DERIVED" if root else "UNVERIFIED"}

def structured_analysis(inputs, skill=None, reg=None):
    src = inputs.get("description") or inputs.get("analysis")
    if not src: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "description/analysis required"}
    return {"status": "ASSISTED", "frame": {"what_happened": src if isinstance(src, str) else "see analysis", "why_it_matters": "UNKNOWN — supply impact",
            "root_cause": inputs.get("root_cause", "UNKNOWN"), "options": inputs.get("options", []),
            "recommendation": inputs.get("recommendation", "PENDING"), "owner": inputs.get("owner", "<NAME>"),
            "deadline": inputs.get("deadline", "<DATE>"), "head_action": inputs.get("head_action", "Decide/approve")}, "label": "DERIVED"}

def executive_reporting(inputs, skill=None, reg=None):
    dl = deadline_management(inputs); wf = waiting_for_tracking(inputs)
    red = len(dl["buckets"]["overdue"]); yellow = len(dl["buckets"]["today"]) + len(wf["waiting_for"])
    snapshot = "RED" if red else "YELLOW" if yellow else "GREEN"
    return {"status": "EXECUTED", "snapshot": snapshot, "red": dl["buckets"]["overdue"], "yellow_today": dl["buckets"]["today"],
            "waiting": wf["waiting_for"], "sales": "UNKNOWN — no feed", "operations": "UNKNOWN — no feed",
            "decisions_required": [t for t in dl["buckets"]["today"] + dl["buckets"]["overdue"] if t["owner"].isupper()]}

# ───────────────────────── communication ─────────────────────────
INTERNAL = [("Ես ու Claude", "Գև"), ("Ես + Claude", "Գև"), ("Claude", ""), ("pull անել", ""), ("push", ""), ("Bitrix-ում ստուգել", "")]
def communication_quality_check(inputs, skill=None, reg=None):
    t = inputs.get("content") or inputs.get("text") or ""
    if not t: return {"status": "BLOCKED", "reason": "content missing"}
    issues = []
    if re.search(r"(^|\W)Ես(\W|$)", t) and "Գև" not in t: issues.append("uses «Ես» — outgoing must be in «Գև» voice")
    for a, _ in INTERNAL:
        if a.lower() in t.lower(): issues.append(f"internal wording present: {a!r}")
    if not re.search(r"\d{2}-\d{2}|\d{4}-\d{2}-\d{2}|ուրբաթ|հինգշաբթի|վաղը|այսօր|tomorrow|today", t, re.I): issues.append("no deadline/date")
    return {"status": "EXECUTED", "ok": not issues, "issues": issues}

def outgoing_communication(inputs, skill=None, reg=None):
    t = inputs.get("content") or ""
    if not t: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": "content missing"}
    kind = inputs.get("kind") or "message"
    if kind == "follow_up" and not re.search(r"(status|կարգավիճակ|new date|նոր ժամկետ|\?)", t, re.I): t = t.rstrip() + "\nStatus?  ·  New date?  ·  Blocker?"
    clean = t
    for a, b in INTERNAL: clean = clean.replace(a, b)
    clean = re.sub(r"(^|\W)Ես(\W)", r"\1Գև\2", clean)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    q = communication_quality_check({"content": clean})
    return {"status": "EXECUTED", "kind": kind, "recipient": inputs.get("recipient"), "draft": clean, "quality": q,
            "requires_head_ok_before_send": True, "send_tool_available": False}

def drafting(inputs, skill=None, reg=None):
    c = inputs.get("content")
    if not c: return {"status": "BLOCKED", "reason": "content missing"}
    kind = inputs.get("kind") or "summary"
    tmpl = {"summary": "WHAT HAPPENED: {c}\nWHY IT MATTERS: <supply>\nRECOMMENDATION: <supply>\nHEAD ACTION: <supply>",
            "meeting": "Decisions:\nTasks (owner/deadline):\nFollow-up date:\nSource: {c}"}
    if kind not in tmpl: return {"status": "BLOCKED", "code": "MISSING_INPUT", "reason": f"unknown kind {kind!r}; use summary|meeting"}
    return {"status": "ASSISTED", "kind": kind, "draft": tmpl[kind].format(c=c), "requires_head_ok_before_send": True}

# ───────────────────────── output validation ─────────────────────────
def validate_output(skill_id, result):
    if not isinstance(result, dict) or "status" not in result: return False, "result must be dict with status"
    if result["status"] not in ("EXECUTED","VERIFIED","RECORDED","DUPLICATE","BLOCKED","ASSISTED","ATTEMPTED"):
        return False, f"bad status {result['status']}"
    if result["status"] == "BLOCKED" and not (result.get("reason") or result.get("code")): return False, "BLOCKED without reason"
    checks = {
        "executive_prioritization": lambda r: all(x.get("P") in ("P1","P2","P3","P4") for x in r.get("ranked", [])) and r.get("p1_count", 0) <= 5,
        "deadline_management": lambda r: set(r.get("buckets", {})) == {"overdue","today","tomorrow","upcoming","no_deadline"},
        "daily_briefing": lambda r: all(k in r for k in ("top_priorities","overdue","deadlines_today","waiting_for","counts")),
        "task_management": lambda r: "tasks" in r or "task" in r,
        "commitment_tracking": lambda r: "op_id" in r and "scheduler_available" in r,
        "reminder_intelligence": lambda r: r.get("scheduler_available") is False and "plan" in r,
        "waiting_for_tracking": lambda r: all(i.get("from") for i in r.get("waiting_for", [])),
        "follow_up_management": lambda r: all(f.get("owner") and f.get("next_action") for f in r.get("follow_ups", [])),
        "escalation_management": lambda r: set(r.get("escalation", {})) >= {"problem","impact","owner","deadline_status","done_so_far","head_action"},
        "source_reconciliation": lambda r: r.get("chosen") is None if r.get("contradiction") else True,
        "completion_verification": lambda r: r["status"] in ("VERIFIED","ATTEMPTED") and "verified" in r,
        "delegation_design": lambda r: "draft" in r and "issues" in r,
        "decision_support": lambda r: "decision_needed" in r and r["decision_needed"].get("approver") == HEAD,
        "management_communication": lambda r: r.get("requires_head_ok_before_send") is True and "Claude" not in r.get("draft", ""),
        "decision_logging": lambda r: "op_id" in r and r.get("store") == "decisions",
        "source_verification": lambda r: "stale" in r and "exists" in r,
        "risk_classification": lambda r: r.get("risk") in ("LOW","MEDIUM","HIGH","CRITICAL"),
        "approval_management": lambda r: "approved" in r,
        "authority_checking": lambda r: "allowed" in r,
    }
    fn = checks.get(skill_id)
    if fn and result["status"] not in ("BLOCKED",) and not fn(result): return False, f"validation rule failed for {skill_id}"
    return True, None

def verify_completion(skill_id, result, inputs=None):
    """COMPLETION VERIFICATION — re-read the state a skill claims to have produced. Returns (ok, detail).
    A claim that cannot be re-observed is VERIFICATION_FAILED, never success."""
    inputs = inputs or {}
    if not isinstance(result, dict): return False, "no result"
    st = result.get("status")
    try:
        if st in ("RECORDED", "DUPLICATE") and result.get("store"):
            found = _st().get(result["store"], result.get("op_id"))
            return (found is not None), f"{result['store']}:{result.get('op_id')} {'present' if found else 'ABSENT'} on re-read"
        if skill_id in ("task_management",) and "tasks" in result:
            n = len(_tasks(inputs)); return (n == result.get("count")), f"re-read {n} rows vs reported {result.get('count')}"
        if skill_id == "deadline_management":
            n = len([t for t in _tasks(inputs) if t["open"]]); tot = sum(result.get("counts", {}).values())
            return (n == tot), f"re-read {n} open vs bucketed {tot}"
        if skill_id == "daily_briefing":
            n = len([t for t in _tasks(inputs) if t["open"]]); tot = sum(result.get("counts", {}).values())
            return (n == tot), f"re-read {n} open vs briefed {tot}"
        if skill_id == "audit_logging" and st == "RECORDED":
            import engine
            recs = engine.read_audit(3); ok = any(r.get("manual") for r in recs)
            return ok, "manual audit record present on re-read" if ok else "audit record ABSENT"
        if skill_id == "completion_verification":
            return ("verified" in result), "verification result carries explicit verified flag"
        return True, "no post-condition declared"
    except Exception as e:
        return False, f"verification error {type(e).__name__}: {e}"

def summarize(result):
    if not isinstance(result, dict): return str(result)[:200]
    keys = [k for k in ("status","count","p1_count","snapshot","op_id","verified","contradiction","risk","code","reason") if k in result]
    return {k: result[k] for k in keys}
