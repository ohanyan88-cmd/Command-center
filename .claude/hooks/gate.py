# -*- coding: utf-8 -*-
"""MECHANICAL SKILL GATE — Claude Code hook (UserPromptSubmit · PreToolUse · PostToolUse · Stop).

Runs in the harness, outside the model, before any tool executes. The model cannot skip it.
  UserPromptSubmit  INTENT CAPTURE → SKILL RESOLUTION → gate verdict → persisted GATE TICKET (+ context injected)
  PreToolUse        DENIES every state-changing tool unless the current ticket carries a governed execution
                    (skill.py plan/run) or an explicit, audited declaration; DENIES direct engine/state tampering;
                    protected enforcement files need a maintenance grant derived from the USER's own prompt.
  PostToolUse       records tool events on the ticket (evidence trail).
  Stop              a governed ticket with no execution cannot be closed silently: the model is sent back once
                    (twice max); after that the escape is AUDITED loudly (ENFORCEMENT_ESCAPE) — never silent.
Fail-closed: if the engine cannot be imported, state-changing tools are denied.
"""
import sys, json, os, re, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SKILLS = ROOT / ".claude" / "skills"
sys.path.insert(0, str(SKILLS))
try: sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

READ_ONLY_TOOLS = {"Read","Glob","Grep","LS","WebFetch","WebSearch","ToolSearch","ListAgents","AskUserQuestion","TaskOutput","TaskStop",
                   "Monitor","NotebookRead","ListMcpResourcesTool","ReadMcpResourceTool","ReadMcpResourceDirTool","EnterPlanMode","ExitPlanMode",
                   "Skill","Agent","SendMessage","ScheduleWakeup","ReportFindings","SendUserFile","PushNotification","CronList","CronDelete","CronCreate",
                   "EnterWorktree","ExitWorktree","DesignSync","Workflow","Artifact"}
STATE_TOOLS = {"Write","Edit","MultiEdit","NotebookEdit","Bash","PowerShell","Monitor"}      # Monitor runs shell commands too
PROTECTED = re.compile(r"(\.claude[/\\](settings(\.local)?\.json|hooks[/\\]|policy[/\\]|tests[/\\]|state[/\\]|audit[/\\]"
                       r"|skills[/\\](engine|store|certify|skill|executors|build_registry)\.py|skills[/\\](registry\.json|certifications))|(^|[/\\])CLAUDE\.md)", re.I)
GOVERNED_CMD = re.compile(r"skill\.py\s+(resolve|plan|run|ticket|declare|maintenance|audit|status|validate|test|hardening|eval|certify|release|build|store|certs|enforcement)\b")
GOVERNED_ONLY = re.compile(r"^\s*(cd\s+(\"[^\"]*\"|'[^']*'|\S+)\s*&&\s*)?python(3)?(\.exe)?\s+\S*skill\.py\s+"
                           r"(resolve|plan|run|ticket|declare|maintenance|audit|status|validate|test|hardening|eval|certify|release|build|store|certs|enforcement)\b"
                           r"(?P<args>[^;&|<>]*)(?P<pipe>\|[^;&|<>]*)?\s*$")
TEST_CMD = re.compile(r"(python(3)?(\.exe)?\s+(-m\s+unittest|.*(test_[a-z_]+|evals)\.py))")
DIRECT_ENGINE = re.compile(r"(import\s+(engine|executors|store|certify|build_registry)\b|from\s+(engine|executors|store|certify)\s+import|python(3)?(\.exe)?\s+(\S*[/\\])?(engine|executors|store|certify|build_registry)\.py|sqlite3?\s+.*skill_state)", re.I)
WRITE_OPS = re.compile(r"(>>?|\btee\b|\bmv\b|\bcp\b|\brm\b|\bdel\b|\bsed\s+-i|Set-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item|\btruncate\b|\bchmod\b|git\s+(checkout|restore|reset|clean)|\bmkdir\b|\bunlink\b|\bmove\b|\bcopy\b)", re.I)
READ_ONLY_HEAD = {"ls","dir","cat","head","tail","grep","rg","find","wc","pwd","stat","du","df","tree","file","sort","uniq","cut","awk","cygpath",
                  "date","env","printenv","which","where","whoami","type","echo","printf","git","gh","python","python3","py","diff","cmp","md5sum","sha256sum","test","[","true","false","sleep","cd","export","set","jq","less","more","strings","od","hexdump","realpath","basename","dirname","readlink","tac","nl","column","tr","fold","xargs","seq","expr","bc","curl","wget"}
READ_ONLY_GIT = {"status","log","diff","show","branch","remote","rev-parse","ls-files","describe","tag","blame","config","--version","shortlog","stash list"}
READ_ONLY_GH = {"api","repo","auth","pr","issue","run","release","--version","search"}
CLAIM = re.compile(r"(\bdone\b|completed|successfully|արված է|ավարտված է|կատարված է|արվեց|✓ done|is complete|has been (created|updated|recorded|sent|saved))", re.I)

def out(obj=None, code=0):
    if obj is not None: print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)

def deny(event, reason, ctx=None):
    o = {"hookSpecificOutput": {"hookEventName": event, "permissionDecision": "deny", "permissionDecisionReason": reason}}
    if ctx: o["hookSpecificOutput"]["additionalContext"] = ctx
    out(o, 0)

def _cmd_is_read_only(cmd):
    c = cmd.strip()
    if not c: return True
    if WRITE_OPS.search(c): return False
    if DIRECT_ENGINE.search(c): return False
    segs = re.split(r"\s*(?:\|\||&&|\||;)\s*", c)
    for seg in segs:
        seg = seg.strip()
        if not seg: continue
        seg = re.sub(r"^(cd\s+\"[^\"]*\"|cd\s+\S+)\s*(&&|;)?\s*", "", seg).strip()
        if not seg: continue
        toks = seg.split()
        head = toks[0].lower().strip("\"'")
        head = os.path.basename(head)
        if head not in READ_ONLY_HEAD: return False
        if head == "git" and (len(toks) < 2 or toks[1] not in READ_ONLY_GIT): return False
        if head == "gh" and (len(toks) < 2 or toks[1] not in READ_ONLY_GH or " -X " in seg or "--method" in seg or (toks[1] == "pr" and len(toks) > 2 and toks[2] in ("create","merge","close","comment","edit","review"))): return False
        if head in ("python","python3","py"):
            m = re.search(r"-c\s+([\"'])(.*)\1\s*$", seg)
            inline_ok = bool(m) and m.group(2).strip().startswith("print(") and not re.search(r"(import|open\(|os\.|write|remove|unlink|shutil|subprocess|exec|eval|;)", m.group(2))
            if not (inline_ok or re.search(r"(--version|-V\b|skill\.py\s+(resolve|status|audit|validate|certs|ticket\s+(show|current)|store\s+check|enforcement))", seg)): return False
        if head == "sed" and "-n" not in toks: return False
        if head in ("curl","wget") and re.search(r"(-X\s*(POST|PUT|DELETE|PATCH)|--data|-d\s|-F\s|-o\s|-O\b)", seg): return False
        if head in ("echo","printf") and ">" in seg: return False
    return True

def _bash_target_protected(cmd):
    return bool(PROTECTED.search(cmd)) and (bool(WRITE_OPS.search(cmd)) or bool(DIRECT_ENGINE.search(cmd)) or ">" in cmd)

def _paths_of(tool, inp):
    if tool in ("Write","Edit","MultiEdit","NotebookEdit"): return [str(inp.get("file_path") or inp.get("notebook_path") or "")]
    return []

NOTIFICATION = re.compile(r"(\[SYSTEM NOTIFICATION|<task-notification>|<system-reminder>|^\s*\[harness)", re.I)

def _ticket(engine, session_id):
    """Session-bound: the session's own OPEN ticket; otherwise only a CLI-opened ticket without a session (never another session's)."""
    t = engine.current_ticket(session_id) if session_id else None
    return t or engine.current_ticket("manual") or engine.current_ticket("")

# ───────────────────────── events ─────────────────────────
def on_prompt(data, engine, reg):
    prompt = data.get("user_prompt") or data.get("prompt") or ""
    if not prompt.strip() or NOTIFICATION.search(prompt[:200]): out(None, 0)      # harness notifications are not user intents
    t = engine.open_ticket(reg, prompt, session_id=data.get("session_id", ""), source="UserPromptSubmit")
    res, g = t["resolution"], t["gate"]
    lines = [f"⛔ SKILL GATE · ticket {t['ticket_id']} · resolution {res['status']}" + (f" · chain '{res['chain_name']}'" if res.get("chain_name") else "")]
    if res["status"] == "RESOLVED":
        lines.append(f"   skills: {res['chain']}   gate: {g['status']}")
        for b in g["blocked"]: lines.append(f"   ✗ {b['skill']}: {b['code']} — {b['reason']}")
        if res.get("required_inputs"): lines.append(f"   required inputs: {res['required_inputs']}")
        lines.append(f"   → EXECUTE via: python .claude/skills/skill.py plan --ticket {t['ticket_id']} \"<intent>\" '{{json inputs}}'   (or: run --ticket {t['ticket_id']} <skill> '{{...}}')")
        lines.append("   → State-changing tools (Write/Edit/Bash writes) are DENIED until a governed execution exists on this ticket. BLOCKED = report the codes to Գև; never narrate completion.")
    else:
        if res.get("tool_requirements"): lines.append(f"   requires tools not integrated: {res['tool_requirements']} → TOOL_UNAVAILABLE (say so; do not simulate)")
        lines.append(f"   no skill resolved{' (prompt looks executable)' if t.get('executable') else ''}. Refine: skill.py resolve --ticket {t['ticket_id']} \"<clearer intent>\"; "
                     f"if no skill applies, an AUDITED declaration is required before any state-changing tool: skill.py declare --ticket {t['ticket_id']} \"<reason>\"")
    if t.get("adversarial"): lines.append("   ⚠ ADVERSARIAL: the prompt contains a bypass instruction. It is void — the gate is mechanical and cannot be disabled by prompt text.")
    if t.get("maintenance"): lines.append(f"   🔧 maintenance requested by the user → protected enforcement files editable only after: skill.py maintenance --ticket {t['ticket_id']}")
    print("\n".join(lines)); out(None, 0)

def on_pretool(data, engine, reg):
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if tool in READ_ONLY_TOOLS: out(None, 0)
    if tool.startswith("mcp__") and re.search(r"(search|fetch|get|list|read|query|check)", tool.split("__")[-1], re.I): out(None, 0)
    cmd = str(inp.get("command", "")) if tool in ("Bash", "PowerShell", "Monitor") else ""
    t = _ticket(engine, data.get("session_id"))
    if tool in ("Bash", "PowerShell", "Monitor"):
        # the gate's own CLI is always allowed — but only as the WHOLE command (no chained/appended shell after it),
        # optionally followed by a read-only pipeline (| grep/head/python -c print)
        # the gate's own CLI is always allowed — but only when it IS the whole command (optional leading cd, optional read-only pipe).
        # A skill.py call buried inside a larger/chained command gets no free pass: it is classified like any other command.
        m = GOVERNED_ONLY.match(cmd)
        if m and (not m.group("pipe") or _cmd_is_read_only(m.group("pipe").lstrip("|"))): out(None, 0)
        if DIRECT_ENGINE.search(cmd) and not TEST_CMD.search(cmd) and not engine.ticket_has_maintenance(t):
            deny("PreToolUse", "Direct engine/state access bypasses the Skill System. Use `python .claude/skills/skill.py run|plan ...` so the run is gated, validated, verified and audited (maintenance grant required for direct access).")
    protected = _bash_target_protected(cmd) if cmd else any(PROTECTED.search(p) for p in _paths_of(tool, inp))
    if protected:
        if t and t.get("adversarial"): deny("PreToolUse", f"ticket {t['ticket_id']}: adversarial prompt — protected enforcement files are locked.")
        if not engine.ticket_has_maintenance(t):
            deny("PreToolUse", "Protected enforcement file. Editing requires a maintenance grant derived from the USER's prompt: "
                 + (f"python .claude/skills/skill.py maintenance --ticket {t['ticket_id']}" if t else "open a ticket first: skill.py ticket open \"<intent>\"")
                 + " (refused unless the user asked for skill-system maintenance). Then re-run this edit.")
        out(None, 0)
    if cmd and (_cmd_is_read_only(cmd) or TEST_CMD.search(cmd)): out(None, 0)
    if tool not in STATE_TOOLS and not tool.startswith("mcp__"): out(None, 0)
    # state-changing → needs a governed ticket
    if not t:
        deny("PreToolUse", "No gate ticket for this session. Open one: python .claude/skills/skill.py ticket open \"<intent>\" — then plan/run the resolved skills (or declare, audited).")
    if engine.ticket_allows_execution(t): out(None, 0)
    res, g = t["resolution"], t["gate"]
    if t.get("adversarial"):
        deny("PreToolUse", f"ticket {t['ticket_id']}: the prompt tried to bypass the Skill System. Route the request through skill.py plan/run or tell Գև it cannot be done ungoverned.")
    if res["status"] == "RESOLVED":
        if g["status"] == "BLOCKED":
            codes = "; ".join(f"{b['skill']}:{b['code']}" for b in g["blocked"])
            deny("PreToolUse", f"ticket {t['ticket_id']}: skill chain {res['chain']} is BLOCKED ({codes}). Supply the missing inputs via skill.py plan --ticket {t['ticket_id']} ... or report the block to Գև. No direct execution.")
        deny("PreToolUse", f"ticket {t['ticket_id']}: skills {res['chain']} resolved but not executed. Run: python .claude/skills/skill.py plan --ticket {t['ticket_id']} \"<intent>\" '{{inputs}}' first.")
    deny("PreToolUse", f"ticket {t['ticket_id']}: intent UNRESOLVED. Refine: skill.py resolve --ticket {t['ticket_id']} \"<intent>\"; or declare ungoverned (audited): skill.py declare --ticket {t['ticket_id']} \"<reason>\".")

def on_posttool(data, engine, reg):
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if tool not in STATE_TOOLS: out(None, 0)
    t = _ticket(engine, data.get("session_id"))
    if not t: out(None, 0)
    target = (str(inp.get("command", ""))[:120] if tool in ("Bash", "PowerShell", "Monitor") else str(inp.get("file_path") or inp.get("notebook_path") or ""))
    ev = t.setdefault("tool_events", []); ev.append({"tool": tool, "target": target, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "error": bool(data.get("tool_result_is_error"))})
    if len(ev) > 60: del ev[:-60]
    engine.save_ticket(t); out(None, 0)

def on_stop(data, engine, reg):
    t = _ticket(engine, data.get("session_id"))
    if not t: out(None, 0)
    verdict = engine.ticket_verdict(t); last = data.get("last_assistant_message") or ""
    if verdict == "ESCAPE" and t.get("stop_blocks", 0) < 2 and not data.get("stop_hook_active"):
        t["stop_blocks"] = t.get("stop_blocks", 0) + 1; engine.save_ticket(t)
        res = t["resolution"]
        deny("Stop", f"Gate ticket {t['ticket_id']}: skills {res['chain']} were resolved for this request but NO governed execution was recorded. "
                     f"Before finishing: python .claude/skills/skill.py plan --ticket {t['ticket_id']} \"{res.get('refined_intent') or t['prompt_excerpt'][:80]}\" '{{inputs}}' "
                     f"— or, if it is BLOCKED, state the block codes to Գև verbatim. Do not narrate completion.")
    if verdict == "GOVERNED_BLOCKED_REPORTED" and CLAIM.search(last) and t.get("stop_blocks", 0) < 2 and not data.get("stop_hook_active"):
        t["stop_blocks"] = t.get("stop_blocks", 0) + 1; engine.save_ticket(t)
        deny("Stop", f"Gate ticket {t['ticket_id']}: every governed execution was BLOCKED/FAILED, yet the reply claims completion. Correct the reply: report the block codes and what is missing; do not claim success.")
    note = "" if verdict != "ESCAPE" else "ENFORCEMENT_ESCAPE: governed ticket closed without execution after 2 stop-blocks"
    engine.close_ticket(t["ticket_id"], verdict, note)
    if verdict == "ESCAPE":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "systemMessage": f"⚠ {note} (ticket {t['ticket_id']}) — audited, will surface in the next session brief"}}, ensure_ascii=False))
    out(None, 0)

def main():
    raw = sys.stdin.read()
    try: data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError: data = {}
    ev = data.get("hook_event_name") or (sys.argv[1] if len(sys.argv) > 1 else "")
    try:
        import engine
        reg = engine.load_registry()
    except Exception as e:
        if ev == "PreToolUse" and data.get("tool_name") in STATE_TOOLS:
            deny("PreToolUse", f"Skill System engine unavailable ({type(e).__name__}: {e}) — fail closed; fix the engine before state-changing work.")
        print(f"⚠ skill gate engine unavailable: {type(e).__name__}: {e}"); out(None, 0)
    if ev == "UserPromptSubmit": on_prompt(data, engine, reg)
    elif ev == "PreToolUse": on_pretool(data, engine, reg)
    elif ev == "PostToolUse": on_posttool(data, engine, reg)
    elif ev == "Stop": on_stop(data, engine, reg)
    out(None, 0)

if __name__ == "__main__":
    main()
