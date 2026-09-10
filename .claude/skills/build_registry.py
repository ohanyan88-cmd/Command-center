# -*- coding: utf-8 -*-
"""Canonical Skill Registry builder — SOURCE of truth for skill contracts. Emits registry.json.

REGISTRY QUALITY AUDIT (2026-09-10): 132 → see RETIRED below. Every retired id carries the survivor it merged
into and the reason. Rule applied: a skill survives only if it provides a capability no other skill provides
(distinct executor behaviour, distinct required input, or distinct routing target). Same executor + same input
+ same output = alias → merged. Tools are not skills → retired into tools_available/tool_intents.

Maturity here is a DECLARED TARGET only. certify.py computes the ACHIEVED level per skill from mapped evidence
and writes it back; engine.validate_registry() rejects any L3+ skill whose per-skill certification is missing,
failed, or stale (fingerprint mismatch after a contract/implementation change).
"""
import json, pathlib, datetime, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "runtime")); import python_runtime; python_runtime.ensure()        # deterministic project interpreter (<root>/.venv)
TODAY = datetime.date.today().isoformat()

AUTHORITY = ["READ", "ANALYZE", "RECOMMEND", "DRAFT", "CREATE_INTERNAL_TASK",
             "EXECUTE_REVERSIBLE", "EXECUTE_EXTERNAL", "EXECUTE_MATERIAL"]

TOOLS_AVAILABLE = {
    "python": True, "filesystem": True, "xlsx": True, "docx": True,
    "memory_files": True, "audit_log": True, "state_store": True,
    "crm": False, "bitrix24": False, "billing_db": False, "bi_dashboard": False,
    "calendar": False, "email": False, "scheduler": False, "database": False,
    "api": False, "whatsapp_live": False,
}
# Intent phrases that name a TOOL action (not a skill). The resolver attaches the tool requirement so the gate
# can fail closed with TOOL_UNAVAILABLE instead of routing to a fake "*_operations" skill.
TOOL_INTENTS = {
    # WRITE intents only (Mission 4 is READ-ONLY): reading mail/calendar is served by the integration layer (INT-OL-*), not by a tool skill
    "email":       ("send email", "send an email", "send the email", "email them", "email him", "email her", "reply to the email", "forward the email", "նամակ ուղարկ", "նամակը ուղարկ", "մեյլ ուղարկ", "ուղարկիր նամակ"),
    "calendar":    ("add to calendar", "create event", "create a meeting", "calendar event", "book a meeting", "schedule a meeting", "reschedule the meeting", "cancel the meeting", "օրացույցում ավելացրու", "հանդիպում նշանակ"),
    "bitrix24":    ("create task in bitrix", "bitrix task create", "in bitrix", "բիտրիքսում", "crm update", "update the crm", "update the deal", "update deal", "close the deal in", "delete the task", "delete task"),
    "billing_db":  ("change the tariff", "change tariff", "update the customer", "update customer", "suspend the subscriber", "սակագինը փոխ", "բաժանորդին անջատ"),
    "bi_dashboard":("power bi", "dashboard query", "open the dashboard"),
    "database":    ("query the db", "sql query", "run sql"),
    "api":         ("api call", "call the api", "webhook"),
    "scheduler":   ("set a timer", "schedule a job", "cron"),
    "whatsapp_live": ("send whatsapp", "send on whatsapp", "whatsapp-ով ուղարկ"),
}

XLSX = "Tasks.xlsx"
CORE_TOOLS = ("python", "filesystem", "xlsx", "audit_log")
STATE_TOOLS = ("python", "filesystem", "state_store", "audit_log")
XLSX_POLICY = {"max_age_hours": 24 * 14}      # tracker older than 14 days → STALE_SOURCE unless accept_stale acknowledged

def S(skill_id, name, domain, purpose, outcome, *, maturity="L0", triggers=(), anti=(), req_in=(), opt_in=(),
      pre=(), ctx=(), sources=(), deps=(), req_skills=(), tools_allowed=(), tools_req=(), steps=(), outputs=(),
      validation=(), approval=(), max_action="RECOMMEND", failures=(), fallback="Return structured BLOCKED state; never fabricate.",
      logging=(), metrics=(), tests=(), evals=(), executor=None, core=False, status="active", version="1.2.0",
      absorbed=(), source_policy=None):
    return {
        "skill_id": skill_id, "name": name, "version": version, "domain": domain,
        "purpose": purpose, "business_outcome": outcome, "description": purpose,
        "maturity_level": maturity, "declared_maturity": maturity, "status": status, "core": core,
        "triggers": list(dict.fromkeys(triggers)), "anti_triggers": list(anti),
        "required_inputs": list(req_in), "optional_inputs": list(opt_in),
        "preconditions": list(pre), "required_context": list(ctx),
        "authoritative_sources": list(sources), "source_policy": source_policy or ({} if not sources else dict(XLSX_POLICY)),
        "dependencies": list(deps), "required_skills": list(req_skills),
        "allowed_tools": list(tools_allowed), "required_tools": list(tools_req),
        "execution_steps": list(steps), "expected_outputs": list(outputs),
        "validation_rules": list(validation), "approval_requirements": list(approval),
        "authority_boundary": {"max_action": max_action, "material_requires_explicit_approval": True},
        "failure_conditions": list(failures), "fallback_behavior": fallback,
        "logging_requirements": list(logging) or ["execution_id", "inputs", "sources", "result_status", "duration_ms"],
        "success_metrics": list(metrics), "test_cases": list(tests), "eval_cases": list(evals),
        "executor": executor, "absorbed": list(absorbed),
        "evidence": {}, "certification": {}, "last_verified": None,
    }

skills = []
RETIRED = {}     # old_id → {merged_into, reason}
def retire(old, into, reason): RETIRED[old] = {"merged_into": into, "reason": reason, "retired_on": TODAY}

# ═══════════════════════ A. EXECUTIVE CONTROL ═══════════════════════
A = "A_EXECUTIVE_CONTROL"
skills += [
S("executive_prioritization","Executive Prioritization",A,
  "Rank open items P1–P4 by business impact, urgency, owner and deadline; surface the 3–5 that need the Head's attention.",
  "Head sees the few things that matter, not a flat list.", maturity="L3", core=True, executor="executive_prioritization",
  triggers=("prioritize","priorit","առաջնահերթ","what matters","top priorities","ինչ է կարևոր","what should i do","do first",
            "ինչից սկսեմ","need my attention","needs my attention","which problems","ուշադրության","three problems","top 3"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("task_management",),
  steps=("load open tasks","score: overdue>today>tomorrow>later; escalate ball-with-other","cap P1 at 5"),
  outputs=("ranked list with P-level and reason",), validation=("every open task assigned exactly one P-level","P1 count <= 5"),
  metrics=("P1 items resolved within deadline",), evals=("daily_brief","overdue_action","r_attention")),
S("task_management","Task Management",A,
  "Read, list and inspect tasks from the source of truth (xlsx); normalize fields. Also the read/write primitive for the tracker.",
  "Single accurate view of every task.", maturity="L4", core=True, executor="task_management",
  triggers=("list tasks","show tasks","task list","open tasks","task status","առաջադրանքների ցուցակ","ցուցակը","excel","xlsx","spreadsheet","աղյուսակ"),
  opt_in=("task_id","status_filter"), sources=(XLSX,), tools_req=CORE_TOOLS,
  steps=("open xlsx","parse rows 13+ (№,task,status,comment,due,owner)","normalize dates/status"),
  outputs=("task records",), validation=("every record has id,task,status","status in allowed set"),
  failures=("xlsx missing","sheet missing","schema drift"), absorbed=("spreadsheet_data_operations",)),
S("delegation_design","Delegation & Instruction Design",A,
  "Turn a vague instruction, meeting note or recommendation into an executable task: one named owner, deadline, expected output.",
  "One accountable owner per task; no 'sales team' ownership.", maturity="L2", executor="delegation_design",
  triggers=("delegate","assign","հանձնարար","who should do","bitrix task","թասկ","action plan","next steps","action items",
            "meeting actions","draft instruction","write an instruction","հանձնարարական գրիր","notes to tasks"),
  req_in=("instruction",), opt_in=("owner","deadline","expected_output","notes","recommendation"), max_action="DRAFT",
  steps=("extract task","require single named owner","require deadline","define expected output"),
  outputs=("task draft: task/owner/deadline/expected_output",),
  validation=("owner is a single named person, not a team","deadline present or flagged"),
  absorbed=("meeting_action_capture","action_plan","instruction_drafting")),
S("commitment_tracking","Commitment Tracking",A,
  "Record commitments ('I'll call Friday', 'if X then tell me') as tracked items with idempotency in the hardened store.",
  "Nothing promised is forgotten.", maturity="L4", core=True, executor="commitment_tracking",
  triggers=("remind me","i will","կզանգեմ","կտամ","խոստանում եմ","my commitment","remember to","հիշեցրու","don't let me forget"),
  req_in=("text",), opt_in=("due","owner","condition"), tools_req=STATE_TOOLS,
  steps=("normalize text","op_id = sha256(normalized text|owner|due)","store.record → RECORDED|DUPLICATE (DB decides)"),
  outputs=("commitment record with op_id and status RECORDED|DUPLICATE",),
  validation=("op_id deterministic","duplicate text → DUPLICATE not second record","record re-read from store after write"),
  failures=("state dir unwritable","store corrupt"), evals=("conversational_reminder","r_remind")),
S("waiting_for_tracking","Waiting-for & Accountability Tracking",A,
  "Register of what we are waiting for, from whom, since when, expected by when — including cross-department handoffs.",
  "Ball-with-others items never disappear.", maturity="L4", core=True, executor="waiting_for_tracking",
  triggers=("waiting for","waiting on","սպասում","who owes","ով է պարտք","ումից","waiting-for","handoff","between departments",
            "բաժինների միջև","cross-functional","accountab","պատասխանատվ","who committed","owes me"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("task_management",),
  steps=("filter open tasks whose owner is not Գև or contains →","group by counterpart","attach due"),
  outputs=("waiting-for list grouped by counterpart",), validation=("every item names a counterpart",),
  evals=("cross_department_blocker","r_who_owes"), absorbed=("cross_department_handoff_control","accountability_tracking")),
S("deadline_management","Deadline Management",A,
  "Bucket open tasks: overdue / today / tomorrow / upcoming / no deadline.", "No deadline is missed silently.",
  maturity="L4", core=True, executor="deadline_management",
  triggers=("deadline","ժամկետ","overdue","ժամկետանց","due today","due tomorrow","what's due","late","ուշաց"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("task_management",),
  steps=("load open tasks","compute days to due","bucket + sort"), outputs=("buckets with counts",),
  validation=("bucket set exact","no closed task in buckets"), evals=("overdue_action","daily_brief")),
S("reminder_intelligence","Reminder Intelligence",A,
  "Turn a due item into a contextual reminder plan: 7d prep / 3d readiness / 1d confirm / same-day / after-deadline check.",
  "Reminders arrive early and with context, never bare.", maturity="L3", core=True, executor="reminder_intelligence",
  triggers=("reminder plan","when should i be reminded","հիշեցման պլան"),
  req_in=("item","due"), opt_in=("prep_items",), tools_req=("python",),
  validation=("scheduler_available reported honestly (False in this runtime)","plan contains after-deadline check"),
  evals=("conversational_reminder","r_remind")),
S("follow_up_management","Follow-up Management",A,
  "Who needs to be chased for what, since when, and the exact next action; escalate repeated slippage.",
  "Open items are chased, not forgotten.", maturity="L3", core=True, executor="follow_up_management",
  triggers=("follow up on","follow-ups","follow up list","who to chase","հետևել","chase","still hasn't","hasn't sent","hasn't delivered","չի ուղարկել","չի տվել",
            "promised","խոստացել էր","manager follow up","people follow-up","overdue items"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("deadline_management","waiting_for_tracking"),
  outputs=("follow-up list: owner, since, next_action",), validation=("every follow-up has owner and next_action",),
  evals=("cross_department_blocker","r_broken_promise"), absorbed=("management_follow_up",)),
S("escalation_management","Escalation Management",A,
  "Structure an escalation: problem, impact, owner, deadline status, done so far, Head action — and draft the message.",
  "Escalations reach the Head in a decidable form.", maturity="L2", core=True, executor="escalation_management",
  triggers=("escalat","էսկալ","escalation message","draft escalation"), req_in=("item",),
  opt_in=("impact","owner","deadline_status","done_so_far","head_action"), max_action="DRAFT",
  validation=("all six escalation fields present",), absorbed=("escalation_drafting",)),
S("decision_support","Decision Support & Recommendation",A,
  "Prepare a decision for the Head: issue, context, options, recommendation, risk of delay, deadline — or frame an analysis into a recommendation with owner/deadline/Head action.",
  "Decisions, not data dumps.", maturity="L2", core=True, executor="decision_support",
  triggers=("should we","decide","որոշ","pros/cons","pros and cons","recommend","what should we do","առաջարկ","ինչ անենք","your decision","need a decision"),
  req_in=(), opt_in=("issue","analysis","options","context","recommendation","risk_of_delay","deadline"),
  validation=("recommendation never invented without facts: INSUFFICIENT DATA when options/facts absent",),
  evals=("head_decision","r_tariff"), absorbed=("recommendation",)),
S("decision_logging","Decision Logging",A,
  "Record a decision (what/why/who/effective date/follow-up) idempotently in the hardened store.",
  "Decisions are not reopened blindly.", maturity="L3", executor="decision_logging",
  triggers=("log the decision","record the decision","we decided","որոշեցինք","decision log","decided that"),
  req_in=("decision",), opt_in=("reason","owner","effective_date","follow_up"), tools_req=STATE_TOOLS),
S("approval_management","Approval Management",A,
  "Detect when an action level needs explicit Head approval and check the approval token.",
  "Approvals never skipped.", maturity="L4", core=True, executor="approval_management",
  triggers=("needs approval","requires sign-off","approval needed","հաստատում է պետք","approve this"),
  req_in=("action_level",), opt_in=("approval_token",), tools_req=("python",),
  validation=("EXECUTE_EXTERNAL/EXECUTE_MATERIAL without token → BLOCKED APPROVAL_REQUIRED",),
  absorbed=("approval_requirement_detection",)),
S("meeting_preparation","Meeting Preparation",A,
  "Prepare a meeting pack: purpose, participants, previous decisions, open actions, overdue, waiting-for, decisions required, talking points.",
  "Head walks in prepared.", maturity="L2", core=True, executor="meeting_preparation",
  triggers=("prepare me for","prepare for the meeting","meeting prep","meeting preparation","ժողովին պատրաստ","prepare the meeting",
            "performance review","review pack","ատեստ",
            "next meeting","prepare for tomorrow","ժողովից առաջ"),
  req_in=("meeting",), opt_in=("topic","purpose","participants"), sources=(XLSX,), tools_req=CORE_TOOLS,
  deps=("task_management","deadline_management","waiting_for_tracking"), evals=("meeting_prep","r_meeting"),
  absorbed=("performance_review_preparation",)),
S("daily_briefing","Daily Briefing",A,
  "GOOD MORNING BRIEF: top priorities, Head actions, decisions pending, deadlines today/overdue/tomorrow, waiting-for, data gaps.",
  "Day starts with control.", maturity="L4", core=True, executor="daily_briefing",
  triggers=("daily brief","morning brief","օրվա բրիֆ","good morning","առավոտյան պլան","today's priorities","այսօրվա պլան","what should i do today",
            "what meetings","meetings do i have","meetings today","my meetings","what's on my calendar","what is on my calendar","calendar today","my calendar","upcoming meetings","օրացույց","այսօրվա հանդիպումներ","հանդիպումներս","ինչ հանդիպում"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("executive_prioritization","deadline_management","waiting_for_tracking"),
  validation=("top_priorities/overdue/deadlines_today/waiting_for/counts present","counts equal open tasks"),
  evals=("daily_brief",), absorbed=("daily_priority_management",)),
S("end_of_day_control","End-of-Day Control",A,
  "EOD: completed / not completed / decisions pending / waiting / tomorrow.", "Day closes cleanly.",
  maturity="L2", executor="end_of_day_control", triggers=("end of day","eod","երեկոյան ամփոփ","wrap up","close the day","ամփոփում"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS, deps=("deadline_management",)),
S("weekly_executive_review","Weekly Executive Review",A,
  "Weekly S&O review skeleton from available data; sales/ops sections marked UNKNOWN without datasets.",
  "Weekly rhythm maintained.", maturity="L1", executor="weekly_review",
  triggers=("weekly review","weekly executive review","week in review","շաբաթվա ամփոփ","շաբաթական"),
  req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS),
]
retire("daily_priority_management","daily_briefing","alias: same executor (daily_briefing), same input, same output")
retire("meeting_action_capture","delegation_design","alias: same executor (delegation_design); notes→tasks is instruction→task")
retire("action_plan","delegation_design","workflow step / output format of delegation_design (same executor)")
retire("instruction_drafting","delegation_design","output format: an instruction with owner/deadline IS a delegation draft")
retire("escalation_drafting","escalation_management","output format of escalation_management")
retire("recommendation","decision_support","workflow step: a recommendation frame is decision preparation; merged executor")
retire("approval_requirement_detection","approval_management","alias: same executor (approval_management), same input")
retire("performance_review_preparation","meeting_preparation","L0 with no executor; a review pack is a meeting pack with topic")
retire("calendar_management","<tool:calendar>","a tool, not a skill: no capability without the calendar tool (tools_available.calendar=False)")
retire("spreadsheet_data_operations","task_management","alias: same executor (task_management); xlsx is the task source")

# ═══════════════════════ B. SALES MANAGEMENT ═══════════════════════
B = "B_SALES_MANAGEMENT"
def sales(sid, name, purpose, trig, core=False, mat="L0", deps=(), absorbed=(), evals=("sales_decline",)):
    return S(sid, name, B, purpose, "Sales deviations identified early.", maturity=mat, core=core, triggers=trig,
             req_in=("sales_data",), tools_req=("crm",) if mat == "L0" else ("python",), deps=deps, max_action="RECOMMEND",
             fallback="BLOCKED: no live sales data source; requires user-supplied dataset (sales_data).",
             executor="analysis_on_supplied_data" if mat == "L1" else None, evals=evals, absorbed=absorbed)
skills += [
 sales("sales_kpi_monitoring","Sales KPI Monitoring","Track leads/conversion/sales/revenue vs target from a supplied dataset.",
       ("sales kpi","վաճառքի ցուցանիշ","sales numbers","how are sales","sales performance","sales figures"), core=True, mat="L1", evals=("sales_decline","r_sales_down")),
 sales("target_vs_actual","Target vs Actual & Gap","Compare target, actual, gap; quantify shortfall.",
       ("target vs actual","gap to target","shortfall","plan vs actual","պլան-փաստ","թիրախ"), mat="L1", absorbed=("gap_analysis",), evals=("missed_target",)),
 sales("sales_forecasting","Sales Forecasting","Run-rate based forecast, projection and gap.",
       ("forecast","կանխատես","run rate","will we hit","projection","project forward"), core=True, mat="L1", deps=("target_vs_actual",), absorbed=("forecasting",), evals=("missed_target",)),
 sales("sales_funnel_analysis","Sales Funnel, Lead & Conversion Analysis","Stage conversion, drop-off, lead volume/quality/source.",
       ("funnel","ֆաննել","drop-off","stage conversion","conversion","փոխարկում","leads","լիդ","lead quality"), mat="L0", absorbed=("conversion_analysis","lead_analysis")),
 sales("pipeline_management","Pipeline Management","Stale/overdue/no-next-action opportunities.",("pipeline","փայփլայն","opportunities","stale deals"), mat="L0", evals=("pipeline_stagnation",)),
 sales("channel_performance_analysis","Channel Performance Analysis","Performance by channel (D2D, telesales, corporate).",("by channel","channel performance","ալիք","d2d","telesales","կորպորատիվ ալիք"), mat="L1"),
 sales("lost_opportunity_analysis","Lost Opportunity Analysis","Why deals are lost.",("lost deals","lost opportunit","կորցրած գործարք","why we lose"), mat="L0"),
 sales("upsell_analysis","Upsell / Cross-sell Analysis","Upsell and cross-sell potential and results.",("upsell","cross-sell","cross sell"), mat="L0", absorbed=("cross_sell_analysis",)),
 sales("customer_acquisition_analysis","Customer Acquisition Analysis","New connections, CAC, payback.",("acquisition","նոր միացում","new connections","cac"), mat="L1"),
 sales("churn_analysis","Churn & Retention Analysis","Churn rate, drivers, risk signals; retention flow effectiveness.",
       ("churn","չըռն","cancellations","հրաժարվ","retention","ռեթենշն","save list","պահել հաճախորդ"), core=True, mat="L1", absorbed=("retention_analysis",), evals=("churn_increase",)),
 sales("revenue_leakage_detection","Revenue Leakage Detection","Service delivered vs billed mismatch.",("leakage","revenue assurance","չգանձված","billing mismatch"), mat="L1"),
 sales("campaign_performance_analysis","Campaign Performance Analysis","Campaign ROI.",("campaign","քամփեյն","promo"), mat="L0"),
 sales("pricing_performance_analysis","Pricing Performance Analysis","Price/tariff performance from supplied data.",
       ("pricing performance","tariff performance","price performance","սակագնի արդյունավետ","price elasticity"), mat="L0"),
]
retire("gap_analysis","target_vs_actual","alias: same executor + input; the gap IS the target-vs-actual output")
retire("forecasting","sales_forecasting","overlap: generic forecasting duplicated sales_forecasting (same executor)")
retire("conversion_analysis","sales_funnel_analysis","overlap: conversion by stage is the funnel analysis")
retire("lead_analysis","sales_funnel_analysis","overlap: lead volume/quality is the top of the funnel")
retire("cross_sell_analysis","upsell_analysis","overlap: identical L0 contract; one capability")
retire("retention_analysis","churn_analysis","overlap: retention and churn are one analysis; same executor + input")
retire("salesperson_performance_analysis","performance_gap_diagnosis","overlap: per-person results diagnosis is the people-performance skill")

# ═══════════════════════ C. OPERATIONS MANAGEMENT ═══════════════════════
C = "C_OPERATIONS_MANAGEMENT"
def ops(sid, name, purpose, trig, core=False, mat="L0", absorbed=(), evals=("ops_backlog",)):
    return S(sid, name, C, purpose, "Operational problems detected early.", maturity=mat, core=core, triggers=trig,
             req_in=("ops_data",), tools_req=("bi_dashboard",) if mat == "L0" else ("python",),
             executor="analysis_on_supplied_data" if mat == "L1" else None,
             fallback="BLOCKED: no live operations data; requires user-supplied dataset (ops_data).", evals=evals, absorbed=absorbed)
skills += [
 ops("operations_kpi_monitoring","Operations KPI & SLA Monitoring","Backlog/SLA/aging/rework/delivery/fulfillment KPIs from a supplied dataset.",
     ("ops kpi","operations kpi","գործառնական ցուցանիշ","sla","service level","order fulfillment","order to activation","install times","delivery performance"),
     core=True, mat="L1", absorbed=("sla_monitoring","service_delivery_monitoring","order_fulfillment_monitoring"), evals=("ops_backlog","r_backlog")),
 ops("workload_analysis","Workload & Capacity Analysis","Incoming vs completed vs open; capacity vs demand; rebalancing.",
     ("workload","ծանրաբեռն","capacity","թողունակ","rebalance","balance workload","բաշխել"), mat="L1", absorbed=("capacity_analysis","workload_balancing")),
 ops("backlog_management","Backlog & Aging Management","Backlog size, aging distribution, trend.",
     ("backlog","կուտակ","queue","aging","how old is"), mat="L1", absorbed=("aging_analysis",), evals=("ops_backlog","r_backlog")),
 ops("bottleneck_detection","Bottleneck Detection","Where work accumulates and why.",("bottleneck","խցան","where is it stuck","where does it get stuck"), core=True, mat="L1", evals=("ops_backlog","r_backlog")),
 ops("failure_rework_analysis","Failure/Rework Analysis","Failed installs, rework rate.",("rework","failed install","կրկնակի այց"), mat="L0"),
 ops("operational_incident_management","Operational Incident Management","Track incidents to closure.",("incident","outage","ինցիդենտ","խափանում"), mat="L0"),
 ops("customer_complaint_pattern_analysis","Customer Complaint Pattern Analysis","Isolated vs systemic complaints.",("complaint","բողոք"), mat="L1", evals=("complaint_trend",)),
 ops("operational_risk_detection","Operational Risk Detection","Leading indicators of failure.",("ops risk","operational risk","գործառնական ռիսկ"), mat="L1"),
]
retire("sla_monitoring","operations_kpi_monitoring","overlap: SLA is one KPI family of ops monitoring (L0, no executor)")
retire("service_delivery_monitoring","operations_kpi_monitoring","overlap: delivery/activation is an ops KPI (L0, no executor)")
retire("order_fulfillment_monitoring","operations_kpi_monitoring","overlap: order→install→activation is an ops KPI (L0, no executor)")
retire("capacity_analysis","workload_analysis","overlap: capacity vs demand is workload analysis")
retire("aging_analysis","backlog_management","overlap: aging is a dimension of the backlog (same executor + input)")
retire("cross_department_handoff_control","waiting_for_tracking","alias: same executor (waiting_for_tracking), same data")

# ═══════════════════════ D. PEOPLE / PERFORMANCE ═══════════════════════
D = "D_PEOPLE_PERFORMANCE"
skills += [
 S("performance_gap_diagnosis","Employee Performance & Gap Diagnosis",D,
   "Diagnose an employee/salesperson performance gap: classify cause PERSON/PROCESS/SYSTEM/POLICY/CAPACITY/TRAINING/MANAGEMENT/INCENTIVE/DATA; never blame first.",
   "Root cause separated from blame.", maturity="L1", core=True, executor="performance_gap_diagnosis",
   triggers=("employee performance","աշխատակցի կատարում","underperform","performance gap","ինչու չի աշխատում","productivity","արտադրող",
             "training need","needs training","overloaded","too much work","salesperson performance","by employee","who is selling"),
   req_in=("performance_data",), opt_in=("description",), tools_req=("python",), max_action="RECOMMEND",
   approval=("Any compensation/termination action requires explicit Head approval",),
   fallback="BLOCKED: requires performance data; never attribute cause without diagnosis.",
   evals=("employee_underperformance",), absorbed=("employee_performance_analysis","productivity_analysis","training_need_detection","capacity_vs_performance_diagnosis","salesperson_performance_analysis")),
]
retire("employee_performance_analysis","performance_gap_diagnosis","alias: same executor + input (performance_gap_diagnosis)")
retire("productivity_analysis","performance_gap_diagnosis","overlap: output-per-person is an input metric of the performance diagnosis (L0)")
retire("training_need_detection","performance_gap_diagnosis","overlap: TRAINING is a cause class of the diagnosis (L0)")
retire("capacity_vs_performance_diagnosis","performance_gap_diagnosis","overlap: CAPACITY is a cause class of the diagnosis (L0)")
retire("accountability_tracking","waiting_for_tracking","alias: same executor (waiting_for_tracking)")
retire("management_follow_up","follow_up_management","overlap: manager-level follow-up is follow-up management (L0)")
retire("workload_balancing","workload_analysis","overlap: rebalancing is the action side of workload analysis (L0)")

# ═══════════════════════ E. PROCESS & AUTOMATION ═══════════════════════
E = "E_PROCESS_AUTOMATION"
skills += [
 S("root_cause_analysis","Root Cause Analysis (5 Whys)",E,"SYMPTOM → why-chain → ROOT CAUSE → CORRECTIVE ACTION; never solution-first.",
   "Problems fixed at the root.", maturity="L1", core=True, executor="root_cause_analysis",
   triggers=("why did","why are","why is","root cause","ինչու","պատճառ","what caused","5 whys","five whys"),
   req_in=("description",), opt_in=("whys","symptom","corrective_action"), tools_req=("python",), absorbed=("five_whys",),
   evals=("sales_decline","ops_backlog","employee_underperformance")),
 S("process_mapping","Process Mapping & Analysis",E,"Map a process (trigger/steps/owners/decisions/exceptions/KPI/systems) and analyse it for waits, handoffs, waste, duplicate work.",
   "Process visible before it is changed.", maturity="L1", executor="structured_analysis",
   triggers=("map the process","process map","how does it work","workflow analysis","waste","ավելորդ քայլ","inefficien","duplicate work","done twice","handoff analysis","փոխանցում"),
   req_in=("description",), tools_req=("python",), absorbed=("workflow_analysis","waste_detection","duplicate_work_detection","handoff_analysis")),
 S("process_improvement","Process & Control Design",E,"Recommend simplify → standardize → control before automate; design workflows, controls and exception handling.",
   "Processes improved in the right order.", maturity="L1", executor="structured_analysis",
   triggers=("improve process","բարելավ","optimize the process","design workflow","design the flow","control design","add a control","exception handling","edge cases","բացառություն"),
   req_in=("description",), tools_req=("python",), absorbed=("workflow_design","control_design","exception_handling_design")),
 S("automation_opportunity_detection","Automation Assessment",E,"Detect repetitive manual work, assess readiness (stable/logical enough), outline the automation.",
   "Only stable processes get automated.", maturity="L1", core=True, executor="structured_analysis",
   triggers=("automate","ավտոմատ","automation","what can be automated","ready to automate"),
   req_in=("description",), tools_req=("python",), absorbed=("automation_readiness_assessment","automation_design")),
]
retire("five_whys","root_cause_analysis","alias: same executor (root_cause_analysis)")
for old in ("workflow_analysis","waste_detection","duplicate_work_detection","handoff_analysis"):
    retire(old,"process_mapping","artificially split micro-skill: identical executor/template (structured_analysis), no unique capability")
for old in ("workflow_design","control_design","exception_handling_design"):
    retire(old,"process_improvement","artificially split micro-skill: identical executor/template (structured_analysis), no unique capability")
for old in ("automation_readiness_assessment","automation_design"):
    retire(old,"automation_opportunity_detection","workflow step of one automation assessment; identical executor/template")
retire("sop_interpretation","structured_data_extraction","alias: same executor (document_extraction)")

# ═══════════════════════ F. DATA & BI ═══════════════════════
F = "F_DATA_BI"
skills += [
 S("data_analysis","Supplied-Data Analysis",F,"Descriptive statistics and trend/variance on a SUPPLIED dataset (never live); labels output DERIVED.",
   "Numbers explained, not invented.", maturity="L1", executor="analysis_on_supplied_data",
   triggers=("analyze data","analyse data","վերլուծիր տվյալ","trend","միտում","variance","շեղում","deviation","anomaly","spike","unusual",
             "interpret kpi","kpi change","kpi changed","kpi dropped","what does the kpi mean","segment","breakdown by","by region","impact","ազդեցություն","what does it cost",
             "what if","scenario","սցենար","dashboard export"),
   req_in=("dataset",), tools_req=("python",), validation=("never invent numbers","label CONFIRMED/DERIVED/UNVERIFIED/UNKNOWN"),
   fallback="BLOCKED: dataset required; label missing data UNKNOWN.", evals=("missing_kpi_data","sales_decline"),
   absorbed=("trend_analysis","variance_analysis","kpi_interpretation","anomaly_detection","segmentation","business_impact_assessment","scenario_analysis","dashboard_interpretation")),
 S("source_reconciliation","Source Reconciliation & Contradiction Detection",F,"Reconcile two sources; surface A-says-X/B-says-Y, which is newer/authoritative, impact; never silently choose.",
   "No silent choice between conflicting sources.", maturity="L2", core=True, executor="source_reconciliation",
   triggers=("reconcile","reconciliation","համադր","two sources","contradict","doesn't match","don't match","conflict","հակաս","disagree","mismatch"),
   req_in=("sources",), opt_in=("impact",), tools_req=("python",), evals=("conflicting_reports",), absorbed=("contradiction_detection",)),
 S("executive_reporting","Executive Reporting",F,"EXECUTIVE SNAPSHOT over real task data: RED/YELLOW/GREEN + deviations/risks/decisions/owners; sales/ops marked UNKNOWN.",
   "Status is reportable upward in one screen.", maturity="L2", core=True, executor="executive_reporting",
   triggers=("executive report","status report","ռեփորթ","executive summary","snapshot","status update for"),
   req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS),
]
for old, why in (("trend_analysis","direction/rate of change"),("variance_analysis","actual vs expected"),("kpi_interpretation","KPI change"),
                 ("anomaly_detection","outliers — not implemented"),("segmentation","segments — not implemented"),
                 ("business_impact_assessment","impact — not implemented"),("scenario_analysis","what-if — not implemented"),("dashboard_interpretation","L0, no executor")):
    retire(old,"data_analysis",f"identical executor (analysis_on_supplied_data): separate id misrepresented a capability ({why})")
retire("data_quality_checking","source_verification","alias: same executor (source_verification)")

# ═══════════════════════ G. COMMUNICATION ═══════════════════════
G = "G_COMMUNICATION"
skills += [
 S("information_classification","Information Triage & Classification",G,"Classify incoming items (email/chat/notes) ACTION/DECISION/DELEGATE/MONITOR/FYI/IGNORE; protect the Head's attention.",
   "Only meaningful items reach the Head.", maturity="L2", executor="information_classification",
   triggers=("classify","դասակարգ","triage","what kind of item","incoming messages","inbox","emails","նամակներ","filter the noise"),
   req_in=(), opt_in=("content","items"), tools_req=("python",), max_action="ANALYZE",
   absorbed=("email_triage","message_triage","executive_attention_management")),
 S("executive_summarization","Executive Summarization",G,"What happened / why it matters / recommendation / Head action; meeting notes → decisions, tasks, owners, deadlines.",
   "Head reads one screen, not ten.", maturity="L1", executor="drafting",
   triggers=("summarize","summarise","ամփոփիր","tl;dr","short version","meeting summary","ժողովի ամփոփ"),
   req_in=("content",), opt_in=("kind",), tools_req=("python",), max_action="DRAFT", absorbed=("meeting_summary",),
   evals=("meeting_prep",)),
 S("management_communication","Outgoing Communication (Գև's voice)",G,"Draft outgoing messages (management, Finance, the company principal, follow-ups) in «Գև» voice, internal wording stripped; sending needs Head OK.",
   "Nothing leaves in the wrong voice or without OK.", maturity="L2", core=True, executor="outgoing_communication",
   triggers=("write to","գրիր","message to","send finance","send them","send him","send her","a follow-up to","follow-up message","outgoing","draft a message","reply to","email to","send email","նամակ գրիր"),
   req_in=("content",), opt_in=("kind","recipient"), tools_req=("python",), max_action="DRAFT",
   validation=("outgoing text uses «Գև», never «Ես»/internal wording","requires_head_ok_before_send is True"),
   evals=("r_send_finance",), absorbed=("follow_up_drafting",)),
 S("communication_quality_checking","Communication Quality Checking",G,"Check clarity/assignment/deadline/tone; flag internal wording.",
   "Messages are clear and assignable.", maturity="L2", executor="communication_quality_check",
   triggers=("check the message","proofread","ստուգիր տեքստը","quality check the text"), req_in=("content",), tools_req=("python",), max_action="ANALYZE"),
]
retire("email_triage","information_classification","alias: same executor (information_classification); channel is not a capability")
retire("message_triage","information_classification","alias: same executor (information_classification); channel is not a capability")
retire("executive_attention_management","information_classification","alias: same executor (information_classification)")
retire("meeting_summary","executive_summarization","output format of summarization (kind=meeting)")
retire("follow_up_drafting","management_communication","output format of outgoing communication (kind=follow_up)")

# ═══════════════════════ H. MEMORY & CONTEXT ═══════════════════════
H = "H_MEMORY_CONTEXT"
skills += [
 S("commitment_memory","Commitment Memory",H,"Retrieve open commitments from the hardened store.","Promises are remembered.",maturity="L3",executor="commitment_memory",
   triggers=("what did i promise","խոստացել եմ","my commitments","open commitments"), tools_req=("python","filesystem","state_store")),
 S("decision_memory","Decision Memory",H,"Retrieve logged decisions.","Decisions not reopened blindly.",maturity="L3",executor="decision_memory",
   triggers=("what did we decide","որոշել էինք","past decisions","decision history"), tools_req=("python","filesystem","state_store")),
 S("information_retrieval","Context & Information Retrieval",H,"Find facts, history, project context, dependencies and links across workspace + memory files.","Answers and context are findable.",
   maturity="L2",executor="memory_retrieval",
   triggers=("find","where is","գտիր","որտեղ է","search","history of","what happened before","նախկինում","earlier we","background on","context on","related to","depends on","կախված","blocked by"),
   opt_in=("query",), tools_req=("filesystem","memory_files"),
   absorbed=("project_context_retrieval","historical_context_retrieval","context_linking","dependency_memory")),
 S("open_loop_memory","Open-loop Memory",H,"All open loops: tasks + waiting + commitments + decisions pending.","Nothing left open silently.",maturity="L3",core=True,executor="open_loops",
   triggers=("open loops","what's open","anything pending","what's outstanding","բաց հարցեր","unanswered","check my email","check email","my email","in my mail","e-mails","նամակներում","փոստում"), req_in=("tasks",), sources=(XLSX,), tools_req=CORE_TOOLS,
   deps=("deadline_management","waiting_for_tracking","commitment_memory")),
 S("business_model_query","Business Model Query",H,"Answer who-owns / which-process / which-KPI / which-playbook / who-approves / role questions from the canonical Business Operating Model (.claude/business) with source ids; conflicts and unknowns are surfaced (OWNER_UNKNOWN, KPI_DEFINITION_MISSING, PROCESS_UNDEFINED, TARGET_UNKNOWN, APPROVAL_RULE_UNKNOWN, SOURCE_CONFLICT), never invented.",
   "Deputy answers business questions from sources, not from memory.",maturity="L3",core=True,executor="business_query",
   triggers=("who owns","who is responsible","who is accountable","ով է պատասխանատու","ում վրա է","who handles","which process","what process","որ գործընթաց","which kpi","what kpi","որ ցուցանիշ","which metric","playbook","what do we do if","what should we do if","who should approve","who approves","ով պիտի հաստատի","who reports to","business model","org chart","this process"),
   opt_in=("query","kind"), tools_req=("python","filesystem"),
   validation=("unknown owner → OWNER_UNKNOWN","conflicting current sources → SOURCE_CONFLICT (never a silent pick)","every answer carries source ids"),
   evals=("b_who_owns_churn","b_failed_install_process","b_conversion_kpi","b_backlog_playbook","b_who_approves","b_decided_process")),
]
for old in ("project_context_retrieval","historical_context_retrieval","context_linking","dependency_memory"):
    retire(old,"information_retrieval","alias: same executor (memory_retrieval) over the same files")
retire("source_of_truth_selection","source_verification","alias: same executor (source_verification)")
retire("contradiction_detection","source_reconciliation","alias: same executor (source_reconciliation), same input")

# ═══════════════════════ I. GOVERNANCE ═══════════════════════
I = "I_GOVERNANCE"
skills += [
 S("authority_checking","Authority Checking",I,"Check a requested action level against a skill's max_action and the approval policy.","No unauthorized action.",maturity="L4",core=True,executor="authority_checking",
   triggers=("can i","am i allowed","authority","լիազոր","permission to"), req_in=("action_level",), opt_in=("approval_token","skill_id"), tools_req=("python",),
   validation=("EXECUTE_MATERIAL requires token","level not in ladder → BLOCKED"), evals=("head_decision","r_tariff")),
 S("risk_classification","Risk & Policy Classification",I,"Classify an action LOW/MEDIUM/HIGH/CRITICAL by materiality (pricing/comp/hiring/contract/public/irreversible) and reversibility.","Risk and policy visible before action.",
   maturity="L2",executor="risk_classification",
   triggers=("how risky","risk level","policy","քաղաքականություն","is this allowed","tariff price","change the price","change pricing","սակագինը փոխ","raise the price","lower the price"),
   req_in=("action",), tools_req=("python",), absorbed=("policy_checking",), evals=("r_tariff",)),
 S("data_sensitivity_awareness","Data Sensitivity Awareness",I,"Flag credentials/personal data; redact from logs.","No secrets leaked.",maturity="L2",executor="sensitivity_check",
   triggers=("sensitive","password","գաղտնաբառ","personal data","credential"), req_in=("text",), tools_req=("python",)),
 S("completion_verification","Completion & Action Verification",I,"Distinguish ATTEMPTED/EXECUTED/VERIFIED by re-reading source state (file exists, task status, store record).","Done means verified, not narrated.",
   maturity="L4",core=True,executor="completion_verification",
   triggers=("is it done","ավարտված է","verify","did it work","ստուգիր որ","confirm it happened","արվե՞լ է"), req_in=("evidence_spec",), tools_req=("python","filesystem"),
   evals=("completed_no_evidence",), absorbed=("action_verification",)),
 S("audit_logging","Audit Logging",I,"Append a structured audit record to the hardened store for a skill run or manual event.","Every run is traceable.",maturity="L4",core=True,executor="audit_logging",
   triggers=("audit","log this","լոգ"), req_in=("record",), tools_req=("python","filesystem","audit_log")),
 S("source_verification","Source Verification & Data Quality",I,"Verify a source exists, is readable, schema matches, freshness; pick the authoritative source.","Only real, fresh sources used.",
   maturity="L4",core=True,executor="source_verification",
   triggers=("is the source valid","check the file","source check","ֆայլը ճիշտ է","data quality","տվյալների որակ","is the data right","stale","which file is right","source of truth"),
   opt_in=("path",), tools_req=("python","filesystem"), absorbed=("data_quality_checking","source_of_truth_selection")),
 S("confidence_handling","Confidence Handling",I,"Label outputs CONFIRMED/DERIVED/UNVERIFIED/UNKNOWN.","Uncertainty is explicit.",maturity="L2",executor="confidence_labeling",
   triggers=("how sure","confidence","վստահ"), req_in=("claims",), tools_req=("python",), evals=("conflicting_reports",)),
]
retire("policy_checking","risk_classification","overlap: same MATERIAL regex; risk_classification is the superset (adds reversibility)")
retire("action_verification","completion_verification","alias: same executor + input (completion_verification)")

# ═══════════════════════ J. TOOL / INTEGRATION ═══════════════════════
J = "J_TOOL_INTEGRATION"
skills += [
 S("structured_data_extraction","Document & Structured Data Extraction",J,"Read docx/xlsx/text files (SOPs, roadmaps) and extract structure/paragraphs/tables.",
   "Documents become usable facts.", maturity="L2", executor="document_extraction",
   triggers=("extract","հանիր","parse the file","docx","read the document","փաստաթուղթը կարդա","sop","procedure document","ընթացակարգը կարդա"),
   req_in=("path",), tools_req=("python","docx"), max_action="ANALYZE", absorbed=("document_operations","sop_interpretation")),
]
retire("document_operations","structured_data_extraction","alias: same executor (document_extraction)")
for old, key in (("calendar_operations","calendar"),("email_operations","email"),("crm_operations","bitrix24"),("bi_dashboard_operations","bi_dashboard"),
                 ("task_management_operations","bitrix24"),("database_data_retrieval","database"),("api_integration_operations","api")):
    retire(old,f"<tool:{key}>",f"a tool, not a skill: no executor, no capability; tool '{key}' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE")

# ═══════════════════════ CHAINS (minimum complete graphs; dependencies are added automatically) ═══════════════════════
CHAINS = {
  "investigate_sales_decline": ["sales_kpi_monitoring","data_analysis","root_cause_analysis","decision_support"],
  "sales_target_missed":       ["target_vs_actual","sales_forecasting","root_cause_analysis","decision_support"],
  "ops_backlog_growing":       ["operations_kpi_monitoring","backlog_management","bottleneck_detection","root_cause_analysis","decision_support"],
  "employee_underperformance": ["performance_gap_diagnosis","root_cause_analysis","decision_support"],
  "churn_increase":            ["churn_analysis","data_analysis","root_cause_analysis","decision_support"],
  "pipeline_stagnation":       ["pipeline_management","decision_support"],
  "complaint_trend":           ["customer_complaint_pattern_analysis","root_cause_analysis","decision_support"],
  "prepare_sales_review":      ["meeting_preparation","executive_summarization"],
  "conversational_reminder":   ["commitment_tracking","reminder_intelligence"],
  "daily_brief":               ["daily_briefing"],
  "cross_department_blocker":  ["waiting_for_tracking","follow_up_management","escalation_management"],
  "broken_promise":            ["follow_up_management"],
  "weekly_sno_review":         ["weekly_executive_review","executive_summarization"],
  "decision_about_process":    ["business_model_query","decision_memory"],
  "head_decision":             ["decision_support","risk_classification","authority_checking","approval_management"],
  "conflicting_reports":       ["source_reconciliation","confidence_handling"],
  "completed_no_evidence":     ["completion_verification"],
  "outgoing_message":          ["management_communication"],
}
CHAIN_TRIGGERS = {
  "investigate_sales_decline": ("why did sales drop","sales dropped","sales decline","վաճառք իջել","վաճառքն իջել","sales fell","why are sales down","sales are down","sales down"),
  "sales_target_missed": ("missed target","missed the target","missed the sales target","պլանը չկատար","target missed","below target","behind target"),
  "ops_backlog_growing": ("backlog growing","backlog is growing","backlog doubled","backlog has doubled","backlog doubles","կուտակ աճ","queue growing","backlog up"),
  "employee_underperformance": ("underperform","չի աշխատում լավ","performance problem","not performing"),
  "churn_increase": ("churn increase","churn is up","չըռն աճ","more cancellations","churn up"),
  "pipeline_stagnation": ("pipeline stagn","deals not moving","deals are not moving","pipeline stuck","pipeline is stuck","stale pipeline","գործարքները չեն շարժվում"),
  "complaint_trend": ("complaint trend","complaints increasing","complaints are increasing","increasing complaints","more complaints","complaints are up","բողոքներ շատացել","բողոքները շատ"),
  "prepare_sales_review": ("prepare sales review","sales review","prepare me for","prepare tomorrow","վաճառքի ժողով","prepare the meeting","sales meeting","ժողովին պատրաստ"),
  "conversational_reminder": ("remind me","հիշեցրու"),
  "daily_brief": ("daily brief","morning brief","օրվա բրիֆ","good morning","առավոտյան պլան"),
  "cross_department_blocker": ("blocked by another department","cross-department","other department","բաժինը չի տալիս","stuck waiting on"),
  "broken_promise": ("still hasn't","hasn't sent","hasn't delivered","չի ուղարկել","դեռ չի տվել","missed his deadline","missed her deadline","missed the deadline","missed their deadline","ժամկետը բաց թողեց"),
  "weekly_sno_review": ("weekly sales & operations review","weekly s&o review","sales & operations review","weekly sales and operations review","շաբաթական վաճառքի և գործառնական"),
  "decision_about_process": ("decide about this process","decided about this process","decide about the process","what did we decide about this process","որոշել էինք գործընթաց"),
  "head_decision": ("need your decision","requires your approval","should we approve","decide on","should we change","should we raise","should we lower","փոխե՞նք"),
  "conflicting_reports": ("conflicting reports","reports disagree","numbers don't match","երկու տարբեր թիվ"),
  "completed_no_evidence": ("he says it's done","says it is done","ասում է արել է","claims completed","says it's done"),
  "outgoing_message": ("send finance","send them a follow-up","send him a follow-up","send her a follow-up","write to the principal","ղեկավարին գրիր","message to management","a follow-up to"),
}

registry = {
  "schema_version": "2.0.0", "generated": TODAY,
  "authority_ladder": AUTHORITY, "maturity_levels": ["L0","L1","L2","L3","L4"],
  "tools_available": TOOLS_AVAILABLE, "tool_intents": TOOL_INTENTS,
  "material_actions": ["pricing_change","compensation_change","hiring","termination","contract","financial_commitment",
                       "customer_concession","public_statement","policy_change","irreversible_operational_change"],
  "chains": CHAINS, "chain_triggers": CHAIN_TRIGGERS,
  "skills": skills, "retired": RETIRED,
  "audit": {"before": 132, "after": len(skills), "retired": len(RETIRED)},
}

def write_audit_md(path):
    from collections import Counter
    by_survivor = {}
    for old, r in RETIRED.items(): by_survivor.setdefault(r["merged_into"], []).append((old, r["reason"]))
    lines = [f"# Registry Quality Audit — {TODAY}", "",
             f"**Before:** 132 skills · **After:** {len(skills)} skills · **Retired/merged:** {len(RETIRED)}", "",
             "Rule: a skill survives only if it provides a capability no other skill provides (distinct executor behaviour, distinct required input, or distinct routing target). "
             "Same executor + same input + same output = alias → merged. Tools are not skills → `tools_available` / `tool_intents`.", "",
             "## Merges and retirements", ""]
    for surv in sorted(by_survivor):
        lines.append(f"### → `{surv}`")
        for old, why in by_survivor[surv]: lines.append(f"- `{old}` — {why}")
        lines.append("")
    lines += ["## Surviving skills and their unique capability", ""]
    for s in skills:
        lines.append(f"- `{s['skill_id']}` ({s['domain']}, target {s['declared_maturity']}, executor `{s['executor']}`): {s['purpose']}")
    c = Counter(s["domain"] for s in skills)
    lines += ["", "## Per-domain counts (after)", ""] + [f"- {d}: {n}" for d, n in sorted(c.items())]
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    ids = [s["skill_id"] for s in skills]
    assert len(ids) == len(set(ids)), "duplicate skill ids"
    assert not (set(ids) & set(RETIRED)), "retired id still active"
    for s in skills:
        for a in s["absorbed"]: assert a in RETIRED and RETIRED[a]["merged_into"] == s["skill_id"], f"absorbed mismatch {a}"
    out = HERE / "registry.json"
    out.write_text(json.dumps(registry, ensure_ascii=False, indent=1), encoding="utf-8")
    write_audit_md(HERE.parent / "docs" / "Registry-audit-2026-09-10.md")      # documentation lives in .claude/docs (workspace contract)
    from collections import Counter
    c = Counter(s["maturity_level"] for s in skills)
    print(f"registry.json  ·  {len(skills)} skills (from 132; retired {len(RETIRED)})  ·  declared: " + "  ".join(f"{k}={c[k]}" for k in sorted(c)))
