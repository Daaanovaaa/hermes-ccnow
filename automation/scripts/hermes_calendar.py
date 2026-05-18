#!/usr/bin/env python3
"""
Hermes Calendar — creates Google Calendar events following the CC NOW! format.
Events appear in Fantastical color-coded by pillar.

Usage:
  python3 hermes_calendar.py create \
    --pillar MONEY \
    --summary "Sales Outreach Block" \
    --date 2026-05-20 \
    --start 15:00 \
    --end 17:00 \
    --why "Every sales hour compounds toward the millionaire target." \
    --coaching "The rock doesn't roll itself, DaNova. Push it." \
    --status CONFIRMED

  python3 hermes_calendar.py seed-week --date 2026-05-19
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# Reuse auth from google-workspace skill
GWS_SCRIPTS = Path('/root/.hermes/skills/productivity/google-workspace/scripts')
sys.path.insert(0, str(GWS_SCRIPTS))

try:
    from google_api import get_credentials, build_service
    HAS_DIRECT = True
except ImportError:
    HAS_DIRECT = False

CALENDAR_ID = 'primary'
TZ_OFFSET   = '-04:00'  # AST — Puerto Rico (no DST)
TZ_NAME     = 'America/Puerto_Rico'

# Google Calendar colorId mapping by pillar
PILLAR_META = {
    'FUNNY':  {'emoji': '😄', 'color_id': '5',  'tag': 'FUNNY'},   # Banana (yellow/gold)
    'MONEY':  {'emoji': '💰', 'color_id': '10', 'tag': 'MONEY'},   # Basil (green)
    'HONEY':  {'emoji': '🍯', 'color_id': '4',  'tag': 'HONEY'},   # Flamingo (pink)
    'SPIRIT': {'emoji': '🙏', 'color_id': '3',  'tag': 'SPIRIT'},  # Grape (purple)
    'HERMES': {'emoji': '⚙️', 'color_id': '7',  'tag': 'HERMES'},  # Peacock (blue)
}

# Daily schedule anchors (time, pillar, title, duration_min, status)
DAILY_SCHEDULE = [
    ('05:00', '05:30', 'HONEY',  'Wake, coffee, high-protein breakfast',        'CONFIRMED'),
    ('05:30', '08:30', 'FUNNY',  'RAP WORK — airplane mode',                    'CONFIRMED'),
    ('10:00', '12:00', 'MONEY',  'CC NOW! Deep Work — content, product, output','CONFIRMED'),
    ('12:00', '12:30', 'HONEY',  'Pescatarian Lunch',                           'CONFIRMED'),
    ('13:00', '15:00', 'HERMES', 'ADMIN BATCH — Hermes delegation window',      'CONFIRMED'),
    ('15:00', '17:00', 'MONEY',  'Sales, marketing, outreach, revenue actions', 'CONFIRMED'),
    ('17:00', '19:00', 'MONEY',  'Learning / Ministry / La Fortaleza PR mag',   'CONFIRMED'),
    ('21:00', '21:30', 'HERMES', 'Next-Day Prep + Hermes debrief',              'CONFIRMED'),
    ('21:30', '22:00', 'HONEY',  'Honey Time / Wind-down',                      'CONFIRMED'),
]

GYM_DAYS    = {0, 2, 4, 5}   # Mon, Wed, Fri, Sat
CHURCH_DAYS = {1, 3, 6}      # Tue, Thu, Sun

COACHING_BY_PILLAR = {
    'FUNNY':  "Protect the joy, DaNova. A rested artist creates better.",
    'MONEY':  "The rock doesn't roll itself, DaNova. Push it.",
    'HONEY':  "Kingdom health is the foundation everything else is built on.",
    'SPIRIT': "Stay rooted. The anointing precedes the assignment.",
    'HERMES': "Every admin task delegated is an hour returned to the mission.",
}


def to_iso(date_str, time_str):
    """Convert date (YYYY-MM-DD) + time (HH:MM) to ISO 8601 with AST offset."""
    return f"{date_str}T{time_str}:00{TZ_OFFSET}"


def build_description(pillar, why, coaching, status):
    meta = PILLAR_META.get(pillar, PILLAR_META['MONEY'])
    coaching = coaching or COACHING_BY_PILLAR.get(pillar, '')
    why      = why or "This block advances the CC NOW! millionaire mission."
    return (
        f"Why this matters: {why}\n"
        f"Hermes says: \"{coaching}\"\n"
        f"Pillar: {meta['emoji']} {meta['tag']} | Status: {status}"
    )


def create_event(service, pillar, summary, date_str, start_time, end_time,
                 why='', coaching='', location='', status='TESTING'):
    meta = PILLAR_META.get(pillar.upper(), PILLAR_META['MONEY'])
    title = f"{meta['emoji']} {summary} — {meta['tag']}"
    description = build_description(pillar.upper(), why, coaching, status)

    event = {
        'summary':     title,
        'description': description,
        'colorId':     meta['color_id'],
        'start': {'dateTime': to_iso(date_str, start_time), 'timeZone': TZ_NAME},
        'end':   {'dateTime': to_iso(date_str, end_time),   'timeZone': TZ_NAME},
    }
    if location:
        event['location'] = location

    result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {
        'status':   'created',
        'id':       result['id'],
        'summary':  result.get('summary', ''),
        'htmlLink': result.get('htmlLink', ''),
        'colorId':  meta['color_id'],
        'pillar':   pillar.upper(),
    }


def seed_week(service, start_date_str):
    """Seed a full week of the standard CC NOW! daily schedule.

    Day-specific overrides:
      Sunday  — RAP WORK shortened to 5:30–8:00 AM (church at 8:00 AM)
      Tuesday — Sales block (3–5 PM) replaced by church rehearsal (3–6 PM)
    """
    start   = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    created = []

    for day_offset in range(7):
        day     = start + timedelta(days=day_offset)
        date_str = day.strftime('%Y-%m-%d')
        weekday  = day.weekday()  # 0=Mon … 6=Sun
        is_sun   = weekday == 6
        is_tue   = weekday == 1

        for start_t, end_t, pillar, title, event_status in DAILY_SCHEDULE:
            # Sunday: shorten rap block to end at 8:00 for church
            if is_sun and title == 'RAP WORK — airplane mode':
                end_t = '08:00'

            # Tuesday: skip the sales block — church rehearsal owns that time
            if is_tue and title == 'Sales, marketing, outreach, revenue actions':
                continue

            created.append(create_event(
                service, pillar, title, date_str, start_t, end_t,
                status=event_status
            ))

        # 8:30 AM slot — gym (TESTING) or devotional (CONFIRMED)
        # Sunday: church covers the morning; no extra slot needed
        if not is_sun:
            if weekday in GYM_DAYS:
                created.append(create_event(
                    service, 'HONEY', 'Planet Fitness', date_str, '08:30', '09:30',
                    why='Physical discipline compounds into mental clarity for creative work.',
                    status='TESTING'
                ))
            else:
                created.append(create_event(
                    service, 'SPIRIT', 'Devotional + Prayer', date_str, '08:30', '09:30',
                    why='The anointing precedes the assignment.',
                    status='CONFIRMED'
                ))

        # Tuesday: church rehearsal (replaces sales block)
        if is_tue:
            created.append(create_event(
                service, 'SPIRIT', 'The Gathering — Audio Engineer Rehearsal',
                date_str, '15:00', '18:00',
                why='Ministry commitment — audio engineering is pastoral service.',
                status='CONFIRMED'
            ))

        # Sunday: church service (anchor)
        if is_sun:
            created.append(create_event(
                service, 'SPIRIT', 'The Gathering Church — Audio Engineer',
                date_str, '08:00', '13:00',
                why='Weekly anchor. Non-negotiable.',
                status='CONFIRMED'
            ))

    return created


def cmd_create(args):
    service = build_service('calendar', 'v3')
    result  = create_event(
        service,
        pillar     = args.pillar.upper(),
        summary    = args.summary,
        date_str   = args.date,
        start_time = args.start,
        end_time   = args.end,
        why        = args.why or '',
        coaching   = args.coaching or '',
        location   = args.location or '',
        status     = args.status.upper(),
    )
    print(json.dumps(result, indent=2))


def cmd_seed(args):
    service = build_service('calendar', 'v3')
    results = seed_week(service, args.date)
    print(json.dumps({'seeded': len(results), 'events': results}, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Hermes Calendar — CC NOW! event writer')
    sub    = parser.add_subparsers(dest='cmd')

    p_create = sub.add_parser('create', help='Create a single event')
    p_create.add_argument('--pillar',   required=True, choices=['FUNNY','MONEY','HONEY','SPIRIT','HERMES'])
    p_create.add_argument('--summary',  required=True)
    p_create.add_argument('--date',     required=True, help='YYYY-MM-DD')
    p_create.add_argument('--start',    required=True, help='HH:MM (AST)')
    p_create.add_argument('--end',      required=True, help='HH:MM (AST)')
    p_create.add_argument('--why',      default='')
    p_create.add_argument('--coaching', default='')
    p_create.add_argument('--location', default='')
    p_create.add_argument('--status',   default='TESTING', choices=['TESTING','CONFIRMED'])
    p_create.set_defaults(func=cmd_create)

    p_seed = sub.add_parser('seed-week', help='Seed a full week of the standard schedule')
    p_seed.add_argument('--date', required=True, help='Monday of the week (YYYY-MM-DD)')
    p_seed.set_defaults(func=cmd_seed)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    args.func(args)


if __name__ == '__main__':
    main()
