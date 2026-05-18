#!/usr/bin/env python3
"""
CC NOW! Accountability Logger — Testing Season
Writes memory log entries in the standard format.
Called by Hermes after receiving Carlos's check-in answers.

Usage:
  python3 record_accountability.py \
    --planned "Planet Fitness 8:30 AM" \
    --actual "Did not go" \
    --pillar HONEY \
    --note "Gym attendance low in mornings"

  python3 record_accountability.py --report          # weekly pattern report
  python3 record_accountability.py --flag-check      # list repeatedly-missed items
"""
import os
import csv
import argparse
from datetime import datetime, timezone, date, timedelta
from collections import defaultdict

LOG_FILE = '/root/Hetzner/CC_NOW/accountability/memory_log.csv'
FIELDS   = ['date', 'planned', 'actual', 'gap_win', 'pillar', 'pattern_note', 'status']

# Items that get TESTING status by default (physical activities)
TESTING_KEYWORDS = [
    'planet fitness', 'gym', 'fitness', 'exercise', 'workout',
    'golf', 'dance', 'dancing', 'wine',
]

# Threshold: flag if missed N or more times in past 14 days
FLAG_THRESHOLD = 3


def ensure_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def infer_status(planned, actual):
    """TESTING if physical activity, CONFIRMED if executed, FLAG if repeatedly missed."""
    p_lower = planned.lower()
    if any(kw in p_lower for kw in TESTING_KEYWORDS):
        return 'TESTING'
    if actual.strip().lower() in ('', 'did not', 'no', 'skipped', 'missed'):
        return 'GAP'
    return 'WIN'


def infer_gap_win(planned, actual):
    a_lower = actual.lower()
    if any(w in a_lower for w in ['did not', 'skipped', 'missed', 'no ', 'nothing']):
        return 'GAP'
    if planned.lower().strip() == actual.lower().strip():
        return 'WIN'
    return 'GAP'  # partial is still a gap for pattern tracking


def write_entry(planned, actual, pillar, note='', status=None, today=None):
    ensure_log()
    today     = today or date.today().isoformat()
    gap_win   = infer_gap_win(planned, actual)
    if status is None:
        status = infer_status(planned, actual)
        if gap_win == 'WIN':
            status = 'CONFIRMED'

    row = {
        'date':         today,
        'planned':      planned,
        'actual':       actual,
        'gap_win':      gap_win,
        'pillar':       pillar.upper(),
        'pattern_note': note,
        'status':       status,
    }
    with open(LOG_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
    return row


def load_log(days_back=30):
    ensure_log()
    cutoff = date.today() - timedelta(days=days_back)
    rows   = []
    with open(LOG_FILE, 'r', newline='') as f:
        for row in csv.DictReader(f):
            try:
                if date.fromisoformat(row['date']) >= cutoff:
                    rows.append(row)
            except (ValueError, KeyError):
                pass
    return rows


def flag_check():
    """Return items missed FLAG_THRESHOLD+ times in last 14 days."""
    rows      = load_log(days_back=14)
    gap_count = defaultdict(int)
    for row in rows:
        if row.get('gap_win') == 'GAP':
            gap_count[row['planned'].strip()] += 1
    flagged = {item: count for item, count in gap_count.items() if count >= FLAG_THRESHOLD}
    return flagged


def weekly_report():
    rows = load_log(days_back=7)
    wins = [r for r in rows if r['gap_win'] == 'WIN']
    gaps = [r for r in rows if r['gap_win'] == 'GAP']

    flagged  = flag_check()
    by_pillar = defaultdict(lambda: {'wins': 0, 'gaps': 0})
    for r in rows:
        by_pillar[r['pillar']][r['gap_win'].lower() + 's'] += 1

    lines = [
        "CC NOW! ACCOUNTABILITY REPORT — 7 DAYS",
        f"Period: last 7 days | Entries: {len(rows)}",
        f"Wins: {len(wins)} | Gaps: {len(gaps)}",
        "",
        "BY PILLAR:",
    ]
    for pillar, counts in sorted(by_pillar.items()):
        lines.append(f"  {pillar}: {counts['wins']}W / {counts['gaps']}G")

    if flagged:
        lines += ["", "TESTING — PHYSICALLY UNVIABLE OR MISALIGNED:"]
        for item, count in sorted(flagged.items(), key=lambda x: -x[1]):
            lines.append(f"  [{count}x missed] {item}")

    if gaps:
        lines += ["", "RECENT GAPS:"]
        for r in gaps[-5:]:
            lines.append(f"  {r['date']} | {r['planned']} → {r['actual']} ({r['pillar']})")

    return "\n".join(lines)


def cmd_write(args):
    row = write_entry(
        planned = args.planned,
        actual  = args.actual,
        pillar  = args.pillar,
        note    = args.note or '',
        status  = args.status or None,
    )
    print(f"Logged: {row['date']} | {row['gap_win']} | {row['pillar']} | {row['status']}")


def cmd_report(args):
    print(weekly_report())


def cmd_flag(args):
    flagged = flag_check()
    if not flagged:
        print("No items flagged — everything executed within threshold.")
        return
    print("FLAGGED (missed 3+ times in 14 days):")
    for item, count in sorted(flagged.items(), key=lambda x: -x[1]):
        print(f"  [{count}x] {item} → TESTING — physically unviable or misaligned")


def main():
    parser = argparse.ArgumentParser(description='CC NOW! Accountability Logger')
    sub    = parser.add_subparsers(dest='cmd')

    p_write = sub.add_parser('log', help='Write an accountability entry')
    p_write.add_argument('--planned', required=True)
    p_write.add_argument('--actual',  required=True)
    p_write.add_argument('--pillar',  required=True,
                         choices=['FUNNY','MONEY','HONEY','SPIRIT','HERMES'])
    p_write.add_argument('--note',   default='')
    p_write.add_argument('--status', default=None,
                         choices=['TESTING','CONFIRMED','WIN','GAP','FLAG',None])
    p_write.set_defaults(func=cmd_write)

    p_report = sub.add_parser('report', help='7-day pattern report')
    p_report.set_defaults(func=cmd_report)

    p_flag = sub.add_parser('flag-check', help='List repeatedly-missed items')
    p_flag.set_defaults(func=cmd_flag)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    args.func(args)


if __name__ == '__main__':
    main()
