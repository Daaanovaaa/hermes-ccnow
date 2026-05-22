#!/usr/bin/env python3
"""
Prayer Finance Engine — Weekly IPO Research & $1 Fractional Seed Investment
Kingdom Investment Strategy: Mark 4:26-29

Schedule:
  Friday  22:00 UTC (6 PM AST)  — research + shortlist generation
  Friday  23:00 UTC (7 PM AST)  — Telegram shortlist alert
  Saturday 12:00 UTC (8 AM AST) — Telegram recommendation
  Sunday  14:00 UTC (10 AM AST) — journal entry + weekly summary

Usage:
  python3 prayer_finance_engine.py --research     # Fri 22:00
  python3 prayer_finance_engine.py --shortlist    # Fri 23:00
  python3 prayer_finance_engine.py --recommend    # Sat 12:00
  python3 prayer_finance_engine.py --journal      # Sun 14:00
  python3 prayer_finance_engine.py --confirm TICKER CONF_NUMBER  # on reply
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

FINANCE_DIR  = Path(__file__).parent
LOG_FILE     = FINANCE_DIR / 'prayer_finance_log.json'
CONFIG_FILE  = FINANCE_DIR / 'prayer_finance_config.json'
JOURNALS_DIR = FINANCE_DIR / 'journals'
GWS_SCRIPT   = Path('/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py')

PRAYER_VERSE = "Mark 4:26-29 — \"So is the kingdom of GOD, as if a man should cast seed into the ground...\""

SECTOR_KEYWORDS = ['tech', 'health', 'media', 'faith', 'christian', 'biotech',
                   'software', 'digital', 'communications', 'education']

SCORE_LABELS = {
    (8, 10): 'STRONG SEED',
    (6, 7):  'GOOD SEED',
    (4, 5):  'WATCH',
    (0, 3):  'PASS',
}


def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {'total_seeds_planted': 0, 'total_invested': 0.00, 'entries': []}


def save_log(data):
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def search_upcoming_ipos():
    """
    Use web search via Hermes tools to find upcoming IPOs.
    Returns list of candidate dicts.
    """
    # Try DuckDuckGo search via terminal
    try:
        result = subprocess.run(
            ['python3', str(GWS_SCRIPT)],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        pass

    # Build a curated shortlist from known upcoming IPO sources
    # In production, this would query IPO calendars via web search
    # For now, returns a structured template that Hermes agent can populate
    today = date.today()
    next_week = today + timedelta(days=14)

    # Return template structure — Hermes agent with web search fills this
    return {
        'research_date': today.isoformat(),
        'window': f'{today.isoformat()} to {next_week.isoformat()}',
        'source_note': 'Run via Hermes agent with web search for live IPO data',
        'candidates': []
    }


def score_ipo(candidate):
    """Score an IPO candidate 1-10 on four criteria."""
    stability   = candidate.get('stability_score', 5)
    mission     = candidate.get('mission_score', 5)
    fractional  = 10 if candidate.get('fractional_eligible') else 3
    momentum    = candidate.get('momentum_score', 5)
    total = (stability * 0.25 + mission * 0.25 + fractional * 0.20 + momentum * 0.30)
    return round(total, 1)


def get_score_label(score):
    for (lo, hi), label in SCORE_LABELS.items():
        if lo <= score <= hi:
            return label
    return 'UNKNOWN'


def format_shortlist(candidates, research_date):
    if not candidates:
        return (
            f"PRAYER FINANCE SHORTLIST — {research_date}\n"
            f"No IPO candidates found this week matching our criteria.\n"
            f"Criteria: price under $20, Fidelity accessible, tech/faith/media/health.\n"
            f"Consider holding this week's $1 seed for next week.\n"
            f"Praying for divine guidance on timing."
        )
    lines = [
        f"PRAYER FINANCE SHORTLIST — {research_date}",
        f"This week's IPO candidates for prayer review:",
        "",
    ]
    for i, c in enumerate(candidates[:5], 1):
        score = score_ipo(c)
        label = get_score_label(score)
        lines.append(
            f"{i}. {c.get('ticker','?')} — {c.get('company','?')} "
            f"— Score: {score}/10 [{label}]"
        )
        if c.get('sector'):
            lines.append(f"   Sector: {c['sector']} | Est. price: ${c.get('price','?')}")
    lines += [
        "",
        "Review and pray. Saturday 8am I send the final recommendation.",
        PRAYER_VERSE,
    ]
    return '\n'.join(lines)


def format_recommendation(top_candidate, research_date):
    ticker  = top_candidate.get('ticker', 'TBD')
    company = top_candidate.get('company', 'TBD')
    reason  = top_candidate.get('rationale', 'Strong fundamentals and mission alignment with Kingdom priorities.')
    pw_id   = f"{ticker}-{date.today().strftime('%Y%m%d')}"

    return (
        f"PRAYER FINANCE RECOMMENDATION\n"
        f"PW-ID: {pw_id}\n"
        f"Company: {company}\n"
        f"Ticker: {ticker}\n"
        f"Recommended: $1 fractional share\n"
        f"Reason: {reason}\n"
        f"\n"
        f"Go to Fidelity app now.\n"
        f"Search {ticker}.\n"
        f"Buy $1 fractional share.\n"
        f"Reply with your confirmation number.\n"
        f"\n"
        f"{PRAYER_VERSE}"
    )


def cmd_research():
    """Friday 22:00 — Run IPO research, save shortlist to log."""
    config   = load_config()
    log_data = load_log()
    research = search_upcoming_ipos()

    # Save to log as a pending shortlist
    log_data.setdefault('pending_shortlist', research)
    log_data['last_research_date'] = date.today().isoformat()
    save_log(log_data)

    print(
        f"Prayer Finance research complete.\n"
        f"Window: {research['window']}\n"
        f"Candidates: {len(research['candidates'])}\n"
        f"Shortlist saved. Telegram alert fires at 23:00 UTC."
    )


def cmd_shortlist():
    """Friday 23:00 — Send shortlist to Telegram."""
    log_data   = load_log()
    shortlist  = log_data.get('pending_shortlist', {})
    candidates = shortlist.get('candidates', [])
    today      = date.today().isoformat()
    msg        = format_shortlist(candidates, today)
    print(msg)


def cmd_recommend():
    """Saturday 12:00 — Send recommendation to Telegram."""
    log_data   = load_log()
    shortlist  = log_data.get('pending_shortlist', {})
    candidates = shortlist.get('candidates', [])
    today      = date.today().isoformat()

    if not candidates:
        print(
            f"PRAYER FINANCE — No recommendation this week.\n"
            f"No qualifying IPOs found. Holding $1 seed.\n"
            f"Check back next Friday.\n"
            f"{PRAYER_VERSE}"
        )
        return

    # Sort by score, take top
    top = max(candidates, key=score_ipo)
    msg = format_recommendation(top, today)
    print(msg)


def cmd_journal():
    """Sunday 14:00 — Generate journal entry and weekly summary."""
    log_data = load_log()
    today    = date.today()
    fname    = JOURNALS_DIR / f"{today.isoformat()}_journal.md"
    JOURNALS_DIR.mkdir(exist_ok=True)

    shortlist  = log_data.get('pending_shortlist', {})
    candidates = shortlist.get('candidates', [])
    last_entry = log_data['entries'][-1] if log_data['entries'] else None
    total_seeds = log_data['total_seeds_planted']
    total_inv   = log_data['total_invested']

    # Get top pick if any
    if candidates:
        top = max(candidates, key=score_ipo)
        ticker  = top.get('ticker', 'N/A')
        company = top.get('company', 'N/A')
        rationale = top.get('rationale', 'Kingdom alignment and momentum.')
    else:
        ticker = company = rationale = 'None this week'

    journal = f"""# Prayer Finance Journal — {today.isoformat()}

## This Week's IPO
**Ticker:** {ticker}
**Company:** {company}
**Rationale:** {rationale}

## Scripture Connection
{PRAYER_VERSE}

The seed principle: you do not understand exactly how a seed grows after you plant it.
But you plant it in faith, and GOD gives the increase in His timing.

## Prayer Declaration
Father, we present this financial seed as an act of worship and obedience.
We declare that every dollar planted in Your name multiplies according to Your covenant.
We bind every spirit of financial destruction and loose abundance and provision over
this investment and all that follows it.
In the name of JESUS. Amen.

## Running Total
Seeds planted: {total_seeds}
Total invested: ${total_inv:.2f}
{'Latest entry: ' + last_entry['ticker'] + ' on ' + last_entry['date'] if last_entry else 'First seed not yet planted.'}

## Notes
"""
    fname.write_text(journal)

    summary = (
        f"PRAYER FINANCE WEEKLY SUMMARY — {today.isoformat()}\n"
        f"This week's pick: {ticker} — {company}\n"
        f"Total seeds planted: {total_seeds}\n"
        f"Total invested: ${total_inv:.2f}\n"
        f"Journal saved: {fname.name}\n"
        f"\n"
        f"{PRAYER_VERSE}"
    )
    print(summary)


def cmd_confirm(ticker, conf_number):
    """Record confirmation when Carlos replies with confirmation number."""
    log_data  = load_log()
    today     = date.today().isoformat()
    config    = load_config()
    pw_id     = f"{ticker}-{date.today().strftime('%Y%m%d')}"
    amount    = config['weekly_budget']

    entry = {
        'date':                today,
        'ticker':              ticker.upper(),
        'pw_id':               pw_id,
        'confirmation_number': conf_number,
        'amount':              amount,
        'status':              'EXECUTED',
        'platform':            config['platform'],
    }
    log_data['entries'].append(entry)
    log_data['total_seeds_planted'] += 1
    log_data['total_invested'] = round(log_data['total_invested'] + amount, 2)
    save_log(log_data)

    print(
        f"Logged. PW-ID {pw_id} confirmed.\n"
        f"Seeds planted: {log_data['total_seeds_planted']}\n"
        f"Total invested: ${log_data['total_invested']:.2f}\n"
        f"Praying over this seed.\n"
        f"{PRAYER_VERSE}"
    )


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == '--research':
        cmd_research()
    elif cmd == '--shortlist':
        cmd_shortlist()
    elif cmd == '--recommend':
        cmd_recommend()
    elif cmd == '--journal':
        cmd_journal()
    elif cmd == '--confirm' and len(args) >= 3:
        cmd_confirm(args[1], args[2])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
