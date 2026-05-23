#!/usr/bin/env python3
"""
Journal Generator — Sunday 10 AM AST (14:00 UTC)
Generates weekly Prayer Finance journal entry and sends via Telegram.

Usage:
  python3 journal_generator.py
"""
import json, subprocess, sys
from datetime import date
from pathlib import Path

FINANCE_DIR = Path(__file__).parent
LOG_FILE    = FINANCE_DIR / 'prayer_finance_log.json'
CACHE_FILE  = FINANCE_DIR / 'ipo_cache.json'
JOURNALS    = FINANCE_DIR / 'journals'

PRAYER_VERSE = (
    'Mark 4:26-29 — "So is the kingdom of GOD, as if a man should cast seed '
    'into the ground; And should sleep, and rise night and day, and the seed '
    'should spring and grow up, he knoweth not how."'
)

DECLARATION = (
    'Father, we present this week\'s financial seed as an act of worship and covenant obedience.\n'
    'We declare that every dollar planted in Your name multiplies according to Kingdom law.\n'
    'We bind every spirit of financial destruction and loose abundance over this investment.\n'
    'In the name of JESUS. Amen.'
)


def load_json(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def generate(log: dict, cache: dict, today: date) -> tuple[str, str]:
    entries     = log.get('entries', [])
    total_seeds = log.get('total_seeds_planted', 0)
    total_inv   = log.get('total_invested', 0.0)
    last_entry  = entries[-1] if entries else None

    candidates = cache.get('candidates', [])
    if candidates:
        top       = candidates[0]
        ticker    = top.get('ticker', 'N/A')
        company   = top.get('company', 'N/A')
        rationale = top.get('rationale', 'Kingdom alignment')
        ipo_date  = top.get('ipo_date', 'TBD')
        price_rng = top.get('price_range', 'N/A')
    else:
        ticker = company = rationale = ipo_date = price_rng = 'N/A'

    if last_entry:
        last_line = (
            f"Latest seed: **{last_entry['ticker']}** | "
            f"Conf: {last_entry.get('confirmation_number', 'pending')} | "
            f"${last_entry.get('amount', 1.00):.2f} on {last_entry['date']}"
        )
    else:
        last_line = 'No seeds planted yet — first seed coming soon.'

    md = f"""# Prayer Finance Journal — {today.isoformat()}

## This Week's IPO
**Ticker:** {ticker}
**Company:** {company}
**IPO Date:** {ipo_date}
**Price Range:** {price_rng}
**Rationale:** {rationale}

## Scripture Connection
{PRAYER_VERSE}

The seed principle: you do not understand exactly how a seed grows after you plant it.
But you plant it in faith, and GOD gives the increase in His timing.

## Prayer Declaration
{DECLARATION}

## Running Total
- Seeds planted: **{total_seeds}**
- Total invested: **${total_inv:.2f}**
- {last_line}

## Notes

"""

    tg_msg = (
        f'PRAYER FINANCE WEEKLY JOURNAL — {today.isoformat()}\n\n'
        f'This week: {ticker} — {company}\n'
        f'Seeds planted: {total_seeds} | Total invested: ${total_inv:.2f}\n\n'
        f'{PRAYER_VERSE}\n\n'
        f'Journal saved: journals/{today.isoformat()}_journal.md'
    )

    return md, tg_msg


def run():
    today = date.today()
    log   = load_json(LOG_FILE)
    cache = load_json(CACHE_FILE)

    JOURNALS.mkdir(exist_ok=True)
    fname = JOURNALS / f'{today.isoformat()}_journal.md'

    md, tg_msg = generate(log, cache, today)
    fname.write_text(md)
    print(f'Journal written: {fname}')

    # Send via hermes send (preferred)
    result = subprocess.run(
        ['hermes', 'send', '--to', 'telegram', tg_msg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print('Journal sent to Telegram via hermes.')
    else:
        # Fallback: direct bot API
        print(f'hermes send failed, trying direct API...', file=sys.stderr)
        from telegram_handler import send_message
        if send_message(tg_msg):
            print('Journal sent via direct Telegram API.')
        else:
            print('Telegram send failed. Journal saved locally only.', file=sys.stderr)


if __name__ == '__main__':
    run()
