# -*- coding: utf-8 -*-
"""ՀԱՐԴ ԲՐԻՖԻՆԳ — SessionStart hook, routed THROUGH the certified Skill Engine on a governed gate ticket:
daily_briefing + commitment_memory run via engine.run_skill → audited, verified. Also reports enforcement health
(escaped tickets, stale certifications, store integrity). Falls back to a direct xlsx read only if the engine is
unavailable — and says so."""
import os, sys, io, datetime, pathlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills"))
TODAY = datetime.date.today()
HY = ["երկուշաբթի","երեքշաբթի","չորեքշաբթի","հինգշաբթի","ուրբաթ","շաբաթ","կիրակի"]

def line(): print("─" * 56)
def d(x): return x[5:] if isinstance(x, str) and len(x) >= 10 else (x or "—")

print(); line()
print(f"  ⛔ ՊԱՐՏԱԴԻՐ ՍԵՍԻԱՅԻ ՍԿԻԶԲ — {TODAY.isoformat()}, {HY[TODAY.weekday()]}")
print("  Դու Գև-ի գործադիր օգնականն ես։ Գործիր ըստ CLAUDE.md-ի։ Skill gate՝ մեխանիկական (hooks)։")
line()

inbox = ROOT / "00_ԳՑԻՐ_ԱՅՍՏԵՂ"
items = [f for f in os.listdir(inbox) if f != "_ԿԱՐԴԱ.md"] if inbox.is_dir() else []
if items:
    print(f"\n  📥 00_ԳՑԻՐ_ԱՅՍՏԵՂ — {len(items)} ԱՆԴԱՍԱՎՈՐ ԲԱՆ, դասավորի ԱՌԱՋԻՆԸ՝")
    for f in items: print(f"       • {f}")
else: print("\n  📥 Մուտքի պանակը դատարկ է ✓")

try:
    raw = io.open(ROOT / "04_WhatsApp" / "ՄՈՒՏՔ.md", encoding="utf-8").read()
    seg = raw.split("## Չմշակված", 1); body = seg[1].split("---", 1)[0] if len(seg) > 1 else ""
    if "\n".join(l for l in body.splitlines() if l.strip() and not l.strip().startswith("<!--")).strip():
        print("\n  ✉  ՄՈՒՏՔ.md-ում կա չմշակված տեքստ — դարձրու առաջադրանք")
except Exception: pass

engine_used = False
try:
    import engine
    reg = engine.load_registry()
    session = os.environ.get("CLAUDE_SESSION_ID", "")
    t = engine.open_ticket(reg, "session-start brief: daily_briefing + commitment_memory", session_id=session, source="SessionStart")
    r = engine.run_skill(reg, "daily_briefing", {}, intent="session-start brief", selection_reason="SessionStart hook", ticket_id=t["ticket_id"])
    if r["status"] == "BLOCKED" and any(b.get("code") == "STALE_SOURCE" for b in r.get("blocked", [])):
        print(f"\n  ⚠ ԱՂԲՅՈՒՐԸ ՀՆԱՑԱԾ Է — {r['blocked'][0]['reason']}\n     Բրիֆը տրվում է հնացած տվյալով (ընդունված, աուդիտված)։ Թարմացրու Առաջադրանքներ.xlsx-ը։")
        r = engine.run_skill(reg, "daily_briefing", {"accept_stale": True}, intent="session-start brief (stale acknowledged)", selection_reason="SessionStart hook", ticket_id=t["ticket_id"])
    if r["status"] == "EXECUTED":
        b = r["result"]; engine_used = True
        def show(title, rows, mark):
            if not rows: return
            print(f"\n  {mark} {title} — {len(rows)}")
            for x in rows: print(f"       {x['id']}. [{d(x.get('due'))}] {x['task'][:52]}  ·  {x.get('owner','')}")
        show("ԺԱՄԿԵՏԱՆՑ", b["overdue"], "🔴"); show("ԱՅՍՕՐ", b["deadlines_today"], "🟠"); show("ՎԱՂԸ", b["tomorrow"], "🟡")
        if b["waiting_for"]:
            print(f"\n  ⏳ ՍՊԱՍՈՒՄ ԵՄ ՈՒՐԻՇԻՑ — {len(b['waiting_for'])}")
            for w in b["waiting_for"]: print(f"       {w['id']}. {w['from']}  ·  {w['task'][:44]}  [{d(w.get('due'))}]")
        if b["decisions_pending"]:
            print(f"\n  ⚖  ՈՐՈՇՈՒՄ Է ՍՊԱՍՎՈՒՄ — {len(b['decisions_pending'])}")
            for x in b["decisions_pending"]: print(f"       {x['id']}. {x['task'][:52]}  ·  {x['owner']}")
        if b["no_deadline"]: print(f"\n  ⚠  Ժամկետ չունեցող բաց կետ՝ {len(b['no_deadline'])} — ժամկետ դիր")
        if not (b["overdue"] or b["deadlines_today"]): print("\n  ✓ Ժամկետանց կամ այսօրվա բաց կետ չկա")
        c = engine.run_skill(reg, "commitment_memory", {}, intent="session-start brief", selection_reason="SessionStart hook", ticket_id=t["ticket_id"])
        cm = c.get("result", {}).get("commitments", []) if c["status"] == "EXECUTED" else []
        due_soon = [x for x in cm if x.get("due") and x["due"] <= (TODAY + datetime.timedelta(days=3)).isoformat()]
        if due_soon:
            print(f"\n  📌 ԽՈՍՏՈՒՄՆԵՐ, ԺԱՄԿԵՏԸ ≤3 ՕՐ — {len(due_soon)}")
            for x in due_soon: print(f"       [{d(x['due'])}] {x['text'][:60]}")
        ver = r.get("verification", {}); dbs = reg["_index"]["daily_briefing"]
        print(f"\n  ⚙  skill engine: daily_briefing v{dbs['version']} ({dbs['maturity_level']}) · exec {r['execution_id']} · verified {'✓' if ver.get('ok') else '✗'} · ticket {t['ticket_id']}")
    else:
        print(f"\n  ⚠ daily_briefing skill {r['status']}: {r.get('blocked') or r.get('error')}")
    # enforcement health
    st = engine._store(); chk = st.check()
    cutoff = (datetime.datetime.now() - datetime.timedelta(hours=12)).isoformat(timespec="seconds")
    stale_open = [x for x in st.list("tickets", where="status='OPEN'") if x["ticket_id"] != t["ticket_id"] and x.get("created", "") < cutoff]
    for x in stale_open: engine.close_ticket(x["ticket_id"], "ABANDONED", "left open by a previous session")
    esc = [x for x in st.list("tickets") if (x.get("closure") or {}).get("verdict") == "ESCAPE"]
    probs = engine.validate_registry(reg)
    flags = []
    if not chk["ok"]: flags.append(f"store integrity ✗ {chk['problems'][:1]}")
    if esc: flags.append(f"ENFORCEMENT ESCAPES ընդհանուր՝ {len(esc)} (վերջինը՝ {esc[-1]['ticket_id']}) — ստուգիր skill.py audit")
    if probs: flags.append(f"certification problems՝ {len(probs)} — վազեցրու skill.py release")
    if stale_open: flags.append(f"{len(stale_open)} բաց ticket փակվեց որպես ABANDONED")
    print("  🛡  enforcement: hooks UserPromptSubmit/PreToolUse/PostToolUse/Stop · store " + ("ok" if chk["ok"] else "CORRUPT") + (" · " + " · ".join(flags) if flags else " · escapes 0 · certs fresh"))
    engine.close_ticket(t["ticket_id"], "GOVERNED_EXECUTED" if engine_used else "GOVERNED_BLOCKED_REPORTED", "session-start brief")
except Exception as e:
    print(f"\n  ⚠ skill engine unavailable ({type(e).__name__}: {e}) — fallback read, UNGOVERNED")

if not engine_used:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(ROOT / "Առաջադրանքներ.xlsx", data_only=True); ws = wb["ԱՌԱՋԱԴՐԱՆՔՆԵՐ"]
        over, today = [], []
        for r in range(13, ws.max_row + 1):
            n, task, st, due = ws.cell(row=r,column=2).value, ws.cell(row=r,column=3).value, ws.cell(row=r,column=6).value, ws.cell(row=r,column=11).value
            if not isinstance(n, int) or st == "Արված" or not hasattr(due, "date"): continue
            dd = due.date() if isinstance(due, datetime.datetime) else due
            (over if dd < TODAY else today if dd == TODAY else []).append(f"{n}. {task}")
        if over: print("\n  🔴 ԺԱՄԿԵՏԱՆՑ:", *[f"\n       {x}" for x in over])
        if today: print("\n  🟠 ԱՅՍՕՐ:", *[f"\n       {x}" for x in today])
    except Exception as e: print(f"\n  (Առաջադրանքներ.xlsx չկարդացվեց՝ {type(e).__name__})")

line(); print("  Հաղորդիր վերևը Գև-ին ՆԱԽՔԱՆ մնացած գործը սկսելը։"); line(); print()
