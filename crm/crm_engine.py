#!/usr/bin/env python3
"""
CCN Master CRM Engine — Google Sheets backed CRM with Telegram commands.

Telegram commands:
  "Add contact: [name] | [email] | [phone] | [category] | [notes]"
  "Find contact: [name or email]"
  "Log interaction: [name] | [type] | [summary] | [follow up date]"
  "CRM pipeline: [name] | [opportunity] | [stage] | [value]"
  "CRM follow-ups today"
  "Add to prayer list: [name] | [request]"
  "CRM stats"

Usage:
  python3 crm_engine.py --add "name|email|phone|category|notes"
  python3 crm_engine.py --find "query"
  python3 crm_engine.py --log-interaction "name|type|summary|followup"
  python3 crm_engine.py --pipeline "name|opportunity|stage|value"
  python3 crm_engine.py --followups-today
  python3 crm_engine.py --prayer "name|request"
  python3 crm_engine.py --stats
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

GWS_SCRIPT = '/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
CRM_SHEET_ID = '1r_UxrLVvkymiu3J1roCio9reUJt1YYTJU3ymSmihcW0'
CRM_SHEET_URL = f'https://docs.google.com/spreadsheets/d/{CRM_SHEET_ID}'

CATEGORIES = ['Ministry', 'Business', 'Media', 'Music', 'Legal', 'Government', 'Personal', 'Family']
STATUSES   = ['Active', 'Warm', 'Cold', 'VIP', 'Prayer', 'Do Not Contact']
STAGES     = ['Lead', 'Prospect', 'Engaged', 'Proposal', 'Closed Won', 'Closed Lost']
INT_TYPES  = ['Email', 'Call', 'WhatsApp', 'In Person', 'Telegram']


def gws(args, timeout=20):
    try:
        r = subprocess.run(
            [sys.executable, GWS_SCRIPT] + args,
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return None


def get_all_contacts():
    rows = gws(['sheets', 'get', CRM_SHEET_ID, "'Contacts'!A2:N500"])
    return rows or []


def get_next_contact_id(contacts):
    if not contacts:
        return 'C0001'
    ids = [r[0] for r in contacts if r and r[0].startswith('C')]
    if not ids:
        return 'C0001'
    nums = [int(i[1:]) for i in ids if i[1:].isdigit()]
    return f'C{max(nums)+1:04d}' if nums else 'C0001'


def append_row(tab, values):
    gws(['sheets', 'append', CRM_SHEET_ID, f"'{tab}'!A1", '--values', json.dumps([values])])


def cmd_add(args_str):
    parts = [p.strip() for p in args_str.split('|')]
    name     = parts[0] if len(parts) > 0 else ''
    email    = parts[1] if len(parts) > 1 else ''
    phone    = parts[2] if len(parts) > 2 else ''
    category = parts[3] if len(parts) > 3 else 'Personal'
    notes    = parts[4] if len(parts) > 4 else ''

    if not name:
        print('Error: name is required.')
        return

    contacts = get_all_contacts()
    cid      = get_next_contact_id(contacts)
    today    = date.today().isoformat()

    row = [cid, name, email, phone, category, '', 'Hermes', '', 'English', today, notes, '', 'Active', '']
    append_row('Contacts', row)
    print(f'Contact added: {cid} — {name}\nEmail: {email}\nCategory: {category}\nCRM: {CRM_SHEET_URL}')


def cmd_find(query):
    contacts = get_all_contacts()
    q        = query.lower()
    matches  = [r for r in contacts if any(q in str(c).lower() for c in r)]

    if not matches:
        print(f'No contacts found matching: "{query}"')
        return

    lines = [f'CRM search: "{query}" — {len(matches)} match(es)', '─' * 36]
    for r in matches[:5]:
        lines += [
            f'ID: {r[0] if len(r)>0 else "?"}  Name: {r[1] if len(r)>1 else "?"}',
            f'Email: {r[2] if len(r)>2 else "?"}  Phone: {r[3] if len(r)>3 else "?"}',
            f'Category: {r[4] if len(r)>4 else "?"}  Status: {r[12] if len(r)>12 else "?"}',
            f'Last contact: {r[9] if len(r)>9 else "?"}',
            '',
        ]
    if len(matches) > 5:
        lines.append(f'... and {len(matches)-5} more results.')
    print('\n'.join(lines))


def cmd_log_interaction(args_str):
    parts    = [p.strip() for p in args_str.split('|')]
    name     = parts[0] if len(parts) > 0 else ''
    int_type = parts[1] if len(parts) > 1 else 'Email'
    summary  = parts[2] if len(parts) > 2 else ''
    followup = parts[3] if len(parts) > 3 else ''

    contacts = get_all_contacts()
    match    = next((r for r in contacts if name.lower() in str(r[1]).lower()), None)
    cid      = match[0] if match else '?'
    today    = date.today().isoformat()

    row = [today, cid, name, int_type, 'Outbound', summary, 'Yes' if followup else 'No', followup]
    append_row('Interaction Log', row)
    print(f'Interaction logged: {name} — {int_type}\nSummary: {summary}\nFollow-up: {followup or "None"}')


def cmd_pipeline(args_str):
    parts   = [p.strip() for p in args_str.split('|')]
    name    = parts[0] if len(parts) > 0 else ''
    opp     = parts[1] if len(parts) > 1 else ''
    stage   = parts[2] if len(parts) > 2 else 'Lead'
    value   = parts[3] if len(parts) > 3 else '0'
    today   = date.today().isoformat()

    contacts = get_all_contacts()
    match    = next((r for r in contacts if name.lower() in str(r[1]).lower()), None)
    cid      = match[0] if match else '?'

    row = [cid, name, opp, stage, value, '50%', '', today, '']
    append_row('Pipeline', row)
    print(f'Pipeline updated: {name}\nOpportunity: {opp}\nStage: {stage} | Value: ${value}')


def cmd_followups_today():
    rows  = gws(['sheets', 'get', CRM_SHEET_ID, "'Interaction Log'!A2:H500"])
    today = date.today().isoformat()
    due   = [r for r in (rows or []) if len(r) > 7 and r[7] == today]

    if not due:
        print(f'No follow-ups due today ({today}).')
        return

    lines = [f'FOLLOW-UPS DUE TODAY — {today}', '─' * 36]
    for r in due:
        lines.append(f'  {r[2]} — {r[3]}: {r[5][:60]}')
    print('\n'.join(lines))


def cmd_prayer(args_str):
    parts   = [p.strip() for p in args_str.split('|')]
    name    = parts[0] if len(parts) > 0 else ''
    request = parts[1] if len(parts) > 1 else ''
    today   = date.today().isoformat()

    row = [name, request, today, '', '']
    append_row('Prayer List', row)
    print(f'Added to prayer list: {name}\nRequest: {request}\nAdded: {today}')


def cmd_stats():
    contacts = get_all_contacts()
    pipeline = gws(['sheets', 'get', CRM_SHEET_ID, "'Pipeline'!A2:I500"]) or []
    prayer   = gws(['sheets', 'get', CRM_SHEET_ID, "'Prayer List'!A2:E500"]) or []
    ilog     = gws(['sheets', 'get', CRM_SHEET_ID, "'Interaction Log'!A2:H500"]) or []

    today    = date.today().isoformat()
    due_today = len([r for r in ilog if len(r) > 7 and r[7] == today])

    cat_counts = {}
    for r in contacts:
        cat = r[4] if len(r) > 4 else 'Unknown'
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    lines = [
        f'CRM STATS — {today}',
        f'─' * 36,
        f'Total contacts: {len(contacts)}',
        f'Pipeline items: {len(pipeline)}',
        f'Prayer requests: {len(prayer)}',
        f'Follow-ups due today: {due_today}',
        f'',
        f'By category:',
    ]
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        lines.append(f'  {cat}: {count}')
    lines.append(f'\nSheet: {CRM_SHEET_URL}')
    print('\n'.join(lines))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]
    val = ' '.join(args[1:]) if len(args) > 1 else ''

    if cmd == '--add':              cmd_add(val)
    elif cmd == '--find':           cmd_find(val)
    elif cmd == '--log-interaction':cmd_log_interaction(val)
    elif cmd == '--pipeline':       cmd_pipeline(val)
    elif cmd == '--followups-today':cmd_followups_today()
    elif cmd == '--prayer':         cmd_prayer(val)
    elif cmd == '--stats':          cmd_stats()
    else: print(__doc__)


if __name__ == '__main__':
    main()
