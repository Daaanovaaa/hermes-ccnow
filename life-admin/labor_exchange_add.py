#!/usr/bin/env python3
"""
Life Admin Layer — Landlord Labor Exchange Log
Adds entries to labor_exchange.json and prints confirmation to Telegram.

Called by Hermes agent when Carlos sends a message like:
  "Log labor: painted kitchen, 3 hours, $150, Section8_inspection"
  "Log labor: landlord fixed roof drain, 2 hours, $200, general"

Usage:
  python3 labor_exchange_add.py --add \
    --date 2026-05-20 \
    --who Carlos \
    --description "Painted kitchen walls" \
    --hours 3.0 \
    --value 150.00 \
    --related Section8_inspection \
    --notes "Inspector noted walls needed fresh paint"

  python3 labor_exchange_add.py --list       # show last 10 entries
  python3 labor_exchange_add.py --summary    # show totals

Who values: Carlos | Landlord
Related values: Section8_inspection | general
"""

import json
import sys
from datetime import date
from pathlib import Path

ADMIN_DIR  = Path(__file__).parent
LOG_FILE   = ADMIN_DIR / 'labor_exchange.json'


def load_log():
    with open(LOG_FILE) as f:
        return json.load(f)


def save_log(data):
    data['last_updated'] = date.today().isoformat()
    # Recompute summary
    entries = data.get('entries', [])
    data['summary'] = {
        'total_entries':          len(entries),
        'total_hours_carlos':     round(sum(e['estimated_hours'] for e in entries
                                            if e['who_performed'] == 'Carlos'), 2),
        'total_hours_landlord':   round(sum(e['estimated_hours'] for e in entries
                                            if e['who_performed'] == 'Landlord'), 2),
        'total_value_usd':        round(sum(e['estimated_value_usd'] for e in entries), 2),
        'section8_related_entries': sum(1 for e in entries
                                        if e['related_to'] == 'Section8_inspection'),
    }
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def cmd_add(args):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date',        default=date.today().isoformat())
    parser.add_argument('--who',         required=True,
                        choices=['Carlos', 'Landlord'])
    parser.add_argument('--description', required=True)
    parser.add_argument('--hours',       type=float, required=True)
    parser.add_argument('--value',       type=float, required=True)
    parser.add_argument('--related',     default='general',
                        choices=['Section8_inspection', 'general'])
    parser.add_argument('--notes',       default='')
    parsed = parser.parse_args(args)

    data = load_log()
    entry = {
        'date':               parsed.date,
        'who_performed':      parsed.who,
        'description':        parsed.description,
        'estimated_hours':    parsed.hours,
        'estimated_value_usd': parsed.value,
        'related_to':         parsed.related,
        'notes':              parsed.notes,
    }
    data['entries'].append(entry)
    save_log(data)

    summary = data['summary']
    related_tag = ' [Section 8 inspection]' if parsed.related == 'Section8_inspection' else ''
    print(
        f'Labor logged{related_tag}\n'
        f'Date:  {parsed.date}\n'
        f'Who:   {parsed.who}\n'
        f'Work:  {parsed.description}\n'
        f'Hours: {parsed.hours} | Value: ${parsed.value:.2f}\n'
        f'\n'
        f'Running totals:\n'
        f'  Carlos: {summary["total_hours_carlos"]}h | '
        f'Landlord: {summary["total_hours_landlord"]}h | '
        f'Total value: ${summary["total_value_usd"]:.2f}\n'
        f'  Section 8 related entries: {summary["section8_related_entries"]}'
    )


def cmd_list():
    data    = load_log()
    entries = data.get('entries', [])
    if not entries:
        print('No labor entries logged yet.')
        return
    lines = [f'LABOR EXCHANGE LOG — last {min(10, len(entries))} entries', '─' * 40]
    for e in entries[-10:]:
        tag = ' [S8]' if e['related_to'] == 'Section8_inspection' else ''
        lines.append(
            f"{e['date']} | {e['who_performed']:8s} | "
            f"{e['estimated_hours']}h ${e['estimated_value_usd']:.0f}{tag} | "
            f"{e['description'][:45]}"
        )
    s = data['summary']
    lines += [
        '─' * 40,
        f"Totals: Carlos {s['total_hours_carlos']}h | "
        f"Landlord {s['total_hours_landlord']}h | "
        f"${s['total_value_usd']:.2f} total | "
        f"{s['section8_related_entries']} Section 8 entries",
    ]
    print('\n'.join(lines))


def cmd_summary():
    data = load_log()
    s    = data['summary']
    print(
        f'LABOR EXCHANGE SUMMARY\n'
        f'Total entries:        {s["total_entries"]}\n'
        f'Carlos hours:         {s["total_hours_carlos"]}\n'
        f'Landlord hours:       {s["total_hours_landlord"]}\n'
        f'Total value:          ${s["total_value_usd"]:.2f}\n'
        f'Section 8 entries:    {s["section8_related_entries"]}\n'
        f'Last updated:         {data["last_updated"]}'
    )


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if '--add' in args:
        idx = args.index('--add')
        cmd_add(args[idx + 1:])
    elif '--list' in args:
        cmd_list()
    elif '--summary' in args:
        cmd_summary()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
