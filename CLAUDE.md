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

## CCN Voice Corpus

- **Path**: `/root/hermes-ccnow/voice-corpus/`
- 14 ministry transcripts embedded in ChromaDB; model: `nomic-embed-text` via Ollama
- Use for: social posts, emails, brand content written in Carlos's voice
- `embed.py` rebuilds `corpus.db` from the `raw_text/` folder
- **Never run `wayback_crawler.py`** — permanently disabled (domain hijacked)

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

## N.O.A.H. Vault

- **Path**: `/root/obsidian-vault/`
- **Inbox**: `/root/obsidian-vault/00-INBOX/` — always use this path, never `/Inbox/`
- `OBSIDIAN_VAULT_PATH=/root/obsidian-vault` is set in `/root/.hermes/.env`
- Vault syncs to Dell automatically via Syncthing — do not manually copy files

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

## Session Updates — May 25, 2026

**COMPLETED THIS SESSION:**
- Actual Budget UI live at localhost:5006 (SSH tunnel confirmed working)
- Windows Dell desktop shortcut created: ActualBudget.bat + .lnk
  - Opens tunnel to 5.78.214.131 + launches localhost:5006 automatically
- CCN Personal Budget Google Sheet updated with real amounts
- Vehicle marbete confirmed paid April 17, 2026 — $205 total
  - Annual registration $180 + inspection $20 + marbete sticker $5
  - Next due: April 2027. Budget $15/month in Vehicle Maintenance envelope
- Actual Budget envelope amounts set for May 2026 — $490.92/month total
  - GIVING: $40 | TRANSPORTATION: $65 | FOOD: $20
  - HEALTH: $67.87 | PERSONAL: $70 | BUSINESS/MINISTRY: $153.05
  - SAVINGS: $75 (Emergency $50 + El Pabellón $20 + Prayer Finance $5)
  - Section 8 covers rent + utilities | SNAP covers groceries
- Social media inventory complete — 11 platforms identified:
  Facebook, Instagram, YouTube, TikTok, Twitter/X, LinkedIn,
  Gab, Truth Social, Rumble, WhatsApp, Threads
  Phase 1 build order: YouTube (Google auth ready) → Meta (FB+IG+Threads+WA)
  Phase 2: Twitter/X, LinkedIn, TikTok
  Phase 3: Rumble, Gab, Truth Social (manual — no public API)

**STILL PENDING:**
- Actual Budget envelope amounts — paste Claude Code prompt to set via API
- Obsidian install on Dell + clone repo
- Omi webhook configuration in Omi app
- Fill actual dates in life-reality/obligations.json
- Verify DTOP lien removal by June 13
- FAFSA balance check at studentaid.gov
- Social media Phase 1 build (n8n install + YouTube + Meta APIs)
- Hetzner cleanup report review/approve

---

## CCN Social Hub — LIVE (May 25, 2026)

### System
- n8n v2.21.7 running on port 5678 (Docker, volume: n8n_data)
- Workflow: "CCN Substack to Meta — Phase 1" — ID: TDTkhQrQMncRcprD
- Schedule: Mon/Wed/Fri/Sun 9AM AST (cron: `0 13 * * 1,3,5,0` UTC)
- Source: danova.substack.com — fetches latest post (title, subtitle, slug, cover_image)
- n8n auth: hermes/ccnow2026 — Variables = paid plan only; tokens embedded directly in nodes

### Workflow — 8 Nodes (Current State)
1. **Schedule** — Mon/Wed/Fri/Sun 9AM AST
2. **Fetch Latest Substack Post** — GET danova.substack.com/api/v1/posts?limit=1
3. **Format CCN Post** — Code node; extracts title, subtitle, url, imageUrl (cover_image), message
4. **Post to Facebook Page (CCN)** — graph.facebook.com/v19.0/401214333070906/photos ✅
   - Confirmed live: `post_id=401214333070906_122228954492457468`
5. **Post to Tu Tienda Page** — graph.facebook.com/v19.0/520730761128283/photos ✅
   - Confirmed live: `post_id=520730761128283_122162304974731681`
6. **Post to Threads** — graph.threads.net/v1.0/26824946287114533/threads (TEXT type) ✅
   - Confirmed live: container `18105185252511772` published
7. **Publish to Threads** — graph.threads.net/v1.0/26824946287114533/threads_publish (two-step)
8. **Post to LinkedIn** — Execute Command → `node /opt/ccn/social-media/linkedin_post.js` ✅
   - Script: `/root/hermes-ccnow/social-media/linkedin_post.js` (volume-mounted :ro)
   - Uses LinkedIn Images API + Posts API (`/rest/posts`) with `LinkedIn-Version: 202507`
   - Confirmed live: `urn:li:share:7464781313322082306` with cover image thumbnail
   - Command expression: `={{ "CCN_PAYLOAD='" + JSON.stringify($json).replace(/'/g, "'\\''" ) + "' node /opt/ccn/social-media/linkedin_post.js" }}`
   - Pass all post data as single JSON env var — handles newlines in message safely
   - Author: urn:li:person:41q6-gkeGG (Carlos DaNova personal profile)

Fan-out: Format CCN Post → [CCN FB, Tu Tienda FB, Threads, LinkedIn] → Threads Publish

### Connections & Auth
- CCN Facebook Page ID: 401214333070906 — Token: META_CCN_PAGE_ACCESS_TOKEN (expires ~Oct 2026)
- Tu Tienda Page ID: 520730761128283 — Token: CCN_TUTIENDA_PAGE_ACCESS_TOKEN (expires ~Oct 2026)
- Threads User ID: 26824946287114533 — Token: CCN_THREADS_ACCESS_TOKEN (expires ~Jul 24, 2026)
- LinkedIn Member ID: 41q6-gkeGG — Token: LINKEDIN_ACCESS_TOKEN (expires ~Jul 24, 2026)
- All tokens embedded in workflow nodes (local VPS SQLite — not in .env variables)
- All secrets also backed up in /root/.hermes/.env (chattr +i protected)
- oauth.faaaith.org — HTTPS domain live, SSL cert expires Aug 23, 2026 (auto-renew)

### Token Refresh Reminder
- **July 20, 2026** — Refresh Meta long-lived tokens (page tokens expire ~July 24)
- **July 20, 2026** — Refresh Threads token (expires ~July 24)
- **July 20, 2026** — Refresh LinkedIn token (expires ~July 24)
- Meta process: exchange new short-lived user token via fb_exchange_token, re-fetch page tokens,
  update workflow nodes via n8n REST API PATCH /rest/workflows/TDTkhQrQMncRcprD
- LinkedIn process: new OAuth flow at oauth.faaaith.org (redirect URI already saved in app)

### ACTIVATE
Workflow is **Active**. Posts go out automatically Mon/Wed/Fri/Sun 9AM AST.
To manage: SSH tunnel `ssh -L 5678:localhost:5678 root@5.78.214.131` → localhost:5678

### Phase 2 (Not Yet Built)
- Instagram (needs separate content publishing setup + image URL per post)
- Twitter/X, TikTok
- Rumble, Gab, Truth Social (manual — no public API)

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
*"The blessing of the LORD, it maketh rich, and he addeth no sorrow with it." — Proverbs 10:22*
