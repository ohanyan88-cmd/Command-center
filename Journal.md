# ՕՐԱԳԻՐ

Ամեն օրվա գրառումը՝ ինչ արվեց, ինչ պարզվեց, ինչ մնաց։ **Նոր օրը՝ վերևում։**

---

## 2026-09-10 · հինգշաբթի

### Արվեց

**Workspace → Command-center, agent → Deputy (միգրացիա + մեխանիկական contract)**
- Կանոնական անունները՝ workspace **Command-center**, agent **Deputy — AI Chief of Staff for Sales & Operations** (մեկ աղբյուր՝ `.claude/policy/workspace_policy.json → identity`)։ Ֆիզիկական արմատը դեռ `Daily check` է (formerly). բաց Claude Code-ի cwd-ը վերանվանել անվտանգ չէ — մնացած քայլը՝ փակել Claude Code-ը, `Daily check` → `Command-center`, բացել նորից (memory-ն արդեն պատճենված է նոր project key-ի տակ)։
- Նոր կառուցվածք՝ արմատում `Tasks.xlsx · Journal.md · Actions.md · CLAUDE.md · README.md`; `00_Inbox/Input.md` (մուտք + հում տեքստ), `01_Active/{Sales,Operations,People,Systems}`, `02_Reference/…`, `03_Completed`, `04_Sources/{Whatsapp,Screenshots,Imports}`, `05_Archive`, `.claude/{hooks,docs,policy,skills,tools,tests,state,audit}`։ Ամեն տեղափոխում՝ բովանդակությամբ որոշված անունով, լոգը՝ [.claude/docs/Migration-log-2026-09-10.md](.claude/docs/Migration-log-2026-09-10.md)։
- Հին անուններ → նոր (formerly)՝ `Առաջադրանքներ.xlsx`→`Tasks.xlsx`, `ՕՐԱԳԻՐ.md`→`Journal.md`, `ԱՆԵԼԻՔՆԵՐ.md`→`Actions.md`, `03_Ավարտված/Հաստիքացուցակ_…`→`02_Reference/People/Staffing-plan-2026-09-07.xlsx`, `01_Ընթացիկ/…Billing_Roadmap_v2…`→`01_Active/Systems/Billing-roadmap-v2-2026-09-07.docx`, `Վաճառքի կարճաժամկետ ռազմավարություն.docx`→`01_Active/Sales/Sales-strategy-2026-09-09.docx`, `save-list (2).xlsx`→`01_Active/Sales/Churn-save-list-2026-09-09.xlsx` (churn-ի save list է, «(2)»-ը ներբեռնման կրկնօրինակ էր), `WhatsApp Image…jpeg`→`04_Sources/Screenshots/Churn-risk-signals-2026-09-09.jpeg`, `04_WhatsApp/Բնօրինակներ`→`04_Sources/Whatsapp/Gadukyan-2026-09-09[-afternoon]`, `04_WhatsApp/գործիքներ/*.py`→`.claude/tools/*.py` (անգլերեն տեխնիկական անուններ ըստ գործառույթի), `04_WhatsApp/ՕԳՆԱԿԱՆ_*`→`.claude/docs/Role.md`, `Job-description.md`, `02_Արխիվ`→`05_Archive/Drafts-2026-09-09`։
- Հարկադրանք՝ `workspace_policy.json` (կանոնական contract + identity) · `validate_workspace.py` (SessionStart, release, CLI) · `hooks/workspace_guard.py` (PreToolUse deny + PostToolUse ամբողջ ծառի ստուգում) · `tests/test_workspace.py`։

**Skill System — երկրորդ ալիք. մեխանիկական հարկադրանք, hardened state, per-skill վկայագրում**
- **Hook-եր** (`.claude/hooks/gate.py`, `.claude/settings.json`)՝ UserPromptSubmit (ամեն հաղորդագրություն → skill resolution → gate ticket), PreToolUse (Write/Edit/Bash գրող գործողություններն արգելվում են առանց governed գործարկման; engine/state/registry/hook ֆայլերը՝ protected), PostToolUse (ապացույցի հետք), Stop (resolved ticket առանց գործարկման → հետ, հետո՝ բարձրաձայն ENFORCEMENT_ESCAPE)։ Hook-երն ակտիվացան նույն սեսիայում (file watcher)՝ ապացույց՝ ticket 887a13bbe3, 18 tool event, deny-ներ։
- **State**՝ JSONL → SQLite (`state/skill_state.db`, WAL, BEGIN IMMEDIATE, PRIMARY KEY op_id, checksum, journal-first, quarantine + replay recovery)։ 12 store թեստ՝ 16 thread / 8 process նույն op → ճիշտ 1 գրառում; crash-before-commit; corruption; deterministic recovery։
- **Registry աուդիտ**՝ 132 → 61 հմտություն, 71 մերժված/միաձուլված պատճառով (`registry_audit_2026-09-10.md`); հին registry-ն՝ `02_Արխիվ/2026-09-10_skill_registry_v1/`։ 7 «գործիք-հմտություն» → `tool_intents` (TOOL_UNAVAILABLE)։
- **Per-skill վկայագրում**՝ `certifications/<skill>.json` (61 ֆայլ), հասունությունը հաշվարկվում է mapped ապացույցից (`@covers`), fingerprint = contract ⊕ executor ⊕ engine/store — փոփոխությունը վկայագիրը դարձնում է STALE (ապացուցված)։ Բաշխում՝ L0=8 · L1=21 · L2=15 · L3=7 · L4=10։
- **12 BLOCKED կոդ**, ամեն մեկը թեստով (`test_failclosed.py`); նոր՝ INVALID_SOURCE, STALE_SOURCE (14 օր), CONFLICTING_SOURCE (շղթայով տարածվող), VALIDATION_FAILED, VERIFICATION_FAILED (engine-ը վերաընթերցում է վիճակը)։
- **Router**՝ բառասահման + chain-first + երկար prompt-ի պաշտպանություն; 13 routing eval (under/over-routing), 24 սցենար, 6 bypass eval։ Ընդհանուր՝ 161 թեստ + 43 eval, release OK։
- **Git**՝ լոկալ repo, remote `ohanyan88-cmd/Assistant`, **push չի արվել** (Գև-ի ցուցումով); `.gitignore`-ը բիզնես ֆայլերը (xlsx, WhatsApp, docx, օրագիր) դուրս է թողնում։

**Տնից միանալը լուծվեց (VNC)**
- TightVNC + Tailscale-ով՝ տնից միանում ես `100.120.46.109`-ին, պառոլ 1234։ Windows-ի պառոլ պետք չէ։
- Երեկվա ձախողման պատճառը՝ VNC պառոլը դրված չէր։ Դրվեց (ադմին PowerShell-ով), ստուգվեց՝ աշխատում է։

**Ֆոլդըրի քլինափ**
- Արմատը իջավ 4 ֆայլի՝ `Առաջադրանքներ.xlsx` · `ՕՐԱԳԻՐ.md` · `ԱՆԵԼԻՔՆԵՐ.md` · `README.md`։
- Կրկնվող ու սևագիր ֆայլերը գնացին `02_Արխիվ/2026-09-09_սևագրեր/`՝ հին 8-թերթ ԱՌԱՋԱԴՐԱՆՔՆԵՐ.xlsx, ԳԱԴՈՒԿՅԱՆԻ_ՊԱՀԱՆՋՆԵՐԸ.md, ԳՐԱՖԻԿԻ_ՀԱՐՑԵՐ.md, ԹԱՐՄԱՑՆԵԼ.bat, run.py։
- `ՀԱՐՑԵՐ.md` (դեռ բաց հարցերով) → `04_WhatsApp/ՀԱՐՑԵՐ_բաց.md`։
- Նոր կանոն՝ սկրիպտ/bat չես գործարկում, վերակառուցումն ասում ես ինձ։

**Q1, Q2-ի պատասխանները ստացվեցին**
- `save-list (2).xlsx` և churn-ի սիգնալների նկարը դրված են `01_Ընթացիկ/`-ում։

**Դերս ամրագրվեց + մուտքի պանակ**
- Ես դարձա Գև-ի գործառնական օգնականը՝ **ամեն ինչի** մասով, ոչ միայն WhatsApp։ Դերի քարտ՝ [.claude/docs/Role.md](.claude/docs/Role.md)։
- Ստեղծվեց `00_ԳՑԻՐ_ԱՅՍՏԵՂ/`՝ մուտքի սեղան։ Գև-ը ամեն ինչ գցում է այնտեղ, ես տանում եմ ճիշտ տեղը, վերանվանում, գրանցում այստեղ։

**Skill System — կառուցվեց ու ապացուցվեց**
- `.claude/skills/`՝ 132 գրանցված հմտություն 10 դոմենով (A–J), ամեն մեկը լրիվ պայմանագրով (triggers, inputs, tools, authority, tests, evals…)։
- Engine՝ intent → skill chain (router + dependency graph), fail-closed դարպաս (MISSING_INPUT / TOOL_UNAVAILABLE / NOT_OPERATIONAL / APPROVAL_REQUIRED), իշխանության սանդուղք՝ հասունությունից առանձին, JSONL audit ամեն գործարկման։
- Իրական executors՝ `Առաջադրանքներ.xlsx`-ի վրա (բրիֆ, ժամկետներ, սպասում-եմ, առաջնահերթություն, խոստումներ, որոշումների լոգ, ստուգում)։ Վաճառքի/գործառնական/անձնակազմի վերլուծությունները՝ L0/L1, առանց տվյալի BLOCKED են — թիվ չեն հորինում։
- Ապացույց՝ 66/66 unit test · 29/29 hardening (adversarial + failure injection) · 17/17 behavioral eval · validate 0 խնդիր։ Հասունությունը շնորհվում է միայն `certify`-ով՝ իրական թեստից։ 12 միջուկային հմտություն՝ L4 (ապացույցով)։
- Հարկադրանք՝ CLAUDE.md-ում պարտադիր `skill.py resolve` դարպաս; SessionStart բրիֆը հիմա անցնում է engine-ով՝ audited։
- `skill.py release` = build → certify → validate → eval — պայմանագիր փոխելու միակ ճանապարհը։

**JD + հարդենինգ + մաքրության սկզբունք**
- Ստացվեց իմ ամբողջական 53-կետ charter-ը (Executive Assistant / S&O-ի տեղակալ) → `04_WhatsApp/ՕԳՆԱԿԱՆ_JD.md`։
- Ավելացվեց հարկադրանք՝ `CLAUDE.md` (ինքնաշխատ կարդացվող) + `.claude/settings.json` SessionStart hook → `brief.py` (ամեն սեսիա՝ մուտք + ժամկետանց/այսօր)։
- Ավելացվեց մշտական սկզբունք՝ **ԱՄԵՆ ԻՆՉ ՄԱՔՈՒՐ, ԹԱՓԹՓՎԱԾ ԱՇԽԱՏԱՆՔ = 0**։
- Կիրառվեց միանգամից՝ վերանվանվեց `...v2 (1).docx` → `HouseNet_Billing_Roadmap_v2_2026-09-07.docx`։

---

## 2026-09-09 · չորեքշաբթի

### Արվեց

**Ֆոլդըրը դասավորվեց**
- `01_Ընթացիկ/` · `02_Արխիվ/` · `03_Ավարտված/` · `04_WhatsApp/`, արմատը՝ մուտքի տեղ։
- Ֆայլերի անվանման կանոն՝ `Անուն_vՏարբերակ_ՏՏՏՏ-ԱԱ-ՕՕ`։
- Ավելացվեցին [README.md](README.md), սույն օրագիրը, [Actions.md](Actions.md)։
- **Հաստիքացուցակը** հայտարարվեց վերջնական և հաստատված → `03_Ավարտված/`։ Այսուհետ հենակետն է։

**Առաջադրանքների համակարգ**
- Ստացվեց Gadukyan-ի չատի export-ը (09-05 – 09-09, 244 տող), արխիվացվեց `04_WhatsApp/Բնօրինակներ/`։
- Կառուցվեց ռեեստրը՝ **8 թերթ**՝ ԱՄՓՈՓ · ՕՐՎԱ ՊԼԱՆ · ՔԱՐՏԵՐ · ՍՏԱՑՎԱԾ · ՏՐՎԱԾ · ԳՐԱՆՑԱՄԱՏՅԱՆ · ԱՆՁԻՆՔ · ՀԱՐՑԵՐ։
- **23 ստացված** և **7 տրված** առաջադրանք, ամեն մեկը՝ լուծումով, հաջորդ քայլով, կախվածությամբ։
- Ավելացվեց մեկ սեղմումով թարմացում՝ [update.bat](05_Archive/Drafts-2026-09-09/update.bat)։
- Գրաֆիկը այլևս ձեռքով չի գրվում — **ինքնաշխատ հավաքվում է ռեեստրից**։

### Պարզվեց

**Ամսաթվերի ճշտում**
- «5 շաբթի» = **հինգշաբթի** = 09-10, ոչ թե 5 շաբաթ։ Վաճառքի ռազմավարությունը վաղն է ներկայացվում։

**JD ↔ Հաստիքացուցակ**
- Անհամապատասխանություն չկա։ 29 հաստիք երկուսում էլ, անունները՝ տառ առ տառ նույն։
- 52 = քանակների գումար · 54 = +2 ԱՁ · 57 = +3 ղեկավար։ Համալրվածություն՝ 25/52։

**Առաջին ընթերցումը կիսատ էր** — վերընթերցումից հետո ավելացվեցին 6 բաց թողնված կետ․
- «4 ամսվա մեջ ամսական 2% իջնելու հարցը» — Gadukyan-ի 4 պահանջից **կրիտիկականը**, բովանդակությունը դեռ չճշտված։
- Կորպի ամսական ռեփորթ — քանի կորպ հաճախորդ ենք տեսել, խոսել, օֆեր արել։
- pros/cons՝ պահո՞ւմ ենք համակարգը, թե բիլինգն ու Հայկի արածը դրա վրա չենք անում։
- Միկրոբիլի կարգավիճակների հաստատում, CRM AI-ի դեմոն, պորտալի ճարտարապետության ստուգում։

**Բիլինգի roadmap**
- Կարդացվեց։ Հայտնաբերվեց ուղիղ **հակասություն**․ փաստաթուղթը Billing-ին տալիս է
  «Reporting & intelligence» մանդատ, dashboards, forecast, churn scoring — իսկ դիրքորոշումը
  BI-ը բիլինգի վրայից հանելն է։ Սա մեկ որոշում է, որ պիտի կայացվի։

**Վաճառքի ռազմավարություն**
- D2D-ն ամբողջական է՝ թվերով, ֆինանսական ճանապարհով, կանգնեցման կանոններով։
- Հեռավաճառքը կա թվերով (2 × 20), բայց չկա «ինչ են անում, ոնց են անում»։
- **Կորպորատիվ բաժինը ընդհանրապես չկա։**

**Bitrix24**
- Իրական թասկերը այնտեղ են։ Ռեեստրում ավելացվեց Bitrix-ի սյունակ։
- Ռեեստրը լրիվ չէ, քանի դեռ Bitrix-ի թասկերը ներսում չեն։

### Մնաց

- Այսօրվա և ժամկետանց կետերը՝ [ՕՐՎԱ ՊԼԱՆ](05_Archive/Drafts-2026-09-09/Task-workbook-8-sheet-2026-09-09.xlsx) թերթում։
- Բաց հարցերը՝ նույն ֆայլի **ՀԱՐՑԵՐ** թերթում։
- Մեր ներքին գործը՝ [Actions.md](Actions.md)։

## 2026-09-10 · Mission 2 finalization — ֆիզիկական արմատի վերանվանում
- Գև-ը վերանվանեց ֆիզիկական արմատը՝ `Desktop/Daily check` → `Desktop/Command-center` (14:49)։ Claude Code-ը վերաբացվել է նոր արմատից. cwd = git root = `C:\Users\Admin\Desktop\Command-center`։
- Ակտիվ հնացած հղում գտնվեց մեկ հատ՝ `.claude/skills/executors.py` (memory_retrieval-ի project key `…-Daily-check`) → ուղղվեց `…-Command-center`։ Մնացած «Daily check» հղումները պատմական են (policy stale_patterns ցանկ, թեստային fixture, Migration-log, audit/journal հայելիներ, 05_Archive)։
- Runtime project context՝ `~/.claude/projects/c--Users-Admin-Desktop-Command-center/` (սեսիայի transcript + memory)։ Հին key-ի պանակը մնում է որպես պատմություն։
- Հին ֆիզիկական պանակի backup՝ `Desktop/Daily check.zip` (workspace-ից դուրս, Գև-ի)։

## 2026-09-10 · Mission 2 residuals — deterministic Python runtime + maintenance routing boundary
- **Runtime.** Նոր `.claude/runtime/`՝ `python_runtime.py` (shim/bootstrap/launcher), `hook.sh` (settings.json-ի միակ մուտքը), `requirements.txt` (manifest, `# python: 3.13`, պիններ) + `requirements.lock` (pip freeze, `--no-deps`)։ `<root>/.venv` (git-ignored, policy-ում `.venv` = reserved root dir)։ Բոլոր hook-երը, `skill.py`, certify/build, tests, evals, release-ը աշխատում են միայն `.venv`-ով. PATH-ի python-ը (3.12 դատարկ / 3.13 / ընդհանրապես չկա) վարքը չի փոխում — ապացուցված (test_runtime + ձեռքով)։ Առավոտվա 3.12-ի գլոբալ `openpyxl` տեղադրումը հետ եմ վերցրել (գլոբալ վիճակից կախում = 0)։
- **Routing.** engine.resolve-ում ավելացավ SYSTEM/MAINTENANCE domain boundary. agent runtime / Skill System / hooks / workspace policy / tests / repo / config / architecture / state-audit մտադրությունները այլևս չեն գնում Sales/Ops հմտություններ («fix the skill execution pipeline» → UNRESOLVED·SYSTEM, «our sales pipeline is falling» → pipeline_management)։ Fail-closed անփոփոխ՝ state գործիքները մերժվում են մինչև maintenance/declare։ Ռեգրեսիա՝ 14 boundary eval, T02b_DomainBoundary, E06_MaintenanceRoutingBoundary։
- **Release** (`.venv`, 3.13)՝ 212 test, 57 eval, 61 վկայագիր, distribution անփոփոխ (L4 10 · L3 7 · L2 15 · L1 21 · L0 8)։ Policy 1.2.0։

## 2026-09-10 · Git alignment — առաջին push
- GitHub auth՝ Գև-ը device-code-ով մուտք գործեց `ohanyan88-cmd` (admin)։ Repo `ohanyan88-cmd/Assistant` → **`ohanyan88-cmd/Command-center`** (հին անունը redirect է), description դրված, visibility անփոփոխ (public)։
- Լոկալ `master` → `main`, origin՝ `https://github.com/ohanyan88-cmd/Command-center.git`։ Push `main` (առանց force), upstream `origin/main`։ HEAD = origin/main = `70c9c41`, ahead/behind 0, working tree մաքուր։
- Remote ծառը՝ 101 blob, նույնական լոկալին. `.venv`, state/audit, բիզնես ֆայլեր (Tasks.xlsx, Journal, 00–05 պանակներ), secrets չկան։ Push-ից առաջ վերջին release՝ 212 test, 57 eval, 61 վկայագիր (commit `70c9c41`՝ միայն certified_at)։

## 2026-09-10 · Mission 3 — Business Operating Model (HouseNet)
- Նոր `.claude/business/`՝ 15 աղբյուրի inventory (S01 հաստիքացուցակ APPROVED = հիմք; S02 JD v1.1; S03 վաճառքի ռազմավարություն PROPOSAL; S04 բիլինգի roadmap; S05/S06 churn; S07/S08 WhatsApp; S09 Tasks; S10 հարցեր; S11 գրաֆիկ; S12–S13 արխիվ HISTORICAL; S14 Actions; S15 charter)։ Մոդել՝ 34 դեր, 5 ֆունկցիա, 7 համակարգ, 24 գործընթաց (որից 3 GAP), 56 ownership գրառում, 31 KPI + 97 դերային KPI (թիրախներ՝ բոլորը UNKNOWN), 18 playbook, 6 routine, 7 հակասություն (C01 BI-ի տերը, C02 retention-ի տերը, C03 churn-զանգերի հետևում, C05 D2D 7000/8000, C08 բիլինգի ենթակայություն, C09 դիսպետչեր, C10 JD անուններ), 9 կրիտիկական անհայտ, 20 բաց (gap register)։ Բաժանորդային PII չի պատճենվել. մոդելը public repo-ում չի versionավորվում։
- Skill System՝ +1 skill `business_model_query` (62), engine-ը ամեն գործարկման մեջ ներարկում է business context, BLOCKED պատասխանն էլ ասում է ինչ տվյալ/աղբյուր/տեր է սպասվում. 7 gap code fail-closed։ Թեստ՝ test_business (15), evals՝ +12 business (69 ընդամենը)։

## 2026-09-10 · Mission 3.1 — Business brain-ի ամրացում (core/overlay, boundary, staleness, certification)
- Մոդելը բաժանվեց երկու շերտի՝ CORE (`bm_*.py`, schema 2.0, targets, builder, certifier — versioned, INTERNAL. մարդիկ միայն `@P0…@P8` token-ներով, աշխատավարձ/payroll/cost/quote/բաժանորդային ագրեգատ՝ ոչ) և SENSITIVE OVERLAY (`overlay/ov_people|compensation|commercials|evidence.py` → `overlay.json`, CONFIDENTIAL, միայն լոկալ)։ Runtime-ը միացնում է երկուսը. դեր → մարդ միայն CONFIRMED assignment-ով (այսօր միայն Գև ↔ EXEC-SO), մնացածը PERSON_UNKNOWN + candidates։
- Դասակարգում՝ `.claude/policy/data_classification.json` (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED, 23 item, path/content կանոններ)։ Scanner `sensitive_scan.py`՝ pre-commit + pre-push hooks (տեղադրված), validator-ի boundary check, certification-ի `no_restricted_in_core`/`versioned_core_clean`։
- Pipeline՝ sources → extract (S01 KPI կշիռներ, S02 JD քարտեր, S05 թերթեր՝ խաչաձև ստուգում) → validate → core → overlay → fingerprint (core/overlay/snapshot) → certify (17 check)։ Staleness՝ CURRENT / STALE_MODEL / SOURCE_CHANGED / SOURCE_MISSING / UNCERTIFIED, business_model_query-ն fail-closed։ Targets/thresholds՝ միայն `bm_targets.py` (27, APPROVED/PROPOSED/UNKNOWN)։ Promotion կանոններ՝ OBSERVATION → PROPOSED → CONFIRMED → APPROVED → SUPERSEDED, չատը core չի փոխում։
- Workspace՝ `04_Sources/Whatsapp/Gadukyan-*` → `Principal-*`, արխիվի `Gadukyan-requirements-*` → `Principal-requirements-*` (անուն պանակի անվան մեջ = CONFIDENTIAL path)։ Թեստ՝ test_boundary (9), test_business (23)։

## 2026-09-10 · Mission 3.2 — Core-ի remote delivery, overlay-ի գաղտնագրված backup
- Repo `ohanyan88-cmd/Command-center`՝ PUBLIC → **PRIVATE** (Գև-ի թույլտվությամբ). ապացույց՝ API private=true, անանուն GET → 404, առանց credential git → auth պահանջ։ Push-ված պատմության review՝ 5 commit, RESTRICTED/գաղտնիք՝ 0. CONFIDENTIAL՝ 11 ֆայլում 152 անուն-հիշատակում (@P1-ի անունը registry trigger-ում, docs, legacy tools-ի task data, test fixture) — history rewrite ՉԻ արվել (պահանջում է Գև-ի առանձին որոշում)։ Հիմա բոլորը HEAD-ում token-ացված են։
- Push՝ `70c9c41` → `d32b95b` (fa8c496 + invariants/backup), pre-push hook scan clean, local = origin = API, ahead/behind 0։ Remote ծառում core-ի 11 ֆայլ, overlay/generated/state/աղբյուրներ՝ բացակա։
- Extraction invariants՝ բոլոր 13 CURRENT աղբյուրի համար (docx/xlsx/md բովանդակություն + մոդելի սպասվող id-ներ). certification check `extraction_invariants`, test՝ tamper detection։
- Overlay backup՝ `overlay_backup.py` (gpg AES-256 symmetric, sha256 manifest, model/schema/fingerprint), key `~/.command-center/overlay-backup.key` (repo-ից դուրս, չլոգված), archives `~/.command-center/backups/`. Restore drill՝ PASS (decrypt, integrity, fingerprint = production, core+overlay load, plaintext ջնջված)։ Սխալ/բացակա բանալի → բացահայտ ձախողում (test)։
- Հիշեցում՝ Windows credential manager-ի menqstudio token-ը private repo-ն չի տեսնում. `git fetch/push`՝ gh credential-ով (կամ `gh auth setup-git`)։

## 2026-09-11 · Mission 4 — Deputy-ի «աչքերը»՝ live աղբյուրների READ-ONLY շերտ
- `.claude/integrations/`՝ registry (5 ինտեգրում, FACT_AUTHORITY 8 փաստի տիպի համար), contracts (նորմալացված envelope, failure vocabulary, write-intent արգելք), adapters՝ Tasks.xlsx · Outlook (integrity-pinned `outlook_read.ps1`, Python COM-ը այս մեքենայից չի աշխատում, PowerShell-ը՝ այո) · Bitrix24 (GET-only allowlist, credential չկա) · MikroBill (interface չկա), layer (allowlist, cache, health, audit առանց payload, LEAK_PREVENTED), reconcile (ACTION/DECISION/DELEGATE/MONITOR/FYI/IGNORE, CANDIDATE_OPEN_LOOP, SOURCE_CONFLICT, ENTITY_MATCH_UNCERTAIN, meeting pack), certify_integrations (DECLARED→…→RELIABLE_READ)։
- Իրական ընթերցումներ՝ Tasks.xlsx (12 բաց), Outlook mailbox (Inbox 102, identity verified), Outlook calendar (0 իրադարձություն — Գև-ը Outlook-ի օրացույցը չի օգտագործում)։ Certification՝ INT-TASKS / INT-OL-CAL / INT-OL-MAIL VERIFIED_READ, INT-B24 / INT-MB DECLARED։
- Daily Brief՝ TODAY (հանդիպումներ+ժամկետներ+head actions) · OVERDUE · WAITING FOR (+✉ candidates) · SALES/OPERATIONS (միայն VERIFIED live) · DECISIONS · RISKS (integration down, schedule conflict, overdue pileup, SOURCE_CONFLICT) · PREPARATION; դատարկ բաժին չի տպվում. health տողեր՝ վերջին հաջող ընթերցումով։
- Business model 2026-09-11.1՝ S16 (integration registry), U04 թարմացված, SYS-OL ավելացված, SYS-B24/SYS-MB deputy_access ճշտված, core `sources.json → live_sources`։
- Թեստեր՝ test_integrations 29, evals F 8. registry՝ կարդալու trigger-ներ (daily_briefing/open_loop_memory/meeting_preparation), tool_intents՝ միայն write. Policy 1.5.0, classification 1.1.0, .gitignore՝ integrations json։
- Repo-ն Գև-ի հրահանգով դարձավ **PUBLIC** (`gh repo edit --visibility public`, ստուգված՝ API private=false). Գև-ը կասի, երբ նորից private դարձնենք։ HEAD-ը token-ացված է, հին պատմությունը (մինչև 70c9c41) դեռ անուններ ունի։

## 2026-09-11 · Mission 4 արտաքին audit (c3ffda1) — 5 finding-ի փակում
- Repo՝ PUBLIC → **PRIVATE** (audit-ի պահանջ; API private=true, անանուն GET 404, առանց credential git՝ մերժում)։
- F1 cache՝ mail/calendar payload-ները այլևս սկավառակ չեն գրվում (memory-only, ttl-ով); Tasks.xlsx cache-ը hard expiry-ով, prune ամեն load/startup-ին. ժամկետանց payload-ը վերականգնելի չէ։
- F2 audit fail-closed՝ `layer._audit` գրում է hardened store-ով և վերընթերցում; ձախողում → `AUDIT_UNAVAILABLE`, ընթերցումը հետ է պահվում, success evidence չի գրանցվում (նաև cache hit-ի և fixture-ի դեպքում)։
- F3 task authority scope՝ `register_task_*` (Tasks.xlsx) և `crm_task_*` (Bitrix24) առանձին; `reconcile_task_link` երկու status-ը պահում է կողք-կողքի, տարբերություն → STATUS_DIVERGENCE, override չկա. մոդել 2026-09-11.2։
- F4 certification scope՝ `required_certification_ops` ամեն ինտեգրման համար; VERIFIED_READ միայն երբ բոլորը իրական ընթերցումով անցնեն (mail.search-ը հիմա ապացուցված է); fixture-ը scope proof չէ։
- F5 concurrency՝ health/cache RMW՝ cross-process exclusive lock + atomic replace; 16 thread × 10 + 4 process × 25 → success_count ճիշտ։
- Թեստեր՝ +12 (41 test_integrations), release՝ 287 test, 77 eval, maturity՝ անփոփոխ։

## 2026-09-12 · Mission 4.1 — GitHub + վերականգնման բանալի = ամբողջական Command-center
- Դիմացկունության օրենք (policy 1.6.0)՝ կարևոր լոկալ-միայն ճշմարտություն չկա։ Versioned ուղիղ՝ Tasks.xlsx, Journal.md, Actions.md, 00–05 ամբողջությամբ (փաստաթղթեր, աղբյուրներ, WhatsApp export-ներ, արխիվ), Business Model core + overlay, docs/code, Deputy-ի դիմացկուն state (`.claude/state/durable/`՝ commitments, decisions, audit, observations)։ Գաղտնագրված՝ `.secure/credentials.gpg` (արտաքին credential-ներ, հիմա դատարկ՝ B24/MB ABSENT)։ Վերականգնվող՝ .venv, generated model/certification։ Մեքենային՝ Outlook session, settings.local, ~/.command-center։
- Մեկ արտաքին բանալի՝ `~/.command-center/recovery.key` (նույն գաղտնիքը, ինչ overlay-backup.key-ը՝ հին backup-ները բացվում են)։ Երբեք repo/log/audit։
- `bootstrap.py` (15 քայլ, idempotent), `tree_manifest.py` (policy-ից գեներացվող canonical manifest 71 entry + checksums 185 ֆայլ + parity), `state_snapshot.py`, `secure_recovery.py`։ Scanner 2.0՝ արգելում է միայն RESTRICTED (credential/key/connection string/webhook code), բիզնես տեղեկատվությունը՝ awareness։
- Թեստեր՝ test_portability 14 (clean clone + կրկնակի bootstrap), release 301 test, 77 eval, maturity անփոփոխ։ Business fingerprint-ը այլևս mtime չի պարունակում (նույն core fingerprint ուրիշ մեքենայում)։
- Ուշադրություն՝ repo-ն PUBLIC է (Գև-ի որոշում)։ Push-ից հետո բիզնես փաստաթղթերը (աշխատավարձ, անուններ, չաթեր) հանրային են։ Private դարձնելը՝ միայն Գև-ի հաստատումով։

## 2026-09-12 · Mission 4.2 — Controlled Hands (Action Runtime, ինքնավարություն 0)
- Մեկ կանոնական Action Runtime (`.claude/skills/actions.py`, հմտություն `action_runtime`)՝ PREPARE → Գև-ի քարտ → բացահայտ հաստատում (մեկանգամյա տոկեն, fingerprint-ին կապված) → EXECUTE (lock, stale-state, audit-first) → անկախ VERIFY → REPORT։ Օրենքը մնաց `.claude/policy/approval_rule.json`-ում՝ անփոփոխ։
- Գրող adapter-ներ՝ Tasks.xlsx (create/update/assign/close/reopen/note, read-back-ով), Outlook calendar/mail (`outlook_write.ps1`, integrity-pinned; local draft ≠ provider draft ≠ send), Bitrix24 (POST allowlist, ազնիվ NOT_CONFIGURED), MikroBILL՝ WRITE NOT CERTIFIED / UNAVAILABLE։ Հնարավորությունների ռեեստր՝ `capabilities.py`։
- Engine՝ գրող intent-ները այլևս «անհասանելի գործիք» չեն, ուղղորդվում են action_runtime (63 հմտություն)։ Հաստատման/մերժման տեքստը՝ նույն հմտությանը («cancel X» = գործողություն, ոչ մերժում)։
- Դիմացկունություն՝ `actions` աղյուսակը durable export/import-ում (idempotency-ն restart-ից հետո), manifest 72 entry։
- ⚠ Միջադեպ (փակված)՝ test-ի առաջին վազքը իրական Tasks.xlsx-ում ստեղծել/փոփոխել էր «TEST — hands certification» տողը (adapter-ը լռելյայն կանոնական ռեեստրն էր վերցնում)։ Վերականգնվեց git-ից (15 առաջադրանք, TEST տող չկա); արմատային ուղղում՝ `register_path` պարամետր + env guard + sha ստուգում (թեստ/eval այլևս ֆիզիկապես չեն կարող դիպչել իրական ռեեստրին)։
- Live գրելու վկայագրում՝ սկզբում ՉԻ ԿԱՏԱՐՎԵԼ (READY FOR LIVE CERTIFICATION քարտ), հետո՝ տես հաջորդ գրառումը։

## 2026-09-12 · Mission 4.2 — առաջին live գրառում + հաստատող բառեր
- Գև-ի «GO»-ով (ticket 8297f25baf) կատարվեց ACT-ef5fb6b5d0՝ Tasks.xlsx-ում test տող id 16 (row 28) «TEST — Deputy live write certification (delete after)», պատասխանատու Գև։ VERIFIED երեք անկախ ընթերցումով (engine read-back, ինտեգրման շերտ count 15→16, հում sheet XML)։ INT-TASKS tasks.create → VERIFIED_WRITE (`write_certifications.json`)։
- Cleanup քարտ ACT-0854f55fe0 (task 16 → Արված)՝ պատրաստ, սպասում է հաստատման։ «օք»-ը runtime-ը ճանաչեց AMBIGUOUS՝ fail closed, ոչինչ չկատարվեց։
- Գև-ի խնդրանքով հաստատող բառերին ավելացվեցին հայատառ `այո` (արդեն կար), `օք`, `օկ`, `գո`, `գօ` (actions.py APPROVAL_RX + MODIFIED նախածանց, թեստերով)։ Runtime-ը այսուհետ ինքն է գրանցում VERIFIED_WRITE-ը, երբ գործողությունը նշված է `source_context.certification`-ով։

## 2026-09-12 · Tasks.xlsx = LIVE OPERATIONAL SOURCE — live data sync-ը անջատվեց product release-ից
- Արմատ՝ S09 (Tasks.xlsx) բիզնես-մոդելի բոլոր աղբյուրների պես CONTENT sha256-ով էր մտնում snapshot/core fingerprint → ամեն տողի փոփոխություն = SOURCE_CHANGED → STALE_MODEL → certification FAIL → release կանգ → rebuild → clean-clone fingerprint անհամապատասխանություն → checksums/commit/push միայն release-ով։
- Լուծում (policy 1.7.0, model 2026-09-12.1)՝ S09 `source_kind: LIVE_REGISTER`, `fingerprint_scope: STRUCTURE` (թերթ + header բլոկ), `live_integration: INT-TASKS`; certify-ի նոր check `live_registers_bound`; runtime-ը (business.model_state) նույն կանոնով։ Տողի փոփոխությունը core-ը չի փոխում, կառուցվածքինը՝ փոխում է։
- Drift դասակարգում (`tree_manifest.classify_drift`)՝ CLEAN · SYNC_REQUIRED · RELEASE_REQUIRED · UNCLASSIFIED (fail closed); LIVE DATA SYNC (`skill.py sync` → `runtime/data_sync.py`)՝ export durable state → ստատիկ մոդելը դեռ PASS (առանց rebuild) → checksums → commit միայն data ուղիները → push → origin ստուգում; product/model/unknown՝ մերժում։ Daily Brief-ը ցույց է տալիս sync վիճակը։
- Թեստեր՝ test_live_data (structure fingerprint, model binding temp workspace-ում, provenance/freshness, VERIFIED_WRITE և task 16 ապացույցներն անձեռնմխելի, drift, sync/refuse, gate, recovery), test_portability +1 (clone-ի ռեեստրը = committed, S09 STRUCTURE)։ Իրական Tasks.xlsx-ին թեստերը չեն դիպչում (sha guard)։

## 2026-09-12 · Mission 5 — Live Sales & Operations Intelligence
- Մեկ pipeline (`skills/intelligence.py`)՝ live reads (INT-TASKS, Outlook calendar/mail; B24/MikroBILL ազնիվ NOT_CONFIGURED) → provenance/freshness → current state → change detection (durable `checkpoints`) → exceptions (severity/urgency/impact/deadline/dependency) → cause discipline (CONFIRMED / SUPPORTED HYPOTHESIS / UNKNOWN) → impact → ACTION → OWNER → DEADLINE → VERIFY → Gev queue → management output; durable `loops` (հղումներ), ապացույցով փակվող։
- 4 նոր հմտություն (`management_snapshot`, `exception_review`, `change_review`, `decision_queue`, 67 ընդամենը), `daily_briefing`/`end_of_day_control`/`weekly_executive_review`/`open_loop_memory`-ը management բլոկով; Daily Brief hook-ը ցույց է տալիս TOP LINE / GEV / ACTIONS / Δ։ Բնական լեզվով routing (հայերեն + անգլերեն), գրող intent-ը դեռ միայն Action Runtime-ով։
- Sales framework (11 չափում) և ops framework (12 չափում)՝ live աղբյուր չկա → UNAVAILABLE / NOT CONNECTED + պակասող capability; fixture-ներով թեստավորված, production-ում թիվ չի հորինվում։
- Թեստեր՝ test_intelligence 19, evals +25 (routing 12 + management 13); store՝ `checkpoints`, `loops` աղյուսակներ durable export/import-ում; manifest 74 entry։
- Իրական production proof (read-only)՝ live Daily Brief՝ Tasks LIVE, Outlook calendar/mail LIVE, B24/MB NOT_CONFIGURED — տես Mission 5 զեկույցը։
