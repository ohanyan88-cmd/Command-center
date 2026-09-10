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
