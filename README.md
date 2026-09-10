# Command-center

**Command-center is Gev's operational workspace for Sales & Operations, managed with Deputy — AI Chief of Staff for Sales & Operations.**
HouseNet ՍՊԸ · ամեն աշխատանքային օրը սկսվում է այստեղից։

Ի՞նչ է սա մեկ նախադասությամբ՝ մեկ հսկվող միջավայր ընթացիկ գործի, գործող բիզնես-հենքի, առաջադրանքների, անելիքների, օրագրի, հում աղբյուրների, ավարտվածի, արխիվի և Deputy-ի runtime-ի (skills, governance, tests, state, audit) համար։

> Այս ֆայլը մարդու ուղեցույցն է։ **Մեքենայական հեղինակությունը** `.claude/policy/workspace_policy.json`-ն է (կառուցվածք, անվանում, identity)։ Եթե երկուսը հակասեն՝ policy-ն է ճիշտ, և `validate_workspace.py`-ը ձախողվում է մինչև README-ն ուղղվի։

---

## Արմատում (ընդամենը 5 ֆայլ)

| Ֆայլ | Ինչի համար |
|:---|:---|
| **[Tasks.xlsx](Tasks.xlsx)** | 🎯 Միակ կենդանի առաջադրանքների ռեեստրը։ Գև-ը կարգավիճակ փոխում է ուղիղ այստեղ. Deputy-ն կարդում է այն ամեն սեսիա։ |
| **[Journal.md](Journal.md)** | Ինչ արվեց ամեն օր։ Նոր օրը՝ վերևում։ Ամեն տեղափոխում/վերանվանում գրանցվում է այստեղ։ |
| **[Actions.md](Actions.md)** | Ներքին անելիքներ՝ փաստաթղթերի և համակարգի վրա։ |
| **[CLAUDE.md](CLAUDE.md)** | Deputy-ի վարքի կանոնագիրը (ուղեցույց, ոչ հարկադրանք)։ |
| **README.md** | Այս ֆայլը։ |

## Պանակներ (fixed contract)

| Պանակ | Պատասխանատվություն |
|:---|:---|
| **[00_Inbox/](00_Inbox/)** | 📥 Մուտքի սեղան։ Ամեն ինչ, ինչ չգիտես ուր դնել՝ գցի այստեղ. Deputy-ն դասավորում է։ Կայուն վիճակ՝ դատարկ, բացի [Input.md](00_Inbox/Input.md)-ից (հում տեքստի տեղը)։ |
| **[01_Active/](01_Active/)** | Ընթացիկ գործ՝ `Sales/` · `Operations/` · `People/` · `Systems/`։ Միայն այն, ինչ հիմա մշակվում, ստուգվում կամ կատարվում է։ |
| **[02_Reference/](02_Reference/)** | Հաստատված, **դեռ գործող** ճշմարտություն (օր.՝ Staffing-plan)։ Նույն 4 ենթապանակները։ |
| **[03_Completed/](03_Completed/)** | Ավարտված deliverable-ներ, որոնք այլևս ընթացիկ ճշմարտություն չեն։ |
| **[04_Sources/](04_Sources/)** | Հում ապացույց՝ `Whatsapp/` (export-ներ), `Screenshots/`, `Imports/`։ Ոչ մի կոդ, ոչ մի մշակված deliverable։ |
| **[05_Archive/](05_Archive/)** | Հնացած տարբերակներ, սևագրեր, հին implementation։ Պատմություն է, ոչ ճշմարտություն։ Ոչինչ չի ջնջվում։ |
| **`.claude/`** | Deputy runtime՝ `hooks/` (brief, skill gate, workspace guard) · `docs/` (Role, Job-description, audits) · `policy/` (contract + validator) · `skills/` (Skill System) · `tools/` (helper programs) · `tests/` · `state/` · `audit/`։ |

## Անվանման ստանդարտ

Բիզնես ֆայլերն ու պանակները՝ անգլերեն, `First-word-hyphenated[-vN.N][-YYYY-MM-DD].ext`։
Օրինակներ՝ `Billing-roadmap-v2-2026-09-07.docx` · `Staffing-plan-2026-09-07.xlsx` · `Sales-strategy-2026-09-09.docx` · `Open-questions.md`։
Առանց բացատի, փակագծի, «(2)», «final/new/copy/fixed»; ամսաթիվը միայն `YYYY-MM-DD`, տարբերակը միայն `vN`/`vN.N`, տարբերակը ամսաթվից առաջ, ընդլայնումը փոքրատառ։
Տեխնիկական բացառություններ (policy-ում)՝ `.claude`, `CLAUDE.md`, `README.md`, `settings.json`, Python `snake_case.py`, runtime-ի գեներացված ֆայլեր։

## Ինչպես ենք աշխատում

- **Ամեն ինչ, ինչ ձեռքդ ընկնում է** → գցի `00_Inbox/`։ Deputy-ն տանում է ճիշտ տեղը, վերանվանում, գրանցում Journal-ում։
- **Դու** աշխատում ես `Tasks.xlsx`-ում՝ փոխում ես կարգավիճակներ, գրում մեկնաբանություններ։
- **Սկրիպտ, .bat, ոչ մի բան չես գործարկում** — վերակառուցում պետք լինի, ասում ես Deputy-ին։
- **Deputy-ն** ամեն սեսիա բացելիս տալիս է Deputy Daily Brief-ը՝ workspace-ի վիճակ, մուտք, ժամկետանց/այսօր, սպասումներ, խոստումներ։ Դերը՝ [.claude/docs/Role.md](.claude/docs/Role.md)։

## Հարկադրանք (մեխանիկական, ոչ միայն տեքստ)

| Շերտ | Ինչ է անում |
|:---|:---|
| SessionStart | `hooks/brief.py`՝ workspace validation + Deputy Daily Brief (Skill Engine-ով, աուդիտված) |
| Ամեն հաղորդագրություն | `hooks/gate.py`՝ intent → skill resolution → gate ticket |
| Գրող գործիքից առաջ | `hooks/gate.py` (skill gate) + `hooks/workspace_guard.py` (ուղի/անուն policy-ով) → deny |
| Գրող գործիքից հետո | `workspace_guard.py`՝ ամբողջ ծառի validation, խախտումը՝ բարձրաձայն |
| Release/certify | `skill.py release` = workspace validation → build → certify (բոլոր suite-երը, ներառյալ `test_workspace`) → validate → eval |

Հրամաններ՝ `python .claude/policy/validate_workspace.py` · `python .claude/skills/skill.py release` · `python .claude/skills/skill.py status`։

Business Operating Model՝ `.claude/business/`, երկու շերտ. **CORE** (INTERNAL, versioned)՝ `bm_*.py` authoring, `bm_schema.py`, `bm_targets.py`, `build_business_model.py`, `certify_business.py` — դերեր առանց վարձատրության, գործընթացներ, ownership ըստ ԴԵՐԻ, KPI-ներ, վերահսկվող targets/thresholds, playbooks, routines, gaps, աղբյուրների metadata, մարդիկ միայն `@P` token-ներով; **SENSITIVE OVERLAY** (CONFIDENTIAL, միայն լոկալ)՝ `overlay/ov_*.py` → `overlay.json` (անուն ↔ token, դեր ↔ մարդ, աշխատավարձ, առևտրային թվեր, ապացույցներ)։ Գեներացված `*.json`/`Business-model.md`/`certification.json`՝ լոկալ։ Pipeline՝ sources → extract → validate → core → overlay → fingerprint → certify (schema 2.0, model_version, source snapshot; STALE_MODEL/SOURCE_MISSING հայտնաբերում)։ Սահմանը մեխանիկական է՝ `.claude/policy/data_classification.json` (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED) + `sensitive_scan.py` (pre-commit/pre-push hooks, validator, certification)։ Engine-ը ամեն governed գործարկման մեջ ներարկում է business context (playbook, KPI, process, owner ROLE → CURRENT PERSON միայն CONFIRMED assignment-ով, sources, model identity, gap codes՝ OWNER_UNKNOWN · KPI_DEFINITION_MISSING · PROCESS_UNDEFINED · TARGET_UNKNOWN · APPROVAL_RULE_UNKNOWN · SOURCE_CONFLICT · STALE_MODEL · SOURCE_CHANGED · SOURCE_MISSING · BUSINESS_CONTEXT_MISSING)։ Չատից եկած գիտելիքը միայն OBSERVATION է (state store), core-ը չի փոխում. promotion՝ OBSERVATION → PROPOSED → CONFIRMED → APPROVED → SUPERSEDED։ Private Git-ը secrets database չէ. սահմանը գործում է անկախ repo-ի visibility-ից։

## Live աղբյուրներ — ինտեգրման շերտ (ՄԻԱՅՆ ԿԱՐԴԱԼ)

`.claude/integrations/` — Deputy-ի «աչքերը»։ Ամեն արտաքին համակարգ **անվստահելի աղբյուր է, մինչև վկայագրվի**. CONNECTION AVAILABLE ≠ DATA TRUSTED ≠ BUSINESS FACT CONFIRMED։ Ճանապարհը միշտ նույնն է՝ BUSINESS SKILL → BUSINESS QUERY → `layer.query(id, op)` → adapter (ֆիքսված read op) → նորմալացված envelope (source_system, source_record_id, retrieved_at, source_updated_at, freshness LIVE/CACHED/STALE/UNAVAILABLE, classification, authority, confidence, provenance) → skill։ Vendor schema-ն skill-ին չի հասնում։

| Integration | Համակարգ | Auth | Կարդում է | Գրում է | Վիճակ |
|:---|:---|:---|:---|:---|:---|
| `INT-TASKS` | Tasks.xlsx (կանոնական ռեեստր) | լոկալ ֆայլ | tasks.list | — | certify-ով |
| `INT-OL-CAL` | Outlook desktop օրացույց (սեփականատիրոջ housenet.am mailbox) | Windows session + integrity-pinned `outlook_read.ps1` | calendar.events | — | certify-ով |
| `INT-OL-MAIL` | Outlook desktop փոստ | նույնը | mail.list · mail.search (header + ≤600 նիշ preview) | — | certify-ով |
| `INT-B24` | Bitrix24 REST | read-scoped inbound webhook (repo-ից դուրս) | crm.deals/leads/stages/activities · tasks.list · users · identity — GET-only allowlist | — | DECLARED, մինչև webhook |
| `INT-MB` | MikroBill | UNKNOWN (interface չի գույքագրված) | — | — | DECLARED |

Կանոններ՝ `write_ops` ամեն տեղ դատարկ է. գրող intent-ը (SEND_EMAIL, CREATE_EVENT, UPDATE_DEAL, DELETE_TASK, CHANGE_TARIFF, UPDATE_CUSTOMER…) կառուցվածքով արգելվում է՝ `layer.capability()` → AUTHORITY_EXCEEDED/WRITE_DISABLED, gate → TOOL_UNAVAILABLE. աղբյուրների հեղինակությունը **կոնֆիգուրացված է** (`registry.FACT_AUTHORITY`, նաև core `sources.json → live_sources`), նույն մակարդակի երկու live աղբյուրի անհամաձայնություն = SOURCE_CONFLICT (չի միաձուլվում). freshness-ը միշտ երևում է, թարմության կանոն չկա՝ չի հորինվում. health (AVAILABLE · DEGRADED · UNAVAILABLE · AUTH_FAILED · PERMISSION_DENIED · SCHEMA_CHANGED · NOT_CONFIGURED) + վերջին հաջող ընթերցում՝ `.claude/state/integrations_health.json`, Daily Brief-ը անհասանելի կրիտիկական աղբյուրը **բարձրաձայն** է ասում. փոստից քաղվածը միայն CANDIDATE_OPEN_LOOP է (ACTION · DECISION · DELEGATE · MONITOR · FYI · IGNORE), ոչ մշտական փաստ. secrets՝ `~/.command-center/integrations/<ID>.json` կամ `CC_<ID>_<KEY>` env, երբեք repo/audit (LEAK_PREVENTED). աուդիտում՝ ինչ հարցվեց (op, param keys, count), ոչ payload։ Վկայագրում՝ `python .claude/integrations/integration.py certify` → DECLARED → CONFIGURED → CONNECTED → VERIFIED_READ → RELIABLE_READ (≥10 իրական ընթերցում ≥2 օրում), ապացույցներով (auth, scope, write_rejected, schema, freshness, failure matrix, provenance, sensitive boundary). `skill.py release`-ը այն սպառում է։ Հրամաններ՝ `integration.py status | query <id> <op> | probe | brief | capability "<intent>"`։

Python runtime՝ դետերմինիստիկ. ամեն hook, CLI, test, eval և release աշխատում է `<root>/.venv`-ով (`.claude/runtime/` — `python_runtime.py` shim, `hook.sh` launcher, `requirements.txt` manifest + `requirements.lock`), PATH-ի `python`-ը դեր չունի։ `.venv`-ը git-ում չէ. վերակառուցում՝ `py -3 .claude/runtime/python_runtime.py bootstrap`։
