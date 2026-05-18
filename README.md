# Hermes CC NOW! — Kingdom Operating System v1.0

> *"The blessing of the LORD, it maketh rich, and he addeth no sorrow with it."*
> — Proverbs 10:22

Autonomous business operating system for **Conscious Culture NOW! (CC NOW!)** — the economic discipleship ministry of Carlos "DaNova" Villanueva Cortés Jr., Mayagüez, Puerto Rico.

Built on a Hetzner VPS running [Hermes Agent](https://hermes-agent.nousresearch.com), powered by NVIDIA NIM (daily automation), Cerebras via OpenRouter (content generation), and Google Workspace APIs.

**North Star**: Purchase and restoration of El Pabellón de Victoria — an abandoned arena church in Hormigueros, Puerto Rico — as a kingdom arts and business platform for the west coast of Puerto Rico.

---

## What This System Does

Hermes runs the CC NOW! business autonomously so Carlos can focus on creative work and ministry:

- **9:00 AM AST daily** — reads the live Google Sheet product brain, checks 7 Drive asset inboxes, fetches live bank balances via Plaid, rotates promotional sequences for all 7 revenue streams, writes back status to the sheet, delivers a full Telegram summary to Carlos's iPhone
- **Every Sunday 8:00 PM AST** — delivers a 7-product performance report with revenue totals, Fulkrum Studios exit threshold tracking, accountability summary, and pattern analysis
- **On demand** — creates color-coded Google Calendar events that appear in Fantastical immediately, logs accountability check-ins, tracks Testing Season patterns

---

## The Three Pillars — Funny, Money, Honey

Everything in CC NOW! flows through three pillars that organize Carlos's life and business:

| Pillar | Emoji | Color in Fantastical | Focus |
|--------|-------|---------------------|-------|
| FUNNY | 😄 | Yellow/Gold | Rap artistry, golf, house music dancing, wine culture, joy |
| MONEY | 💰 | Green | CC NOW! products, sales, automation, millionaire mission |
| HONEY | 🍯 | Pink | Planet Fitness, pescatarian diet, relationships, wind-down |
| SPIRIT | 🙏 | Purple | Church, devotionals, ministry, The Gathering |
| HERMES | ⚙️ | Blue | Admin batch, Hermes building, delegation sessions |

---

## The 7 Revenue Streams

| # | Product | Platform | Status |
|---|---------|----------|--------|
| 01 | La Historia Del Niño (Book) | Amazon | URGENT — autonomous marketing |
| 02 | CC NOW! Merch (T-Shirt etc.) | Spreadshop | URGENT — autonomous marketing |
| 03 | La Historia Del Niño (Single) | DistroKid / Spotify | ACTIVE — streaming promotion |
| 04 | Monthly Virtual Rap Concert | TBD | URGENT — $25/ticket, recurring |
| 05 | La Fortaleza PR USA Magazine | Digital / Google Docs | ACTIVE — 14 issues published |
| 06 | THE 5:11 Digital Radio | Gumroad / Zeno Radio | BUILDING — RACE(2)10k campaign |
| 07 | YouTube Channel | YouTube | BUILDING — 1,000 subs target |

The **Google Sheet product brain** is the single source of truth. The **numbered Drive inbox folders** are the asset delivery system. Hermes reads both every morning.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CARLOS (iPhone)                           │
│         Telegram ← morning summary + Sunday review          │
│         Fantastical ← color-coded Google Calendar           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                HERMES (Hetzner VPS)                          │
│         Hermes Agent v0.14.0 + systemd gateway               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ DAILY CRON — 9:00 AM AST (13:00 UTC)                │    │
│  │ 1. Read Google Sheet product brain (26 columns)      │    │
│  │ 2. Check 7 Drive asset inbox folders for files       │    │
│  │ 3. Fetch live bank balances via Plaid MCP            │    │
│  │ 4. Rotate promotional sequences (15 msgs × 7 products)│   │
│  │ 5. Write back: Last Action + Next Target to sheet    │    │
│  │ 6. Deliver Telegram summary → Carlos's iPhone        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ SUNDAY CRON — 8:00 PM AST (00:00 UTC Mon)           │    │
│  │ 1. 7-product performance report from live sheet data │    │
│  │ 2. Fulkrum Studios exit threshold flag ($500/mo)     │    │
│  │ 3. Accountability pattern summary (Testing Season)   │    │
│  │ 4. Automation health check (cron log analysis)       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────────┐
│ Google Sheet │ │  Drive   │ │   Plaid MCP      │
│ Product Brain│ │  Inboxes │ │ Fifth Third +    │
│ (26 columns) │ │ (7 folders│ │ Banco Popular    │
└──────────────┘ └──────────┘ └──────────────────┘
```

### AI Routing — Cost Efficiency = Kingdom Stewardship

| Task | Model | Why |
|------|-------|-----|
| Daily automation, cron jobs, routine ops | NVIDIA NIM (nemotron-super) | Already integrated, cost-effective |
| Content generation, marketing copy, bulk tasks | Cerebras via OpenRouter | High-volume, low-cost |
| Architecture decisions only | Claude Pro | Expensive — reserved for complex decisions |

---

## File Structure & Deployment Map

```
hermes-ccnow/                          ← This repo
├── automation/
│   ├── scripts/
│   │   ├── daily_run.py              → /root/.hermes/scripts/daily_run.py
│   │   ├── sunday_review.py          → /root/.hermes/scripts/sunday_review.py
│   │   ├── hermes_calendar.py        → /root/Hetzner/CC_NOW/automation/scripts/
│   │   ├── get_balances.py           → /root/Hetzner/CC_NOW/automation/scripts/
│   │   └── record_accountability.py  → /root/Hetzner/CC_NOW/accountability/
│   └── promotions/
│       └── {product}/sequence.txt    → /root/Hetzner/CC_NOW/automation/promotions/
├── skills/
│   ├── cc_now_sales_automation/      → /root/.hermes/skills/mlops/cc_now_sales_automation/
│   └── cc_now_accountability/        → /root/.hermes/skills/mlops/cc_now_accountability/
├── accountability/
│   └── .gitkeep                      ← Directory tracked; logs excluded (private)
└── docs/
    └── system-architecture.md
```

---

## Environment Variables Required

Copy `.env.example` to `/root/.hermes/.env` and fill in all values. Never commit `.env`.

```
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=production
FIFTH_THIRD_ACCESS_TOKEN=
BANCO_POPULAR_ACCESS_TOKEN=
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
TELEGRAM_BOT_TOKEN=
```

Google auth is handled by `/root/.hermes/google_token.json` — never committed.

---

## Google System — Single Source of Truth Hierarchy

```
Google Sheet (product brain)   ← Carlos edits here
        ↓
Google Drive (asset inboxes)   ← Carlos drops files here
        ↓
VPS /root/Hetzner/CC_NOW/      ← Hermes reads and mirrors
        ↓
Telegram (daily summary)       ← Carlos receives here
```

**Never reverse this hierarchy.** Product names, URLs, and status always come from the live Sheet.

---

## Testing Season Protocol

This system is in **TESTING SEASON (Q2 2026)** — calibration, not perfection. Everything is data.

- Physical activities (Planet Fitness, golf, dancing) are tagged **TESTING** until verified with 4+ consecutive weeks of real attendance
- Hermes logs planned vs actual in `/root/Hetzner/CC_NOW/accountability/memory_log.csv`
- Items missed 3+ times in 14 days are flagged as "TESTING — physically unviable or misaligned"
- After sufficient data, Hermes redesigns the calendar to fit the real DaNova

### Hermes Opening Question (Every Session)
> "DaNova, before we move — what was PLANNED yesterday and what did you ACTUALLY do?
> Then tell me: what's the one MONEY move that must happen today?"

---

## Hermes Calendar — Fantastical Integration

```bash
# Create a single event
python3 hermes_calendar.py create \
  --pillar MONEY \
  --summary "Sales Outreach Block" \
  --date 2026-05-20 \
  --start 15:00 \
  --end 17:00 \
  --why "Every sales hour compounds toward the millionaire target." \
  --status CONFIRMED

# Seed a full week
python3 hermes_calendar.py seed-week --date 2026-05-19
```

Events appear in Fantastical immediately via Google Calendar sync. Color-coded by pillar.

---

## Accountability Logging

```bash
# Log a check-in entry
python3 record_accountability.py log \
  --planned "Planet Fitness 8:30 AM" \
  --actual "Did not go" \
  --pillar HONEY

# 7-day pattern report
python3 record_accountability.py report

# Flag repeatedly-missed items
python3 record_accountability.py flag-check
```

---

## Cron Jobs Active on VPS

| ID | Name | Schedule | Delivery |
|----|------|----------|---------|
| a10f101bb3e7 | CC NOW Sales Automation Daily | 0 13 * * * (9 AM AST) | Telegram |
| d29189e45128 | CC NOW Weekly Review — Sunday | 0 0 * * 0 (8 PM AST Sun) | Telegram |

---

## Mission

Every line of code in this repository serves one purpose:

**Hermes runs the business autonomously so Carlos can focus on creative work and ministry.**

Every dollar generated is a brick toward **El Pabellón de Victoria** in Hormigueros, Puerto Rico.

---

*Built with: Funny, Money, Honey | Conscious Culture NOW! | Phase 1 & 2 Complete — May 2026*
