#!/usr/bin/env python3
"""
Life Reality Layer — Reality Check-In
Called by the 4 daily activity-check cron jobs (now fixed to deliver to Telegram).

Each cron fires at a UTC hour that maps to the START of a review window:
  05 UTC (1 AM AST)  → morning cron   → reviews night block
  12 UTC (8 AM AST)  → afternoon cron → reviews morning block + sets afternoon intention
  18 UTC (2 PM AST)  → evening cron   → reviews afternoon block
  22 UTC (6 PM AST)  → night cron     → reviews evening block

Usage (as no-agent cron script — stdout delivered to Telegram):
  python3 reality_checkin.py

Usage (record Carlos's response from agent context):
  python3 reality_checkin.py --record BLOCK COMPLETED [REASON] [NOTES]
  Completed: yes | partial | no
  Example: python3 reality_checkin.py --record morning yes "" "Rap session was fire"
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LIFE_DIR  = Path(__file__).parent
LOG_FILE  = LIFE_DIR / 'checkin_log.csv'
CONFIG_F  = LIFE_DIR / 'life_reality_config.json'

LOG_FIELDS = ['date', 'time_utc', 'block', 'scheduled_tasks', 'status',
              'completed', 'interruption_reason', 'notes']

# Maps UTC hour → which block we're reviewing and what was planned
# Each check-in asks about the block that just concluded or is underway
BLOCK_MAP = {
    5:  {
        'block': 'morning',
        'label': 'MORNING BLOCK (5AM–12PM AST)',
        'review': 'night / overnight',
        'ask_about': [
            'Did you get to sleep at a reasonable hour?',
            'Are you up and starting your morning routine?',
            'Rap work block (5:30–8:30 AM) — is it protected?',
        ],
        'scheduled': [
            '05:00–05:30 HONEY — Wake, coffee, high-protein breakfast',
            '05:30–08:30 FUNNY — RAP WORK (airplane mode)',
            '08:30–09:30 HONEY/SPIRIT — Planet Fitness (TESTING) or Devotional',
        ],
    },
    12: {
        'block': 'afternoon',
        'label': 'AFTERNOON BLOCK (12PM–6PM AST)',
        'review': 'morning block',
        'ask_about': [
            'Did you complete your RAP WORK block (5:30–8:30)?',
            'Did you make it to Planet Fitness or do your devotional?',
            'What is the ONE MONEY move that must happen this afternoon?',
        ],
        'scheduled': [
            '10:00–12:00 MONEY — CC NOW! Deep Work',
            '12:00–12:30 HONEY — Pescatarian Lunch',
            '13:00–15:00 HERMES — Admin Batch (delegation window)',
            '15:00–17:00 MONEY — Sales, marketing, outreach',
        ],
    },
    18: {
        'block': 'evening',
        'label': 'EVENING BLOCK (6PM–10PM AST)',
        'review': 'afternoon block',
        'ask_about': [
            'Did you complete your CC NOW! Deep Work block (10AM–12PM)?',
            'Did the Admin Batch happen (1–3 PM)?',
            'Did sales/outreach actions get done (3–5 PM)?',
        ],
        'scheduled': [
            '17:00–19:00 MONEY — Learning / Ministry / La Fortaleza PR',
            '21:00–21:30 HERMES — Next-Day Prep + Hermes debrief',
            '21:30–22:00 HONEY — Honey Time / Wind-down',
        ],
    },
    22: {
        'block': 'night',
        'label': 'NIGHT BLOCK (10PM–5AM AST)',
        'review': 'evening block',
        'ask_about': [
            'Did you get through your learning / ministry block (5–7 PM)?',
            'Did next-day prep happen (9–9:30 PM)?',
            'Are you winding down or do you have a post-midnight creative session planned?',
        ],
        'scheduled': [
            'Wind-down / sleep',
            'Post-midnight creative (FUNNY pillar — if energy permits)',
        ],
    },
}


def ensure_log():
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=LOG_FIELDS).writeheader()


def log_entry(block, scheduled, status='sent', completed='', reason='', notes=''):
    ensure_log()
    now = datetime.now(timezone.utc)
    row = {
        'date':                now.strftime('%Y-%m-%d'),
        'time_utc':            now.strftime('%H:%M'),
        'block':               block,
        'scheduled_tasks':     ' | '.join(scheduled),
        'status':              status,
        'completed':           completed,
        'interruption_reason': reason,
        'notes':               notes,
    }
    with open(LOG_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=LOG_FIELDS).writerow(row)
    return row


def get_block_for_hour(utc_hour):
    """Return the block config for the current UTC hour."""
    return BLOCK_MAP.get(utc_hour)


def format_check_in(block_cfg, today_str):
    lines = [
        f'REALITY CHECK-IN — {block_cfg["label"]}',
        f'Date: {today_str} | Reviewing: {block_cfg["review"]}',
        '─' * 38,
        '',
        'Your SCHEDULED tasks for this block:',
    ]
    for task in block_cfg['scheduled']:
        lines.append(f'  • {task}')

    lines += [
        '',
        'THREE QUESTIONS:',
    ]
    for i, q in enumerate(block_cfg['ask_about'], 1):
        lines.append(f'  {i}. {q}')

    lines += [
        '',
        'Reply format: YES / PARTIAL / NO',
        'If PARTIAL or NO — what interrupted you?',
        '',
        '─' * 38,
        'This is data, not judgment. Every answer builds the real picture.',
    ]
    return '\n'.join(lines)


def cmd_checkin():
    """Generate and log a check-in for the current UTC hour."""
    now      = datetime.now(timezone.utc)
    utc_hour = now.hour
    today    = now.strftime('%Y-%m-%d')

    block_cfg = get_block_for_hour(utc_hour)
    if not block_cfg:
        # No check-in mapped to this hour — shouldn't happen in normal cron use
        print('[SILENT]')
        return

    # Log the "asked" event
    log_entry(
        block     = block_cfg['block'],
        scheduled = block_cfg['scheduled'],
        status    = 'sent',
    )

    print(format_check_in(block_cfg, today))


def cmd_record(args):
    """
    Record Carlos's response to a check-in.
    Called by agent after Carlos responds on Telegram.
    Args: block completed [reason] [notes]
    """
    if len(args) < 2:
        print('Usage: reality_checkin.py --record BLOCK COMPLETED [REASON] [NOTES]')
        print('Completed: yes | partial | no')
        sys.exit(1)

    block     = args[0].lower()
    completed = args[1].lower()
    reason    = args[2] if len(args) > 2 else ''
    notes     = args[3] if len(args) > 3 else ''

    if block not in BLOCK_MAP.values().__class__:
        # Validate by checking block name against all configs
        valid_blocks = [v['block'] for v in BLOCK_MAP.values()]
        if block not in valid_blocks:
            block = block  # accept it anyway — don't fail on typos

    if completed not in ('yes', 'partial', 'no'):
        completed = completed  # accept freeform

    block_cfg = next((v for v in BLOCK_MAP.values() if v['block'] == block), None)
    scheduled = block_cfg['scheduled'] if block_cfg else []

    row = log_entry(
        block     = block,
        scheduled = scheduled,
        status    = 'recorded',
        completed = completed,
        reason    = reason,
        notes     = notes,
    )

    verdict = {'yes': 'WIN', 'partial': 'PARTIAL', 'no': 'GAP'}.get(completed, completed.upper())
    print(f'Logged: {row["date"]} | {block} | {verdict}')
    if reason:
        print(f'Interruption: {reason}')
    if completed in ('partial', 'no') and not reason:
        print('Note: consider logging what interrupted you — it becomes the pattern.')


def main():
    if '--record' in sys.argv:
        idx = sys.argv.index('--record')
        cmd_record(sys.argv[idx + 1:])
    else:
        cmd_checkin()


if __name__ == '__main__':
    main()
