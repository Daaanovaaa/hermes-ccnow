# CLAUDE.md — Hermes CC NOW! Agent Briefing

> Read this entire file before touching anything.
> Then run: `git log --oneline -20`
> Then check: `/root/hermes-ccnow/simulation/modules/` for existing sim wrappers.

---

## What Is This System

**Hermes** is the autonomous Kingdom Operating System for **Conscious Culture NOW! (CC NOW!)** —
the economic discipleship ministry of Pastor Carlos "DaNova" Villanueva Cortés, based in
Mayagüez, Puerto Rico.

**North Star**: Purchase and restoration of El Pabellón de Victoria — an abandoned arena church
in Hormigueros, Puerto Rico — as a kingdom arts and business platform.

**One-line mission**: Hermes runs the business autonomously so Carlos can focus on creative work
and ministry.

This repo is **intentionally public**. No secrets, no passwords in code. All credentials live
in `.env` (never committed). Transparency is a ministry value.

---

## Agent Rules — Read Before Every Session

1. **Never touch `/root/hermes-ccnow/` live data during simulation runs.**
   Always set `HERMES_HOME=/root/hermes-sim/` for any test execution.

2. **Never commit `.env`, `*_token.json`, or any file in `accountability/`.**
   These are in `.gitignore` — keep them there.

3. **Never reverse the data hierarchy.**
   Google Sheet → Drive → VPS → Telegram. Always flows this direction.

4. **When adding a new module**, create the `.sim.py` wrapper in
   `simulation/modules/` in the same session. Not later.

5. **Cost routing is a ministry value** — don't use Claude/expensive models
   for tasks that NVIDIA NIM or Cerebras can handle.

6. **Check `SOUL.md`** (in `/root/.hermes/`) for ministry values that govern
   design decisions before making architectural choices.

7. **Commit message format**: `add:`, `fix:`, `update:`, `sim:` prefixes.

---

## Directory Map

```
hermes-ccnow/
├── CLAUDE.md                          ← You are here
├── README.md                          ← Full system overview
│
├── automation/scripts/                ← Core daily/weekly cron scripts
│   ├── daily_run.py                   → Runs 9:00 AM AST daily
│   ├── sunday_review.py               → Runs 8:00 PM AST Sunday
│   ├── hermes_calendar.py             → Fantastical/Google Calendar
│   ├── get_balances.py                → Plaid bank balance fetch
│   └── record_accountability.py       → Testing Season log
│
├── budget/
│   └── plaid_actual_sync.py           → Plaid → Actual Budget sync
│
├── crm/
│   └── crm_engine.py                  → 7,000+ contact CRM engine
│
├── departments/                       ← Org knowledge base (13 dept files)
│   ├── CCN_DEPARTMENT_INDEX.md        → Master department index
│   ├── EXECUTIVE_DEPT_knowledge.md
│   ├── ACCOUNTING_DEPT_knowledge.md
│   └── ... (11 more dept files)
│
├── life-admin/                        ← Personal legal/financial/admin layer
│   ├── budget_monitor.py              → 9:15 AM AST daily Telegram alert
│   ├── correspondence_tracker.py      → Gmail keyword alerts every 2h
│   ├── doc_vault_monitor.py           → leeegaaal Drive doc watcher
│   ├── case_log_updater.py            → Auto-updates case markdown files
│   ├── labor_exchange_add.py          → Landlord labor log via Telegram
│   └── cases/                         ← 13 active life case files
│       ├── MASTER_CASE_INDEX.md       → Start here for life-admin cases
│       ├── legal_bankruptcy_chapter7.md
│       ├── benefits_section8_recertification.md
│       ├── benefits_SNAP_PAN_recertification.md
│       ├── vehicle_JVL660_marbete_license.md
│       └── ... (9 more active cases)
│
├── life-reality/                      ← Obligations + adaptive learning layer
│   ├── reality_checkin.py             → 4x daily Telegram check-ins
│   ├── obligations_tracker.py         → Section 8, SNAP, Medicare, vehicle
│   ├── threshold_monitor.py           → URGENT/CRISIS keyword watcher
│   ├── adaptive_learner.py            → Sunday 7:00 AM AST pattern learning
│   └── obligations.json               → Fill actual renewal dates (TBD pending)
│
├── prayer-finance/                    ← Prayer Finance Protection System
│   ├── prayer_finance_engine.py       → Main orchestrator
│   ├── ipo_researcher.py              → Friday 6:00 PM IPO research
│   ├── pw_id_generator.py             → PW-ID + recommendation generator
│   ├── telegram_handler.py            → Friday 7pm + Saturday 8am sends
│   ├── journal_generator.py           → Sunday 10:00 AM journal entry
│   ├── prayer_finance_log.json        → Purchase confirmation log
│   └── .claude/settings.local.json   ← Claude Code local permissions (scoped)
│
├── race2-10k/                         ← RACE(2)10k subscriber campaign
│   ├── race2_10k_tracker.py           → Subscriber tracking
│   └── race2_content_calendar.md      → Content schedule
│
├── omi-integration/                   ← Omi wearable voice webhook
│   ├── omi_router.py                  → Routes Omi transcripts
│   └── omi_config.json                → Webhook config (setup pending)
│
├── obsidian-vault/                    ← Knowledge base synced to Obsidian
│   ├── 00-Dashboard/HOME.md           → Master dashboard
│   ├── 03-Finance/                    → Budget + prayer finance logs
│   ├── 07-Business/                   → CRM + RACE2 progress
│   ├── 08-Omi-Transcripts/            → Voice note transcripts
│   └── 09-Prayer-Journal/             → Prayer finance status
│
├── skills/                            ← Hermes skill definitions
│   ├── cc_now_sales_automation/       → Sales automation skill
│   └── cc_now_accountability/         → Accountability skill
│
├── simulation/                        ← Simulation framework (IN PROGRESS)
│   ├── sim_runner.py                  → Plugin engine (build session TBD)
│   ├── sim_config.json                → Timeframe + settings
│   ├── SIMULATION.md                  → How to add modules + run sims
│   └── modules/                       → One .sim.py per Hermes module
│
└── docs/
    └── hetzner_cleanup_report.md      → VPS cleanup log (pending review)
```

---

## Environment Variables

All secrets live in `/root/.hermes/.env` — never in this repo.

Key names (no values):
```
PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV
FIFTH_THIRD_ACCESS_TOKEN, BANCO_POPULAR_ACCESS_TOKEN
NVIDIA_API_KEY, OPENROUTER_API_KEY
TELEGRAM_BOT_TOKEN
```

Google auth: `/root/.hermes/google_token.json` — never committed.
Two Google accounts:
- `dominalo.con.cristo@gmail.com` — business/ministry (default)
- `leeegaaal@gmail.com` — legal/personal (profile: leeegaaal)

---

## Active Cron Jobs

| Schedule | Script | Delivery |
|----------|--------|----------|
| 9:00 AM AST daily | `daily_run.py` | Telegram |
| 9:15 AM AST daily | `budget_monitor.py` | Telegram |
| Every 2h | `correspondence_tracker.py` | Telegram (keyword alerts) |
| Friday 6:00 PM AST | `ipo_researcher.py` | Internal |
| Friday 7:00 PM AST | `telegram_handler.py` | Telegram (IPO shortlist) |
| Saturday 8:00 AM AST | `telegram_handler.py` | Telegram (PW-ID + rec) |
| Sunday 7:00 AM AST | `adaptive_learner.py` | Internal |
| Sunday 8:00 PM AST | `sunday_review.py` | Telegram |
| Sunday 10:00 AM AST | `journal_generator.py` | Obsidian vault |

---

## AI Model Routing

| Task | Model | Reason |
|------|-------|--------|
| Daily crons, routine ops | NVIDIA NIM (nemotron-super) | Cost-effective |
| Content, marketing, bulk | Cerebras via OpenRouter | High-volume, low-cost |
| Architecture decisions | Claude Pro | Reserved — expensive |

---

## Current Build Status (as of May 23, 2026)

**COMPLETE:**
- Daily automation pipeline
- Sunday review
- Life-Reality layer (reality_checkin, obligations_tracker, threshold_monitor, adaptive_learner)
- Life-Admin layer (budget_monitor, correspondence_tracker, doc_vault_monitor, 13 active cases)
- Prayer Finance Protection System
- RACE(2)10k tracker
- Obsidian vault sync
- GitHub MCP (26 tools)
- Plaid MCP
- Simulation framework (sim_runner.py + 4 modules — 285/285 scenarios, 30-day run clean)

**IN PROGRESS / PENDING:**
- Omi webhook configuration in Omi app
- Fill actual dates in `life-reality/obligations.json`
- Fill TBD budget amounts in CCN Personal Budget Google Sheet (before June 1)
- Actual Budget first-time setup via SSH tunnel
- Obsidian install on Dell + clone repo
- Review/approve `docs/hetzner_cleanup_report.md`
- Verify DTOP lien removal by June 13
- FAFSA balance check at studentaid.gov

---

## Simulation Framework — How To Add A New Module

When you build a new Hermes module, create `simulation/modules/[module_name].sim.py`
in the same session. Every sim wrapper answers three questions:

```python
INTENT = "What was this module built to do?"
SCHEDULE = "daily | weekly | monthly | on-trigger"
SCENARIOS = [
    {"name": "normal", "data": {...}},
    {"name": "edge_case", "data": {...}},
    {"name": "crisis", "data": {...}},
]
```

`sim_runner.py` auto-detects all files in `modules/`. No other registration needed.
Use `HERMES_HOME=/root/hermes-sim/` for all simulation runs.

---

## The Three Pillars

| Pillar | Emoji | Focus |
|--------|-------|-------|
| FUNNY | 😄 | Rap artistry, golf, house music, joy |
| MONEY | 💰 | CC NOW! products, sales, automation |
| HONEY | 🍯 | Planet Fitness, diet, relationships |
| SPIRIT | 🙏 | Church, ministry, The Gathering |
| HERMES | ⚙️ | Admin, building, delegation |

---

*Hermes CC NOW! — Kingdom OS | Conscious Culture NOW! | Puerto Rico*
*"The blessing of the LORD, it maketh rich, and he addeth no sorrow with it." — Proverbs 10:22*git add CLAUDE.md
git commit -m "add: CLAUDE.md agent briefing with full system map"
git push
