# Life Reality Layer — CC NOW! Kingdom OS

> "The blessing of the LORD, it maketh rich, and he addeth no sorrow with it." — Proverbs 10:22

This layer sits on top of the existing CC NOW! automation and handles the ground-level realities that make sustainable kingdom business possible: government deadlines, daily rhythm tracking, pattern learning, and crisis triage.

**It does not replace the business OS. It protects the human running it.**

---

## What This Layer Does

| Module | File | When It Runs | What It Delivers |
|--------|------|-------------|-----------------|
| Obligations Tracker | `obligations_tracker.py` | Daily 8:45 AM AST | Telegram alert when gov't deadlines approach (30/14/7/1 days) |
| Reality Check-In | `reality_checkin.py` | 4× daily | Structured check-in question to Telegram (fixed from broken local delivery) |
| Adaptive Learner | `adaptive_learner.py` | Sundays 7 AM AST | Weekly pattern report + schedule suggestions after 4 weeks |
| Threshold Monitor | `threshold_monitor.py` | On-demand / keyword trigger | Triage prompt when URGENT/CRISIS/PROJECT LANDED/THRESHOLD detected |

---

## Directory Structure

```
life-reality/
├── life_reality_config.json          ← Personal context, schedule, config
├── obligations.json                  ← Government/civic deadlines (YOU update dates here)
├── checkin_log.csv                   ← Auto-created: log of all check-ins sent + responses
├── threshold_log.csv                 ← Auto-created: log of all crisis/urgent events
├── obligations_tracker.py            ← Deadline alert system
├── reality_checkin.py                ← Daily check-in script (4 cron jobs)
├── adaptive_learner.py               ← Weekly pattern analysis
├── threshold_monitor.py              ← Crisis/urgent triage tool
├── skills/
│   └── life_reality_threshold/
│       └── SKILL.md                  ← Hermes skill: detects URGENT/CRISIS in messages
└── README.md                         ← This file
```

---

## The 6 Active Cron Jobs

```
ID             Name                        Schedule           Delivers To
────────────── ─────────────────────────── ────────────────── ──────────
a7d8b530f9c2  morning-reality-checkin     Daily 05:00 UTC    Telegram ✅
df3bab3a3a16  afternoon-reality-checkin   Daily 12:00 UTC    Telegram ✅
b8e24093c66b  evening-reality-checkin     Daily 18:00 UTC    Telegram ✅
6f3ce34d61f5  night-reality-checkin       Daily 22:00 UTC    Telegram ✅
54de247e214c  life-reality-obligations    Daily 12:45 UTC    Telegram ✅
2d85b156d9e1  life-reality-weekly-adaptive Sundays 11:00 UTC Telegram ✅
```

The first 4 were broken (delivering locally instead of to Telegram). All 4 are now fixed.

---

## How to Update Obligation Dates

When you receive a renewal notice for any of these:

1. Open `obligations.json`
2. Find the obligation by `id`
3. Update the `due_date` field: `"due_date": "2026-12-07"`
4. Save the file

The tracker will automatically send Telegram alerts at **30 days, 14 days, 7 days, and 1 day** before the deadline. It only alerts once per threshold per day — no spam.

**The 5 tracked obligations:**
- `section8_recertification` — Section 8 annual recertification (housing)
- `snap_recertification` — SNAP / Food Stamps recertification
- `medicare_open_enrollment` — Medicare open enrollment (Oct 15 – Dec 7 annually, pre-set to Dec 7)
- `vehicle_registration` — Vehicle registration (marbete) renewal
- `vehicle_insurance` — Vehicle insurance renewal

If the date field contains `YYYY-MM-DD` (the placeholder), the tracker skips that obligation safely.

---

## How the Reality Check-Ins Work

Four cron jobs fire daily — each sends a structured question to your Telegram:

| Cron time | AST equivalent | Asks about |
|-----------|---------------|------------|
| 05:00 UTC | 1:00 AM AST | Night block / are you starting your morning? |
| 12:00 UTC | 8:00 AM AST | Morning block completion (RAP WORK, gym/devotional) |
| 18:00 UTC | 2:00 PM AST | Afternoon block completion (CC NOW! work, admin, sales) |
| 22:00 UTC | 6:00 PM AST | Evening block completion (learning, ministry, wind-down) |

**Reply format:** YES / PARTIAL / NO + what interrupted you if not YES.

To log your response (so Hermes can record it to the CSV), tell Hermes:
> "Log morning checkin: PARTIAL — got interrupted by [reason]"

Or Hermes can call the script directly:
```bash
python3 reality_checkin.py --record morning partial "unexpected call from family"
```

**Log file:** `checkin_log.csv`
Columns: `date, time_utc, block, scheduled_tasks, status, completed, interruption_reason, notes`

---

## How to Trigger Threshold Mode

Send Hermes any message containing one of these words:
- **URGENT** — something needs attention immediately
- **CRISIS** — emergency situation
- **PROJECT LANDED** — new unexpected project or commitment
- **THRESHOLD** — something significant crossed a limit

Hermes will detect the keyword and run the threshold triage automatically.

**What happens:**
1. Hermes logs the event to `threshold_log.csv`
2. Hermes sends you 5 triage questions (what dropped, what's protected, what can shift)
3. You answer → Hermes helps restructure your schedule
4. Non-negotiables are always called out: RAP WORK, church, sleep

**You can also trigger manually:**
```bash
python3 threshold_monitor.py --event "URGENT: describe what happened"
python3 threshold_monitor.py --list    # see recent threshold events
```

**Non-negotiable protected blocks (never dropped in a crisis):**
- 5:30–8:30 AM RAP WORK (FUNNY pillar — creative output)
- Tuesday 3–6 PM: The Gathering Church rehearsal
- Sunday 8 AM–1 PM: The Gathering Church service
- Minimum 6 hours sleep

---

## Weekly Adaptive Report — Sundays 7 AM AST

Every Sunday before your weekly review, Hermes sends a Life Reality report covering:
1. Check-in coverage (how many of the 28 weekly check-ins generated responses)
2. Completion rate per time block (morning/afternoon/evening/night)
3. Top interruption patterns (what keeps coming up)
4. Cross-reference with accountability log (existing system)
5. After **4 weeks of data**: schedule adjustment suggestions

**The standard never moves.** The adaptive learner adjusts TIMING and SEQUENCING — not whether the work happens.

---

## Financial Emergency Protocol

`life_reality_config.json` stores:
```json
"emergency_threshold_dollars": 50,
"emergency_protocol": "Any unplanned expense over $50: send Telegram alert, triage before spending."
```

If you're facing an unexpected expense, trigger threshold mode:
> "CRISIS: [description of expense and amount]"

Hermes will cross-reference your bank balance via Plaid and help identify the fastest CC NOW! revenue action to offset it.

---

## Personal Context Reference

All personal context is stored in `life_reality_config.json`:
- Housing: Section 8
- Food: SNAP / Food Stamps
- Health: Medicare
- Transport: Vehicle owned
- Financial context: Post-bankruptcy, building from zero
- Emergency margin: Low — flag unplanned expenses immediately
- Location: Puerto Rico west coast (Mayagüez / Hormigueros)

This context informs how Hermes frames advice — no generic responses, no assumptions of financial buffer.

---

## The Mission

Every check-in logged, every deadline caught, every crisis triaged is infrastructure for the long game.

**El Pabellón de Victoria in Hormigueros is the destination. This layer makes sure nothing on the ground derails the journey.**

---

*Built May 2026 | Non-destructive addition to Hermes CC NOW! Kingdom OS*
*Co-authored by Claude Sonnet 4.6*
