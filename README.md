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

## Դիմացկունություն — GitHub + մեկ վերականգնման բանալի = ամբողջական Command-center

**Օրենք.** Կարևոր լոկալ-միայն ճշմարտություն չկա։ Այն, ինչ վաղը պետք է Deputy-ին կամ Գև-ին, կա՛մ (1) ուղիղ versioned է Git-ում, կա՛մ (2) versioned է որպես գաղտնագրված վերականգնման artifact, կա՛մ (3) դետերմինիստիկ վերակառուցվում է versioned բովանդակությունից։ Միայն ephemeral կամ մեքենային կապված տվյալն է լոկալ։

Նոր համակարգիչ →
```
git clone https://github.com/ohanyan88-cmd/Command-center.git
cd Command-center
python bootstrap.py            # կամ py -3 bootstrap.py — idempotent, ոչինչ չի ջնջում/չի վերագրում
```
`bootstrap.py`՝ արմատ · նախապայմաններ (Python ≥3.11, git, gpg) · կանոնական պանակներ · `.venv` + pinned կախվածություններ · գաղտնագրված credential-ների վերականգնում (եթե բանալին կա) · Deputy-ի դիմացկուն state-ի import · boundary hooks · Business Model rebuild (sources → extract → build → validate → certify) · workspace + tree-manifest validation · checksums · business/integration certification · skill validation (`--release`՝ ամբողջական release) · վերջնական READY/NOT READY։

| Ինչ | Որտեղ | Ինչպես է վերականգնվում |
|:---|:---|:---|
| `CLAUDE.md · README.md · Tasks.xlsx · Journal.md · Actions.md · bootstrap.py`, `00_Inbox…05_Archive` (բոլոր բիզնես փաստաթղթերը, աղբյուրները, արխիվները) | Git (VERSION_DIRECTLY) | clone. դատարկ պանակները՝ `.gitkeep`-ով |
| Business Operating Model՝ core `bm_*.py` **և** overlay `overlay/ov_*.py` | Git (VERSION_DIRECTLY, Գև-ի որոշմամբ) | clone → `build_business_model.py` (generated json/md՝ REGENERATE) |
| Deputy-ի դիմացկուն հիշողություն՝ commitments, decisions, audit, actions, observations | Git՝ `.claude/state/durable/*.jsonl` (`state_snapshot.py export`՝ `skill.py sync`-ում և release-ում ավտոմատ) | bootstrap → `state_snapshot.py import` (idempotent, op_id-ով, կրկնություն չկա) |
| Արտաքին համակարգերի credential-ներ (`~/.command-center/integrations/*.json`) | Git՝ `.secure/credentials.gpg` (GnuPG AES-256) + `.secure/manifest.json` (անուններ/checksum, ոչ արժեք) | bootstrap → `secure_recovery.py restore`, **միայն** վերականգնման բանալով |
| Runtime (`.venv`), generated model/certification | REGENERATE | bootstrap |
| SQLite store, journal, locks, integration cache/health, audit mirror, `settings.local.json`, `desktop.ini` | EPHEMERAL / MACHINE_LOCAL | չի versioned, վերստեղծվում է |

**Մեկ արտաքին գաղտնիք՝ վերականգնման բանալին** `~/.command-center/recovery.key` (կամ `COMMAND_CENTER_RECOVERY_KEY_FILE`)։ Երբեք Git-ում, log-ում, audit-ում, տերմինալում։ Գև՝ պահիր պատճենը password manager-ում կամ արտաքին սարքի վրա (ֆայլի բովանդակությունը՝ մեկ տող)։ Առանց բանալու՝ ամեն ինչ վերականգնվում է, բացի արտաքին credential-ներից (ինտեգրումները մնում են NOT_CONFIGURED և դա ասվում է բարձրաձայն)։

**Երկու ուղի, մեխանիկապես տարանջատված (policy `durability.live_data`, 1.7.0).**

| Ինչ փոխվեց | Դաս | Ուղի |
|:---|:---|:---|
| `Tasks.xlsx` տող (create/assign/due/status/close/reopen/note), `Journal.md`, `00_Inbox/Input.md`, բիզնես փաստաթուղթ, որը մոդելի extraction աղբյուր չէ, `.claude/state/durable/*`, `durable_checksums.json` | LIVE DATA / DOCUMENT / DURABLE_STATE / INTEGRITY_META | **`skill.py sync`** — classify → durable state export → ստատիկ մոդելը դեռ վկայագրվա՞ծ է (առանց rebuild) → checksums refresh → commit միայն այդ ուղիները → push → origin ստուգում |
| Կոդ, policy, hooks, skills, tests, `bm_*.py`/overlay, extraction աղբյուր (S01…S16 բացի S09-ից), ռեեստրի **կառուցվածք** (sheet/header) | PRODUCT / MODEL_SOURCE / RELEASE_ARTIFACT | **`skill.py release`** (rebuild → certify → validate → eval → checksums) |
| Անհայտ ուղի | UNKNOWN | fail closed — ոչինչ չի sync-վում |

`Tasks.xlsx`-ը **LIVE OPERATIONAL SOURCE** է (S09 · `source_kind: LIVE_REGISTER` · `fingerprint_scope: STRUCTURE`)՝ մոդելը կապված է միայն նրա կառուցվածքին (թերթ + header բլոկ), տողերը կարդացվում են live՝ INT-TASKS-ով (retrieved_at/freshness ամեն ընթերցման)։ Տողի փոփոխությունը core fingerprint-ը չի փոխում, STALE_MODEL չի առաջացնում, rebuild/certification/release չի պահանջում։ Drift-ը ամեն սեսիա երևում է Daily Brief-ում (`🔄 GitHub sync ✓` կամ `ՉԻ ՀԱՄԱԺԱՄԱՆԱԿԵՑՎԱԾ — SYNC_REQUIRED/RELEASE_REQUIRED/UNCLASSIFIED`), `tree_manifest.py drift`-ով՝ ձեռքով։

Կանոնական ծառի պայմանագիր՝ `.claude/policy/workspace_tree_manifest.json` (գեներացվում է policy-ից `tree_manifest.py build --write`-ով, validator-ը ստուգում է համապատասխանությունը և ֆիզիկական գոյությունը), checksum-ներ՝ `.claude/policy/durable_checksums.json`։ Parity՝ `tree_manifest.py snapshot` աղբյուրում և վերականգնվածում → `tree_manifest.py parity a b`։ Scanner-ի սեմանտիկա (2.0)՝ **արգելում է միայն RESTRICTED** (credential, token, գաղտնաբառ, private key, բանալի, connection string); բիզնես տեղեկատվությունը (անուններ, աշխատավարձ, փաստաթղթեր) CONFIDENTIAL awareness է՝ versioned Գև-ի որոշմամբ։ `.secure/`՝ գաղտնագրված artifact-ի պանակն է. `_TEMP_WORK_COLLECTION/`՝ ժամանակավոր staging, չի versioned մինչև Գև-ի review-ն։

Business Operating Model՝ `.claude/business/`, երկու շերտ. **CORE** (INTERNAL, versioned)՝ `bm_*.py` authoring, `bm_schema.py`, `bm_targets.py`, `build_business_model.py`, `certify_business.py` — դերեր առանց վարձատրության, գործընթացներ, ownership ըստ ԴԵՐԻ, KPI-ներ, վերահսկվող targets/thresholds, playbooks, routines, gaps, աղբյուրների metadata, մարդիկ միայն `@P` token-ներով; **SENSITIVE OVERLAY** (CONFIDENTIAL, միայն լոկալ)՝ `overlay/ov_*.py` → `overlay.json` (անուն ↔ token, դեր ↔ մարդ, աշխատավարձ, առևտրային թվեր, ապացույցներ)։ Գեներացված `*.json`/`Business-model.md`/`certification.json`՝ լոկալ։ Pipeline՝ sources → extract → validate → core → overlay → fingerprint → certify (schema 2.0, model_version, source snapshot; STALE_MODEL/SOURCE_MISSING հայտնաբերում)։ Սահմանը մեխանիկական է՝ `.claude/policy/data_classification.json` (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED) + `sensitive_scan.py` (pre-commit/pre-push hooks, validator, certification)։ Engine-ը ամեն governed գործարկման մեջ ներարկում է business context (playbook, KPI, process, owner ROLE → CURRENT PERSON միայն CONFIRMED assignment-ով, sources, model identity, gap codes՝ OWNER_UNKNOWN · KPI_DEFINITION_MISSING · PROCESS_UNDEFINED · TARGET_UNKNOWN · APPROVAL_RULE_UNKNOWN · SOURCE_CONFLICT · STALE_MODEL · SOURCE_CHANGED · SOURCE_MISSING · BUSINESS_CONTEXT_MISSING)։ Չատից եկած գիտելիքը միայն OBSERVATION է (state store), core-ը չի փոխում. promotion՝ OBSERVATION → PROPOSED → CONFIRMED → APPROVED → SUPERSEDED։ Private Git-ը secrets database չէ. սահմանը գործում է անկախ repo-ի visibility-ից։

## Live աղբյուրներ — ինտեգրման շերտ (ՄԻԱՅՆ ԿԱՐԴԱԼ)

`.claude/integrations/` — Deputy-ի «աչքերը»։ Ամեն արտաքին համակարգ **անվստահելի աղբյուր է, մինչև վկայագրվի**. CONNECTION AVAILABLE ≠ DATA TRUSTED ≠ BUSINESS FACT CONFIRMED։ Ճանապարհը միշտ նույնն է՝ BUSINESS SKILL → BUSINESS QUERY → `layer.query(id, op)` → adapter (ֆիքսված read op) → նորմալացված envelope (source_system, source_record_id, retrieved_at, source_updated_at, freshness LIVE/CACHED/STALE/UNAVAILABLE, classification, authority, confidence, provenance) → skill։ Vendor schema-ն skill-ին չի հասնում։

| Integration | Համակարգ | Auth | Կարդում է | Գրում է | Վիճակ |
|:---|:---|:---|:---|:---|:---|
| `INT-TASKS` | Tasks.xlsx (կանոնական ռեեստր) | լոկալ ֆայլ | tasks.list | tasks.create/update/assign/close/reopen/note (միայն Action Runtime-ով, Գև-ի հաստատմամբ) | certify-ով |
| `INT-OL-CAL` | Outlook desktop օրացույց (սեփականատիրոջ housenet.am mailbox) | Windows session + integrity-pinned `outlook_read.ps1` | calendar.events | calendar.create/update/cancel (Action Runtime) | certify-ով |
| `INT-OL-MAIL` | Outlook desktop փոստ | նույնը | mail.list · mail.search (header + ≤600 նիշ preview) | mail.draft (provider-side) · mail.send (Action Runtime) | certify-ով |
| `INT-B24` | Bitrix24 REST | read-scoped inbound webhook (repo-ից դուրս) | crm.deals/leads/stages/activities · tasks.list · users · identity — GET-only allowlist | tasks.create · crm.deal.update · crm.activity.create (Action Runtime; NOT_CONFIGURED մինչև webhook) | DECLARED, մինչև webhook |
| `INT-MB` | MikroBill | UNKNOWN (interface չի գույքագրված) | — | tariff.change · subscriber.suspend՝ **WRITE NOT CERTIFIED / UNAVAILABLE** (R3) | DECLARED |

Կանոններ՝ ընթերցող շերտի `write_ops` ամեն տեղ դատարկ է (գրելը միայն ստորև նկարագրված Action Runtime-ով է). գրող intent-ը (SEND_EMAIL, CREATE_EVENT, UPDATE_DEAL, DELETE_TASK, CHANGE_TARIFF, UPDATE_CUSTOMER…) կառուցվածքով արգելվում է՝ `layer.capability()` → AUTHORITY_EXCEEDED/WRITE_DISABLED, gate/engine → `action_runtime` (ոչ թե գործիք). աղբյուրների հեղինակությունը **կոնֆիգուրացված է** (`registry.FACT_AUTHORITY`, նաև core `sources.json → live_sources`), նույն մակարդակի երկու live աղբյուրի անհամաձայնություն = SOURCE_CONFLICT (չի միաձուլվում). freshness-ը միշտ երևում է, թարմության կանոն չկա՝ չի հորինվում. health (AVAILABLE · DEGRADED · UNAVAILABLE · AUTH_FAILED · PERMISSION_DENIED · SCHEMA_CHANGED · NOT_CONFIGURED) + վերջին հաջող ընթերցում՝ `.claude/state/integrations_health.json`, Daily Brief-ը անհասանելի կրիտիկական աղբյուրը **բարձրաձայն** է ասում. փոստից քաղվածը միայն CANDIDATE_OPEN_LOOP է (ACTION · DECISION · DELEGATE · MONITOR · FYI · IGNORE), ոչ մշտական փաստ. secrets՝ `~/.command-center/integrations/<ID>.json` կամ `CC_<ID>_<KEY>` env, երբեք repo/audit (LEAK_PREVENTED). աուդիտում՝ ինչ հարցվեց (op, param keys, count), ոչ payload։ Վկայագրում՝ `python .claude/integrations/integration.py certify` → DECLARED → CONFIGURED → CONNECTED → VERIFIED_READ → RELIABLE_READ (≥10 իրական ընթերցում ≥2 օրում), ապացույցներով (auth, scope, write_rejected, schema, freshness, failure matrix, provenance, sensitive boundary). `skill.py release`-ը այն սպառում է։ Հրամաններ՝ `integration.py status | query <id> <op> | probe | brief | capability "<intent>"`։

## Ձեռքեր — Action Runtime (Mission 4.2, AUTONOMOUS EXTERNAL WRITE AUTHORITY = NONE)

`.claude/skills/actions.py` + `action_runtime` հմտություն + `.claude/integrations/capabilities.py` և write adapter-ներ (`adapter_tasks_write.py`, `adapter_outlook_write.py` + integrity-pinned `outlook_write.ps1`, `adapter_bitrix24_write.py`)։ Օրենքը՝ `.claude/policy/approval_rule.json` (մեկ տեղում, չի կրկնօրինակվում)։

```
INTENT → PREPARE (capability · authority · duplicate · precondition · fingerprint · idempotency key)
      → ԳԵՎ-Ի ՔԱՐՏ  «READY FOR YOUR APPROVAL … Nothing has been changed yet. Approve?»
      → APPROVAL  միայն OK / GO / Արա / Հաստատում եմ  (մեկանգամյա տոկեն · 24ժ · կապված ճշգրիտ fingerprint-ին · batch = ճշգրիտ ցանկ)
      → EXECUTE  (actions.lock · stale-state վերընթերցում → STALE_CONFLICT · audit-first, AUDIT_UNAVAILABLE = չի կատարվում)
      → VERIFY   (անկախ read-back; API success ≠ ավարտ)  → REPORT  DONE / NOT DONE / PARTIAL / BLOCKED / RESULT_UNKNOWN
```

| Վիճակ | Նշանակում է |
|:---|:---|
| APPROVAL_REQUIRED / DENIED | պատրաստ է կամ մերժված կանոնով (CAPABILITY_UNAVAILABLE · NOT_CONFIGURED · AUTHORITY_EXCEEDED · DUPLICATE · ALREADY_EXISTS · TARGET_NOT_FOUND) — ոչինչ չի փոխվել |
| APPROVED → EXECUTING → EXECUTED_UNVERIFIED → VERIFIED | տոկենը սպառվում է առաջին կատարումից; VERIFIED = read-back-ը համընկնում է հաստատված գործողությանը |
| REJECTED | Գև-ը մերժեց, կամ թիրախը փոխվել էր քարտից հետո (STALE_CONFLICT), կամ տոկենը՝ ժամկետանց/այլ գործողության |
| RESULT_UNKNOWN | provider-ը չպատասխանեց → RECONCILE FIRST (FOUND → verify, ABSENT → retry թույլատրելի, UNDETERMINED → Գև-ի որոշում); կույր retry չկա |
| PARTIAL | batch-ի մի մասն է կատարվել — ազնիվ ցուցակ, rollback չի ձևացվում |

Հնարավորությունների ռեեստր (`capabilities.table()`)՝ DECLARED → IMPLEMENTED → CONFIGURED → CONNECTED → VERIFIED_READ → **VERIFIED_WRITE** (միայն `.claude/state/durable/write_certifications.json`-ից՝ Գև-ի հաստատած իրական գրառում) / UNAVAILABLE։ Idempotency-ն restart-ից հետո էլ պահպանվում է (`.claude/state/durable/actions.jsonl` → hardened store)։ Թեստեր՝ `test_actions` (governance · idempotency/failure · verification · Tasks adapter temp copy-ի վրա · capability/routing), eval բաժին G (18 վարքային սցենար)։ Թեստերն ու eval-ները **երբեք** իրական Tasks.xlsx-ին կամ Outlook-ին չեն դիպչում (env `COMMAND_CENTER_TASKS_XLSX` + sha guard, FakeProvider)։

Python runtime՝ դետերմինիստիկ. ամեն hook, CLI, test, eval և release աշխատում է `<root>/.venv`-ով (`.claude/runtime/` — `python_runtime.py` shim, `hook.sh` launcher, `requirements.txt` manifest + `requirements.lock`), PATH-ի `python`-ը դեր չունի։ `.venv`-ը git-ում չէ. վերակառուցում՝ `py -3 .claude/runtime/python_runtime.py bootstrap`։
