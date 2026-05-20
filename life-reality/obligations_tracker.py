#!/usr/bin/env python3
"""
Life Reality Layer — Obligations Tracker
Checks government/civic deadlines and sends Telegram alerts at 30/14/7/1 days out.
Runs daily at 8:45 AM AST (12:45 UTC) via Hermes cron.

Output goes to stdout — Hermes cron delivers it to Telegram.
Prints [SILENT] if nothing is due within 30 days (suppresses delivery).
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

LIFE_DIR      = Path(__file__).parent
OBLIGATIONS_F = LIFE_DIR / 'obligations.json'
CONFIG_F      = LIFE_DIR / 'life_reality_config.json'
ALERT_DAYS    = [30, 14, 7, 1]
DATE_SENTINEL = 'YYYY-MM-DD'   # placeholder — skipped safely


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def days_until(due_str):
    """Return days until due_date, or None if date is unknown/invalid."""
    if not due_str or due_str == DATE_SENTINEL or 'YYYY' in due_str:
        return None
    try:
        due = date.fromisoformat(due_str)
        delta = (due - date.today()).days
        return delta
    except ValueError:
        return None


def urgency_emoji(days):
    if days <= 1:
        return '🚨'
    if days <= 7:
        return '⚠️'
    if days <= 14:
        return '📅'
    return 'ℹ️'


def build_alert(obl, days):
    emoji = urgency_emoji(days)
    if days < 0:
        timing = f"OVERDUE by {abs(days)} day{'s' if abs(days) != 1 else ''}"
    elif days == 0:
        timing = "DUE TODAY"
    elif days == 1:
        timing = "DUE TOMORROW"
    else:
        timing = f"due in {days} days ({obl['due_date']})"

    lines = [
        f"{emoji} {obl['name'].upper()}",
        f"Category: {obl['category'].replace('_', ' ').title()}",
        f"Status: {timing}",
    ]
    if obl.get('what_to_bring'):
        lines.append(f"Bring: {obl['what_to_bring']}")
    if obl.get('contact'):
        lines.append(f"Contact: {obl['contact']}")
    if obl.get('notes'):
        lines.append(f"Note: {obl['notes']}")
    return '\n'.join(lines)


def check_obligations(dry_run=False):
    """
    Check all obligations against today's date.
    Returns (alerts_to_send: list[str], upcoming_summary: list[str]).
    Also updates alert_sent tracking in obligations.json.
    """
    if not OBLIGATIONS_F.exists():
        return [], []

    data   = load_json(OBLIGATIONS_F)
    today  = date.today().isoformat()
    alerts = []
    upcoming = []
    changed  = False

    for obl in data.get('obligations', []):
        days = days_until(obl.get('due_date'))
        if days is None:
            continue  # skip unknown dates

        # Build upcoming summary (anything within 30 days)
        if -1 <= days <= 30:
            if days < 0:
                upcoming.append(f"OVERDUE {abs(days)}d: {obl['name']}")
            elif days == 0:
                upcoming.append(f"DUE TODAY: {obl['name']}")
            else:
                upcoming.append(f"In {days}d: {obl['name']} ({obl['due_date']})")

        # Check if we should send an alert for this threshold
        for threshold in ALERT_DAYS:
            if days == threshold or (days < 0 and days >= threshold - 1):
                key = str(threshold)
                already_sent = obl.get('alert_sent', {}).get(key)
                if already_sent == today:
                    continue  # already sent today for this threshold
                alerts.append(build_alert(obl, days))
                if not dry_run:
                    if 'alert_sent' not in obl:
                        obl['alert_sent'] = {}
                    obl['alert_sent'][key] = today
                    changed = True
                break  # one alert per obligation per day

    if changed and not dry_run:
        data['last_updated'] = today
        save_json(OBLIGATIONS_F, data)

    return alerts, upcoming


def morning_briefing_snippet():
    """
    Returns a compact obligations summary for injection into morning briefing.
    Returns empty string if nothing is due within 30 days.
    """
    _, upcoming = check_obligations(dry_run=True)
    if not upcoming:
        return ''
    lines = ['OBLIGATIONS DUE WITHIN 30 DAYS:']
    lines += [f'  • {item}' for item in upcoming]
    return '\n'.join(lines)


def main():
    alerts, upcoming = check_obligations()

    if not alerts and not upcoming:
        # Nothing due within 30 days — suppress Telegram delivery
        print('[SILENT]')
        return

    lines = ['LIFE REALITY — OBLIGATIONS ALERT']
    lines.append(f'Date: {date.today().isoformat()}')
    lines.append('─' * 36)

    if alerts:
        lines.append('')
        lines.append('ACTION REQUIRED:')
        for alert in alerts:
            lines.append('')
            lines.append(alert)

    if upcoming and not alerts:
        lines.append('')
        lines.append('UPCOMING (within 30 days):')
        for item in upcoming:
            lines.append(f'  • {item}')

    lines += [
        '',
        '─' * 36,
        'Update obligations.json with the exact date when you receive a notice.',
        'Every deadline managed is a wall protecting your stability.',
    ]

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
