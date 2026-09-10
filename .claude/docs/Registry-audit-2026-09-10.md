# Registry Quality Audit — 2026-09-10

**Before:** 132 skills · **After:** 62 skills · **Retired/merged:** 71

Rule: a skill survives only if it provides a capability no other skill provides (distinct executor behaviour, distinct required input, or distinct routing target). Same executor + same input + same output = alias → merged. Tools are not skills → `tools_available` / `tool_intents`.

## Merges and retirements

### → `<tool:api>`
- `api_integration_operations` — a tool, not a skill: no executor, no capability; tool 'api' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `<tool:bi_dashboard>`
- `bi_dashboard_operations` — a tool, not a skill: no executor, no capability; tool 'bi_dashboard' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `<tool:bitrix24>`
- `crm_operations` — a tool, not a skill: no executor, no capability; tool 'bitrix24' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE
- `task_management_operations` — a tool, not a skill: no executor, no capability; tool 'bitrix24' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `<tool:calendar>`
- `calendar_management` — a tool, not a skill: no capability without the calendar tool (tools_available.calendar=False)
- `calendar_operations` — a tool, not a skill: no executor, no capability; tool 'calendar' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `<tool:database>`
- `database_data_retrieval` — a tool, not a skill: no executor, no capability; tool 'database' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `<tool:email>`
- `email_operations` — a tool, not a skill: no executor, no capability; tool 'email' is not integrated (tools_available) — routed via tool_intents → TOOL_UNAVAILABLE

### → `approval_management`
- `approval_requirement_detection` — alias: same executor (approval_management), same input

### → `automation_opportunity_detection`
- `automation_readiness_assessment` — workflow step of one automation assessment; identical executor/template
- `automation_design` — workflow step of one automation assessment; identical executor/template

### → `backlog_management`
- `aging_analysis` — overlap: aging is a dimension of the backlog (same executor + input)

### → `churn_analysis`
- `retention_analysis` — overlap: retention and churn are one analysis; same executor + input

### → `completion_verification`
- `action_verification` — alias: same executor + input (completion_verification)

### → `daily_briefing`
- `daily_priority_management` — alias: same executor (daily_briefing), same input, same output

### → `data_analysis`
- `trend_analysis` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (direction/rate of change)
- `variance_analysis` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (actual vs expected)
- `kpi_interpretation` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (KPI change)
- `anomaly_detection` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (outliers — not implemented)
- `segmentation` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (segments — not implemented)
- `business_impact_assessment` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (impact — not implemented)
- `scenario_analysis` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (what-if — not implemented)
- `dashboard_interpretation` — identical executor (analysis_on_supplied_data): separate id misrepresented a capability (L0, no executor)

### → `decision_support`
- `recommendation` — workflow step: a recommendation frame is decision preparation; merged executor

### → `delegation_design`
- `meeting_action_capture` — alias: same executor (delegation_design); notes→tasks is instruction→task
- `action_plan` — workflow step / output format of delegation_design (same executor)
- `instruction_drafting` — output format: an instruction with owner/deadline IS a delegation draft

### → `escalation_management`
- `escalation_drafting` — output format of escalation_management

### → `executive_summarization`
- `meeting_summary` — output format of summarization (kind=meeting)

### → `follow_up_management`
- `management_follow_up` — overlap: manager-level follow-up is follow-up management (L0)

### → `information_classification`
- `email_triage` — alias: same executor (information_classification); channel is not a capability
- `message_triage` — alias: same executor (information_classification); channel is not a capability
- `executive_attention_management` — alias: same executor (information_classification)

### → `information_retrieval`
- `project_context_retrieval` — alias: same executor (memory_retrieval) over the same files
- `historical_context_retrieval` — alias: same executor (memory_retrieval) over the same files
- `context_linking` — alias: same executor (memory_retrieval) over the same files
- `dependency_memory` — alias: same executor (memory_retrieval) over the same files

### → `management_communication`
- `follow_up_drafting` — output format of outgoing communication (kind=follow_up)

### → `meeting_preparation`
- `performance_review_preparation` — L0 with no executor; a review pack is a meeting pack with topic

### → `operations_kpi_monitoring`
- `sla_monitoring` — overlap: SLA is one KPI family of ops monitoring (L0, no executor)
- `service_delivery_monitoring` — overlap: delivery/activation is an ops KPI (L0, no executor)
- `order_fulfillment_monitoring` — overlap: order→install→activation is an ops KPI (L0, no executor)

### → `performance_gap_diagnosis`
- `salesperson_performance_analysis` — overlap: per-person results diagnosis is the people-performance skill
- `employee_performance_analysis` — alias: same executor + input (performance_gap_diagnosis)
- `productivity_analysis` — overlap: output-per-person is an input metric of the performance diagnosis (L0)
- `training_need_detection` — overlap: TRAINING is a cause class of the diagnosis (L0)
- `capacity_vs_performance_diagnosis` — overlap: CAPACITY is a cause class of the diagnosis (L0)

### → `process_improvement`
- `workflow_design` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability
- `control_design` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability
- `exception_handling_design` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability

### → `process_mapping`
- `workflow_analysis` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability
- `waste_detection` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability
- `duplicate_work_detection` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability
- `handoff_analysis` — artificially split micro-skill: identical executor/template (structured_analysis), no unique capability

### → `risk_classification`
- `policy_checking` — overlap: same MATERIAL regex; risk_classification is the superset (adds reversibility)

### → `root_cause_analysis`
- `five_whys` — alias: same executor (root_cause_analysis)

### → `sales_forecasting`
- `forecasting` — overlap: generic forecasting duplicated sales_forecasting (same executor)

### → `sales_funnel_analysis`
- `conversion_analysis` — overlap: conversion by stage is the funnel analysis
- `lead_analysis` — overlap: lead volume/quality is the top of the funnel

### → `source_reconciliation`
- `contradiction_detection` — alias: same executor (source_reconciliation), same input

### → `source_verification`
- `data_quality_checking` — alias: same executor (source_verification)
- `source_of_truth_selection` — alias: same executor (source_verification)

### → `structured_data_extraction`
- `sop_interpretation` — alias: same executor (document_extraction)
- `document_operations` — alias: same executor (document_extraction)

### → `target_vs_actual`
- `gap_analysis` — alias: same executor + input; the gap IS the target-vs-actual output

### → `task_management`
- `spreadsheet_data_operations` — alias: same executor (task_management); xlsx is the task source

### → `upsell_analysis`
- `cross_sell_analysis` — overlap: identical L0 contract; one capability

### → `waiting_for_tracking`
- `cross_department_handoff_control` — alias: same executor (waiting_for_tracking), same data
- `accountability_tracking` — alias: same executor (waiting_for_tracking)

### → `workload_analysis`
- `capacity_analysis` — overlap: capacity vs demand is workload analysis
- `workload_balancing` — overlap: rebalancing is the action side of workload analysis (L0)

## Surviving skills and their unique capability

- `executive_prioritization` (A_EXECUTIVE_CONTROL, target L3, executor `executive_prioritization`): Rank open items P1–P4 by business impact, urgency, owner and deadline; surface the 3–5 that need the Head's attention.
- `task_management` (A_EXECUTIVE_CONTROL, target L4, executor `task_management`): Read, list and inspect tasks from the source of truth (xlsx); normalize fields. Also the read/write primitive for the tracker.
- `delegation_design` (A_EXECUTIVE_CONTROL, target L2, executor `delegation_design`): Turn a vague instruction, meeting note or recommendation into an executable task: one named owner, deadline, expected output.
- `commitment_tracking` (A_EXECUTIVE_CONTROL, target L4, executor `commitment_tracking`): Record commitments ('I'll call Friday', 'if X then tell me') as tracked items with idempotency in the hardened store.
- `waiting_for_tracking` (A_EXECUTIVE_CONTROL, target L4, executor `waiting_for_tracking`): Register of what we are waiting for, from whom, since when, expected by when — including cross-department handoffs.
- `deadline_management` (A_EXECUTIVE_CONTROL, target L4, executor `deadline_management`): Bucket open tasks: overdue / today / tomorrow / upcoming / no deadline.
- `reminder_intelligence` (A_EXECUTIVE_CONTROL, target L3, executor `reminder_intelligence`): Turn a due item into a contextual reminder plan: 7d prep / 3d readiness / 1d confirm / same-day / after-deadline check.
- `follow_up_management` (A_EXECUTIVE_CONTROL, target L3, executor `follow_up_management`): Who needs to be chased for what, since when, and the exact next action; escalate repeated slippage.
- `escalation_management` (A_EXECUTIVE_CONTROL, target L2, executor `escalation_management`): Structure an escalation: problem, impact, owner, deadline status, done so far, Head action — and draft the message.
- `decision_support` (A_EXECUTIVE_CONTROL, target L2, executor `decision_support`): Prepare a decision for the Head: issue, context, options, recommendation, risk of delay, deadline — or frame an analysis into a recommendation with owner/deadline/Head action.
- `decision_logging` (A_EXECUTIVE_CONTROL, target L3, executor `decision_logging`): Record a decision (what/why/who/effective date/follow-up) idempotently in the hardened store.
- `approval_management` (A_EXECUTIVE_CONTROL, target L4, executor `approval_management`): Detect when an action level needs explicit Head approval and check the approval token.
- `meeting_preparation` (A_EXECUTIVE_CONTROL, target L2, executor `meeting_preparation`): Prepare a meeting pack: purpose, participants, previous decisions, open actions, overdue, waiting-for, decisions required, talking points.
- `daily_briefing` (A_EXECUTIVE_CONTROL, target L4, executor `daily_briefing`): GOOD MORNING BRIEF: top priorities, Head actions, decisions pending, deadlines today/overdue/tomorrow, waiting-for, data gaps.
- `end_of_day_control` (A_EXECUTIVE_CONTROL, target L2, executor `end_of_day_control`): EOD: completed / not completed / decisions pending / waiting / tomorrow.
- `weekly_executive_review` (A_EXECUTIVE_CONTROL, target L1, executor `weekly_review`): Weekly S&O review skeleton from available data; sales/ops sections marked UNKNOWN without datasets.
- `sales_kpi_monitoring` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Track leads/conversion/sales/revenue vs target from a supplied dataset.
- `target_vs_actual` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Compare target, actual, gap; quantify shortfall.
- `sales_forecasting` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Run-rate based forecast, projection and gap.
- `sales_funnel_analysis` (B_SALES_MANAGEMENT, target L0, executor `None`): Stage conversion, drop-off, lead volume/quality/source.
- `pipeline_management` (B_SALES_MANAGEMENT, target L0, executor `None`): Stale/overdue/no-next-action opportunities.
- `channel_performance_analysis` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Performance by channel (D2D, telesales, corporate).
- `lost_opportunity_analysis` (B_SALES_MANAGEMENT, target L0, executor `None`): Why deals are lost.
- `upsell_analysis` (B_SALES_MANAGEMENT, target L0, executor `None`): Upsell and cross-sell potential and results.
- `customer_acquisition_analysis` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): New connections, CAC, payback.
- `churn_analysis` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Churn rate, drivers, risk signals; retention flow effectiveness.
- `revenue_leakage_detection` (B_SALES_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Service delivered vs billed mismatch.
- `campaign_performance_analysis` (B_SALES_MANAGEMENT, target L0, executor `None`): Campaign ROI.
- `pricing_performance_analysis` (B_SALES_MANAGEMENT, target L0, executor `None`): Price/tariff performance from supplied data.
- `operations_kpi_monitoring` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Backlog/SLA/aging/rework/delivery/fulfillment KPIs from a supplied dataset.
- `workload_analysis` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Incoming vs completed vs open; capacity vs demand; rebalancing.
- `backlog_management` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Backlog size, aging distribution, trend.
- `bottleneck_detection` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Where work accumulates and why.
- `failure_rework_analysis` (C_OPERATIONS_MANAGEMENT, target L0, executor `None`): Failed installs, rework rate.
- `operational_incident_management` (C_OPERATIONS_MANAGEMENT, target L0, executor `None`): Track incidents to closure.
- `customer_complaint_pattern_analysis` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Isolated vs systemic complaints.
- `operational_risk_detection` (C_OPERATIONS_MANAGEMENT, target L1, executor `analysis_on_supplied_data`): Leading indicators of failure.
- `performance_gap_diagnosis` (D_PEOPLE_PERFORMANCE, target L1, executor `performance_gap_diagnosis`): Diagnose an employee/salesperson performance gap: classify cause PERSON/PROCESS/SYSTEM/POLICY/CAPACITY/TRAINING/MANAGEMENT/INCENTIVE/DATA; never blame first.
- `root_cause_analysis` (E_PROCESS_AUTOMATION, target L1, executor `root_cause_analysis`): SYMPTOM → why-chain → ROOT CAUSE → CORRECTIVE ACTION; never solution-first.
- `process_mapping` (E_PROCESS_AUTOMATION, target L1, executor `structured_analysis`): Map a process (trigger/steps/owners/decisions/exceptions/KPI/systems) and analyse it for waits, handoffs, waste, duplicate work.
- `process_improvement` (E_PROCESS_AUTOMATION, target L1, executor `structured_analysis`): Recommend simplify → standardize → control before automate; design workflows, controls and exception handling.
- `automation_opportunity_detection` (E_PROCESS_AUTOMATION, target L1, executor `structured_analysis`): Detect repetitive manual work, assess readiness (stable/logical enough), outline the automation.
- `data_analysis` (F_DATA_BI, target L1, executor `analysis_on_supplied_data`): Descriptive statistics and trend/variance on a SUPPLIED dataset (never live); labels output DERIVED.
- `source_reconciliation` (F_DATA_BI, target L2, executor `source_reconciliation`): Reconcile two sources; surface A-says-X/B-says-Y, which is newer/authoritative, impact; never silently choose.
- `executive_reporting` (F_DATA_BI, target L2, executor `executive_reporting`): EXECUTIVE SNAPSHOT over real task data: RED/YELLOW/GREEN + deviations/risks/decisions/owners; sales/ops marked UNKNOWN.
- `information_classification` (G_COMMUNICATION, target L2, executor `information_classification`): Classify incoming items (email/chat/notes) ACTION/DECISION/DELEGATE/MONITOR/FYI/IGNORE; protect the Head's attention.
- `executive_summarization` (G_COMMUNICATION, target L1, executor `drafting`): What happened / why it matters / recommendation / Head action; meeting notes → decisions, tasks, owners, deadlines.
- `management_communication` (G_COMMUNICATION, target L2, executor `outgoing_communication`): Draft outgoing messages (management, Finance, the company principal, follow-ups) in «Գև» voice, internal wording stripped; sending needs Head OK.
- `communication_quality_checking` (G_COMMUNICATION, target L2, executor `communication_quality_check`): Check clarity/assignment/deadline/tone; flag internal wording.
- `commitment_memory` (H_MEMORY_CONTEXT, target L3, executor `commitment_memory`): Retrieve open commitments from the hardened store.
- `decision_memory` (H_MEMORY_CONTEXT, target L3, executor `decision_memory`): Retrieve logged decisions.
- `information_retrieval` (H_MEMORY_CONTEXT, target L2, executor `memory_retrieval`): Find facts, history, project context, dependencies and links across workspace + memory files.
- `open_loop_memory` (H_MEMORY_CONTEXT, target L3, executor `open_loops`): All open loops: tasks + waiting + commitments + decisions pending.
- `business_model_query` (H_MEMORY_CONTEXT, target L3, executor `business_query`): Answer who-owns / which-process / which-KPI / which-playbook / who-approves / role questions from the canonical Business Operating Model (.claude/business) with source ids; conflicts and unknowns are surfaced (OWNER_UNKNOWN, KPI_DEFINITION_MISSING, PROCESS_UNDEFINED, TARGET_UNKNOWN, APPROVAL_RULE_UNKNOWN, SOURCE_CONFLICT), never invented.
- `authority_checking` (I_GOVERNANCE, target L4, executor `authority_checking`): Check a requested action level against a skill's max_action and the approval policy.
- `risk_classification` (I_GOVERNANCE, target L2, executor `risk_classification`): Classify an action LOW/MEDIUM/HIGH/CRITICAL by materiality (pricing/comp/hiring/contract/public/irreversible) and reversibility.
- `data_sensitivity_awareness` (I_GOVERNANCE, target L2, executor `sensitivity_check`): Flag credentials/personal data; redact from logs.
- `completion_verification` (I_GOVERNANCE, target L4, executor `completion_verification`): Distinguish ATTEMPTED/EXECUTED/VERIFIED by re-reading source state (file exists, task status, store record).
- `audit_logging` (I_GOVERNANCE, target L4, executor `audit_logging`): Append a structured audit record to the hardened store for a skill run or manual event.
- `source_verification` (I_GOVERNANCE, target L4, executor `source_verification`): Verify a source exists, is readable, schema matches, freshness; pick the authoritative source.
- `confidence_handling` (I_GOVERNANCE, target L2, executor `confidence_labeling`): Label outputs CONFIRMED/DERIVED/UNVERIFIED/UNKNOWN.
- `structured_data_extraction` (J_TOOL_INTEGRATION, target L2, executor `document_extraction`): Read docx/xlsx/text files (SOPs, roadmaps) and extract structure/paragraphs/tables.

## Per-domain counts (after)

- A_EXECUTIVE_CONTROL: 16
- B_SALES_MANAGEMENT: 13
- C_OPERATIONS_MANAGEMENT: 8
- D_PEOPLE_PERFORMANCE: 1
- E_PROCESS_AUTOMATION: 4
- F_DATA_BI: 3
- G_COMMUNICATION: 4
- H_MEMORY_CONTEXT: 5
- I_GOVERNANCE: 7
- J_TOOL_INTEGRATION: 1
