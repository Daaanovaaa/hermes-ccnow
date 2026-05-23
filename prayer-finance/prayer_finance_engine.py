#!/usr/bin/env python3
"""
Prayer Finance Engine — Weekly IPO Research & $1 Fractional Seed Investment
Kingdom Investment Strategy: Mark 4:26-29

Schedule:
  Friday  22:00 UTC (6 PM AST)  — research + shortlist generation
  Friday  23:00 UTC (7 PM AST)  — Telegram shortlist alert
  Saturday 12:00 UTC (8 AM AST) — Telegram PW-ID + recommendation
  Sunday  14:00 UTC (10 AM AST) — journal entry + weekly summary

Usage:
  python3 prayer_finance_engine.py --research      # Fri 22:00
  python3 prayer_finance_engine.py --shortlist     # Fri 23:00
  python3 prayer_finance_engine.py --recommend     # Sat 12:00
  python3 prayer_finance_engine.py --journal       # Sun 14:00
  python3 prayer_finance_engine.py --confirm TICKER CONF_NUMBER
"""

import csv, json, subprocess, sys
from datetime import date
from pathlib import Path

FINANCE_DIR = Path(__file__).parent
LOG_FILE    = FINANCE_DIR / 'prayer_finance_log.json'
CSV_FILE    = FINANCE_DIR / 'prayer_finance_log.csv'
CONFIG_FILE = FINANCE_DIR / 'prayer_finance_config.json'
CACHE_FILE  = FINANCE_DIR / 'ipo_cache.json'
JOURNALS    = FINANCE_DIR / 'journals'

PRAYER_VERSE = (
    'Mark 4:26-29 — "So is the kingdom of GOD, as if a man should cast seed '
    'into the ground; And should sleep, and rise night and day, and the seed '
    'should spring and grow up, he knoweth not how."'
)

SCORE_LABELS = [
    (8.0, 'STRONG SEED'),
    (6.0, 'GOOD SEED'),
    (4.0, 'WATCH'),
    (0.0, 'PASS'),
]


# ── Persistence ────────────────────────────────────────────────────────────────

def load_log() -> dict:
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {'total_seeds_planted': 0, 'total_invested': 0.00, 'entries': []}


def save_log(data: dict):
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {'candidates': [], 'research_date': '', 'window': ''}


def append_csv(entry: dict):
    write_header = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['date', 'pw_id', 'ticker', 'amount',
                        'confirmation_number', 'journal_entry']
        )
        if write_header:
            writer.writeheader()
        writer.writerow({
            'date':                entry.get('date', ''),
            'pw_id':               entry.get('pw_id', ''),
            'ticker':              entry.get('ticker', ''),
            'amount':              entry.get('amount', 1.00),
            'confirmation_number': entry.get('confirmation_number', ''),
            'journal_entry':       entry.get('journal_entry', ''),
        })


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_ipo(c: dict) -> float:
    return (c.get('stability_score', 5)  * 0.25
            + c.get('mission_score', 5)  * 0.25
            + (10 if c.get('fractional_eligible') else 3) * 0.20
            + c.get('momentum_score', 5) * 0.30)


def get_score_label(score: float) -> str:
    for threshold, label in SCORE_LABELS:
        if score >= threshold:
            return label
    return 'PASS'


# ── Telegram ───────────────────────────────────────────────────────────────────

def send_telegram(msg: str):
    """Send via hermes send; fallback to telegram_handler direct API."""
    result = subprocess.run(
        ['hermes', 'send', '--to', 'telegram', msg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return
    # Fallback
    try:
        sys.path.insert(0, str(FINANCE_DIR))
        from telegram_handler import send_message
        send_message(msg)
    except Exception as e:
        print(f'Telegram fallback error: {e}', file=sys.stderr)


# ── Message formatters ─────────────────────────────────────────────────────────

def format_shortlist(candidates: list, research_date: str) -> str:
    if not candidates:
        return (
            f'PRAYER FINANCE SHORTLIST — {research_date}\n\n'
            f'No IPO candidates found this week under $20 on Fidelity.\n'
            f'Consider holding this week\'s $1 seed for next Friday.\n'
            f'Praying for divine guidance on timing.\n\n'
            f'{PRAYER_VERSE}'
        )
    lines = [
        f'PRAYER FINANCE SHORTLIST — {research_date}',
        f'This week\'s top IPO candidates:',
        '',
    ]
    for i, c in enumerate(candidates[:3], 1):
        score = score_ipo(c)
        label = get_score_label(score)
        lines.append(
            f'{i}. {c.get("ticker","?")} — {c.get("company","?")} '
            f'| Score: {score:.0f}/10 [{label}]'
        )
        lines.append(
            f'   {c.get("ipo_date","?")} | {c.get("price_range","?")} '
            f'| {c.get("sector","?")}'
        )
    lines += [
        '',
        'Review and pray over these. Saturday 8 AM I send the final recommendation.',
        '',
        PRAYER_VERSE,
    ]
    return '\n'.join(lines)


def format_recommendation(top: dict) -> str:
    from pw_id_generator import generate_pw_id, format_saturday_message
    ticker    = top.get('ticker', 'TBD')
    company   = top.get('company', 'TBD')
    price_rng = top.get('price_range', 'TBD')
    ipo_date  = top.get('ipo_date', 'TBD')
    reason    = top.get('rationale', 'Strong fundamentals and Kingdom mission alignment.')
    pw_id     = generate_pw_id(ticker)

    return format_saturday_message(ticker, company, price_rng, ipo_date, reason, pw_id)


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_research():
    """Friday 22:00 — Run IPO researcher, save cache."""
    print('Running IPO research...')
    result = subprocess.run(
        ['python3', str(FINANCE_DIR / 'ipo_researcher.py')],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f'Research error: {result.stderr}', file=sys.stderr)
    else:
        cache = load_cache()
        count = cache.get('candidate_count', 0)
        window = cache.get('window', '')
        print(f'Research complete. {count} candidates in {window}')
        print('Telegram shortlist alert fires at 23:00 UTC.')


def cmd_shortlist():
    """Friday 23:00 — Send shortlist to Telegram."""
    cache = load_cache()
    candidates = cache.get('candidates', [])
    today = date.today().isoformat()
    msg = format_shortlist(candidates, today)
    print(msg)
    send_telegram(msg)


def cmd_recommend():
    """Saturday 12:00 — Send PW-ID + recommendation to Telegram."""
    sys.path.insert(0, str(FINANCE_DIR))
    cache = load_cache()
    candidates = cache.get('candidates', [])

    if not candidates:
        msg = (
            f'PRAYER FINANCE — No recommendation this week.\n'
            f'No qualifying IPOs under $20 found. Holding $1 seed.\n'
            f'Check back next Friday.\n\n'
            f'{PRAYER_VERSE}'
        )
        print(msg)
        send_telegram(msg)
        return

    top = max(candidates, key=score_ipo)
    msg = format_recommendation(top)
    print(msg)
    send_telegram(msg)


def cmd_journal():
    """Sunday 14:00 — Generate journal and send via Telegram."""
    result = subprocess.run(
        ['python3', str(FINANCE_DIR / 'journal_generator.py')],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)


def cmd_confirm(ticker: str, conf_number: str):
    """Log Carlos's Fidelity confirmation."""
    sys.path.insert(0, str(FINANCE_DIR))
    from pw_id_generator import generate_pw_id

    log_data = load_log()
    config   = load_config()
    today    = date.today().isoformat()
    pw_id    = generate_pw_id(ticker)
    amount   = config['weekly_budget']

    entry = {
        'date':                today,
        'ticker':              ticker.upper(),
        'pw_id':               pw_id,
        'confirmation_number': conf_number.upper(),
        'amount':              amount,
        'status':              'EXECUTED',
        'platform':            config['platform'],
        'journal_entry':       '',
    }
    log_data['entries'].append(entry)
    log_data['total_seeds_planted'] += 1
    log_data['total_invested'] = round(log_data['total_invested'] + amount, 2)
    save_log(log_data)
    append_csv(entry)

    print(
        f'Logged. {pw_id}\n'
        f'Seeds planted: {log_data["total_seeds_planted"]}\n'
        f'Total invested: ${log_data["total_invested"]:.2f}\n'
        f'Praying over this seed.\n'
        f'{PRAYER_VERSE}'
    )


# ── Main ───────────────────────────────────────────────────────────────────────

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
