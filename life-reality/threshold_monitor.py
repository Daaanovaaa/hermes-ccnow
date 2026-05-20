#!/usr/bin/env python3
"""
Life Reality Layer — Threshold Monitor
Triggered when Carlos sends a message containing:
  URGENT, CRISIS, PROJECT LANDED, or THRESHOLD

Called by the Hermes agent (via terminal tool) when keyword is detected.
Logs the event to threshold_log.csv and prints a triage prompt.

Usage:
  python3 threshold_monitor.py --event "PROJECT LANDED: New client needs deliverable by Friday"
  python3 threshold_monitor.py --event "CRISIS: Car broke down, need $400"
  python3 threshold_monitor.py --list   # show recent threshold events
"""

import csv
import json
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

LIFE_DIR       = Path(__file__).parent
THRESHOLD_LOG  = LIFE_DIR / 'threshold_log.csv'
CONFIG_F       = LIFE_DIR / 'life_reality_config.json'

LOG_FIELDS = ['date', 'time_utc', 'trigger_word', 'event_description',
              'what_dropped', 'what_protected', 'what_rescheduled', 'resolved_date']

TRIAGE_QUESTIONS = [
    'What DROPPED from your schedule to make room for this?',
    'What is NON-NEGOTIABLE and must stay protected (RAP WORK, church, sleep)?',
    'What can be RESCHEDULED to later this week or next week?',
    'Is there a financial component? If yes, what is the dollar impact?',
    'What is the ONE action that must happen in the next 2 hours?',
]

KEYWORD_PROTOCOLS = {
    'URGENT': {
        'label': 'URGENT FLAG',
        'tone': 'Something needs attention now. Let\'s triage clearly and move fast.',
        'follow_up': 'What is the hard deadline and who else is involved?',
    },
    'CRISIS': {
        'label': 'CRISIS MODE',
        'tone': 'You are in a crisis. Stay calm. One step at a time.',
        'follow_up': 'Is this a safety issue, financial emergency, or relationship crisis? That determines the first move.',
    },
    'PROJECT LANDED': {
        'label': 'NEW PROJECT',
        'tone': 'A new project arrived. This is opportunity — and it needs a plan that does not break everything else.',
        'follow_up': 'What is the scope, the deadline, and what does it pay?',
    },
    'THRESHOLD': {
        'label': 'THRESHOLD EVENT',
        'tone': 'Something significant crossed the threshold. Let\'s look at the full picture.',
        'follow_up': 'Is this a positive threshold (revenue milestone, breakthrough) or a pressure threshold (capacity limit, burnout signal)?',
    },
}


def detect_keyword(event_text):
    """Return the matched keyword from the event description."""
    upper = event_text.upper()
    for kw in KEYWORD_PROTOCOLS:
        if kw in upper:
            return kw
    return 'THRESHOLD'  # default


def ensure_log():
    if not THRESHOLD_LOG.exists():
        with open(THRESHOLD_LOG, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=LOG_FIELDS).writeheader()


def log_event(event_text, trigger_word):
    ensure_log()
    now = datetime.now(timezone.utc)
    row = {
        'date':              now.strftime('%Y-%m-%d'),
        'time_utc':          now.strftime('%H:%M'),
        'trigger_word':      trigger_word,
        'event_description': event_text,
        'what_dropped':      '',
        'what_protected':    '',
        'what_rescheduled':  '',
        'resolved_date':     '',
    }
    with open(THRESHOLD_LOG, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=LOG_FIELDS).writerow(row)
    return row


def format_triage(event_text, trigger_word, row):
    protocol = KEYWORD_PROTOCOLS.get(trigger_word, KEYWORD_PROTOCOLS['THRESHOLD'])
    now_str  = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    lines = [
        f'THRESHOLD MONITOR — {protocol["label"]}',
        f'Triggered: {now_str}',
        f'Event: {event_text}',
        '─' * 40,
        '',
        protocol['tone'],
        '',
        'TRIAGE — answer these in order:',
    ]
    for i, q in enumerate(TRIAGE_QUESTIONS, 1):
        lines.append(f'  {i}. {q}')

    lines += [
        '',
        f'KEY QUESTION: {protocol["follow_up"]}',
        '',
        '─' * 40,
        f'Event logged to threshold_log.csv (entry {row["date"]} {row["time_utc"]})',
        'Reply with your triage answers and Hermes will help you restructure.',
        '',
        'Your North Star does not move. El Pabellón de Victoria is still the destination.',
        'Crises are detours, not dead ends.',
    ]
    return '\n'.join(lines)


def cmd_event(event_text):
    trigger  = detect_keyword(event_text)
    row      = log_event(event_text, trigger)
    triage   = format_triage(event_text, trigger, row)
    print(triage)


def cmd_list():
    if not THRESHOLD_LOG.exists():
        print('No threshold events logged yet.')
        return

    rows = []
    try:
        with open(THRESHOLD_LOG, newline='') as f:
            rows = list(csv.DictReader(f))
    except Exception as e:
        print(f'Error reading log: {e}')
        return

    if not rows:
        print('No threshold events logged yet.')
        return

    # Show last 30 days
    cutoff = date.today() - timedelta(days=30)
    recent = []
    for row in rows:
        try:
            if date.fromisoformat(row['date']) >= cutoff:
                recent.append(row)
        except (ValueError, KeyError):
            pass

    lines = [f'THRESHOLD EVENTS — last 30 days ({len(recent)} events)', '─' * 40]
    for row in recent[-20:]:  # show up to 20 most recent
        resolved = f' [resolved {row["resolved_date"]}]' if row.get('resolved_date') else ''
        lines.append(
            f'{row["date"]} {row["time_utc"]} | {row["trigger_word"]:15s} | '
            f'{row["event_description"][:60]}{resolved}'
        )
    print('\n'.join(lines))


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    if '--list' in args:
        cmd_list()
        return

    if '--event' in args:
        idx = args.index('--event')
        if idx + 1 >= len(args):
            print('Error: --event requires a description string')
            sys.exit(1)
        event_text = args[idx + 1]
        cmd_event(event_text)
        return

    # Positional arg fallback: treat everything as the event text
    event_text = ' '.join(args)
    cmd_event(event_text)


if __name__ == '__main__':
    main()
