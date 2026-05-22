#!/usr/bin/env python3
"""
RACE(2)10k Weekly Substack Growth Tracker
Runs every Monday at 9 AM AST (13:00 UTC).

Since Substack does not have a public API, this script:
1. Reads the manually-updated subscriber count from a config file
2. Calculates week-over-week growth and projections
3. Sends Telegram weekly report

To update subscriber count: edit race2_10k_config.json
Set: "current_subscribers": [number]
Also set: "last_week_subscribers": [previous number]

Usage:
  python3 race2_10k_tracker.py              # run weekly report
  python3 race2_10k_tracker.py --update 125 # update subscriber count
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'race2_10k_config.json'


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def project_10k_date(current, weekly_growth, goal=10000):
    if weekly_growth <= 0:
        return 'N/A (no growth this week)'
    weeks_needed = (goal - current) / weekly_growth
    target = date.today() + timedelta(weeks=weeks_needed)
    return target.strftime('%B %d, %Y')


def main():
    args = sys.argv[1:]

    config = load_config()
    goal   = config.get('goal', 10000)

    # Handle --update command
    if '--update' in args:
        idx = args.index('--update')
        if idx + 1 < len(args):
            new_count = int(args[idx + 1])
            config['last_week_subscribers'] = config.get('current_subscribers', 0)
            config['current_subscribers']   = new_count
            config['last_updated']          = date.today().isoformat()
            save_config(config)
            print(f'Subscriber count updated: {new_count}')
        return

    current  = config.get('current_subscribers', 0)
    last_wk  = config.get('last_week_subscribers', 0)
    monthly  = config.get('monthly_target', 500)
    growth   = current - last_wk
    pct      = (current / goal * 100) if goal else 0
    proj     = project_10k_date(current, growth)
    weekly_target = monthly // 4

    lines = [
        f'RACE(2)10k WEEKLY REPORT — {date.today().isoformat()}',
        f'Current: {current:,} subscribers',
        f'Goal: {goal:,}',
        f'Progress: {pct:.1f}%',
        f'Weekly growth: +{growth}',
        f'Projected 10k date: {proj}',
        f'',
        f'This week\'s growth target: +{weekly_target}',
        f'Praying for {weekly_target} new members',
        f'',
        f'Phase: {config.get("scaling", {}).get("phase_1", "RACE(2)10k — 0 to 10,000")}',
        f'',
        f'To update count: tell Hermes "RACE update [number]"',
    ]
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
