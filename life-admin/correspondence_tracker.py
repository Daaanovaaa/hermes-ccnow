#!/usr/bin/env python3
"""
Life Admin Layer — Correspondence Tracker
Monitors leeegaaal@gmail.com for emails matching life-admin keywords.
Sends immediate Telegram alerts on new matches.
Sends weekly Monday 8 AM AST (12 UTC) summary of pending correspondence.

Runs:
  Every 2 hours (hourly scan): python3 correspondence_tracker.py --scan
  Monday 12 UTC (summary):     python3 correspondence_tracker.py --weekly

Output → stdout → Hermes no_agent Telegram delivery.
Prints [SILENT] if nothing new.
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ADMIN_DIR   = Path(__file__).parent
STATE_FILE  = ADMIN_DIR / 'correspondence_state.json'
GWS_SCRIPT  = Path('/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py')
LEEGAL_HOME = '/root/.hermes/profiles/leeegaaal'

# Keywords that trigger alerts — case-insensitive search applied in Gmail
KEYWORD_GROUPS = {
    'Housing': ['Section 8', 'HUD', 'Housing Authority', 'HAP contract', 'housing assistance'],
    'Food Assistance': ['SNAP', 'PAN', 'food stamps', 'Departamento de la Familia', 'ASES'],
    'Healthcare': ['Medicare'],
    'Legal / Bankruptcy': [
        'bankruptcy', 'Chapter 7', 'Marggie', 'Rodriguez',
        'legal services', 'tribunal', 'notificacion', 'resolucion'
    ],
}

# Gmail search query covering all keywords (OR logic)
ALL_KEYWORDS = [kw for group in KEYWORD_GROUPS.values() for kw in group]

# Category emoji map
CATEGORY_EMOJI = {
    'Housing': '🏠',
    'Food Assistance': '🍽️',
    'Healthcare': '⚕️',
    'Legal / Bankruptcy': '⚖️',
}


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        'last_scanned': None,
        'seen_message_ids': [],
        'pending_reply': [],
        'last_weekly_summary': None,
    }


def save_state(state):
    state['last_scanned'] = date.today().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def gws(args, timeout=30):
    """Call google_api.py with leeegaaal profile."""
    env = os.environ.copy()
    env['HERMES_HOME'] = LEEGAL_HOME
    try:
        result = subprocess.run(
            [sys.executable, str(GWS_SCRIPT)] + args,
            capture_output=True, text=True, timeout=timeout, env=env
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass
    return None


def build_gmail_query():
    """Build a Gmail search query matching any keyword."""
    # Wrap multi-word terms in quotes, join with OR
    terms = []
    for kw in ALL_KEYWORDS:
        if ' ' in kw:
            terms.append(f'"{kw}"')
        else:
            terms.append(kw)
    return ' OR '.join(terms)


def categorize_message(msg):
    """Return the first matching category for a message."""
    subject = (msg.get('subject') or '').lower()
    sender  = (msg.get('from') or '').lower()
    snippet = (msg.get('snippet') or '').lower()
    text    = f"{subject} {sender} {snippet}"

    for category, keywords in KEYWORD_GROUPS.items():
        for kw in keywords:
            if kw.lower() in text:
                return category
    return 'Uncategorized'


def format_new_alert(new_messages):
    lines = [
        'CORRESPONDENCE ALERT — leeegaaal@gmail.com',
        f'Date: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}',
        '─' * 38,
        '',
    ]
    for msg in new_messages:
        cat   = categorize_message(msg)
        emoji = CATEGORY_EMOJI.get(cat, '📧')
        lines += [
            f'{emoji} {cat.upper()}',
            f'From:    {msg.get("from", "?")}',
            f'Subject: {msg.get("subject", "(no subject)")}',
            f'Date:    {msg.get("date", "?")[:25]}',
            '',
        ]
    lines += [
        'Action: Review leeegaaal@gmail.com and reply if needed.',
        'Tell Hermes to mark as replied when done.',
    ]
    return '\n'.join(lines)


def format_weekly_summary(pending, state):
    today = date.today().isoformat()
    lines = [
        'WEEKLY CORRESPONDENCE SUMMARY — leeegaaal@gmail.com',
        f'Week ending: {today}',
        '─' * 40,
        '',
    ]

    if not pending:
        lines += [
            '✓ No pending correspondence in tracked categories.',
            '',
            'Monitored categories:',
        ]
        for cat, emoji in CATEGORY_EMOJI.items():
            lines.append(f'  {emoji} {cat}')
        return '\n'.join(lines)

    # Group by category
    by_cat = {}
    for msg in pending:
        cat = msg.get('category', categorize_message(msg))
        by_cat.setdefault(cat, []).append(msg)

    lines.append(f'PENDING CORRESPONDENCE ({len(pending)} items):')
    lines.append('')
    for cat, msgs in sorted(by_cat.items()):
        emoji = CATEGORY_EMOJI.get(cat, '📧')
        lines.append(f'{emoji} {cat} ({len(msgs)} message{"s" if len(msgs) != 1 else ""})')
        for msg in msgs[:5]:
            subj = msg.get('subject', '(no subject)')[:55]
            sndr = msg.get('from', '?')[:30]
            lines.append(f'   • {subj}')
            lines.append(f'     from: {sndr}')
        if len(msgs) > 5:
            lines.append(f'   ... and {len(msgs) - 5} more')
        lines.append('')

    lines += [
        '─' * 40,
        'Review each item and reply or file as resolved.',
        'Tell Hermes "mark [subject] as replied" to clear from pending.',
    ]
    return '\n'.join(lines)


def cmd_scan():
    """Scan Gmail for new matching messages. Alert on new ones."""
    state = load_state()
    seen  = set(state.get('seen_message_ids', []))

    query   = build_gmail_query()
    results = gws(['gmail', 'search', query, '--max', '50'])

    if results is None:
        # Gmail unreachable — suppress silently
        print('[SILENT]')
        return

    new_messages = []
    for msg in results:
        mid = msg.get('id', '')
        if mid and mid not in seen:
            seen.add(mid)
            cat = categorize_message(msg)
            new_messages.append({**msg, 'category': cat, 'first_seen': date.today().isoformat()})
            # Add to pending_reply if not already there
            pending_ids = {m.get('id') for m in state.get('pending_reply', [])}
            if mid not in pending_ids:
                state.setdefault('pending_reply', []).append({
                    'id':         mid,
                    'subject':    msg.get('subject', '(no subject)'),
                    'from':       msg.get('from', '?'),
                    'date':       msg.get('date', '?'),
                    'category':   cat,
                    'first_seen': date.today().isoformat(),
                    'replied':    False,
                })

    state['seen_message_ids'] = list(seen)
    save_state(state)

    if not new_messages:
        print('[SILENT]')
        return

    print(format_new_alert(new_messages))


def cmd_weekly():
    """Print weekly summary of pending correspondence."""
    state   = load_state()
    pending = [m for m in state.get('pending_reply', []) if not m.get('replied')]

    state['last_weekly_summary'] = date.today().isoformat()
    save_state(state)

    print(format_weekly_summary(pending, state))


def cmd_mark_replied(subject_fragment):
    """Mark messages matching subject fragment as replied."""
    state   = load_state()
    matched = 0
    for msg in state.get('pending_reply', []):
        if subject_fragment.lower() in msg.get('subject', '').lower():
            msg['replied']     = True
            msg['replied_date'] = date.today().isoformat()
            matched += 1
    save_state(state)
    if matched:
        print(f'Marked {matched} message(s) as replied.')
    else:
        print(f'No pending messages matched: "{subject_fragment}"')


def main():
    args = sys.argv[1:]

    if not args or '--scan' in args:
        cmd_scan()
    elif '--weekly' in args:
        cmd_weekly()
    elif '--mark-replied' in args:
        idx = args.index('--mark-replied')
        if idx + 1 < len(args):
            cmd_mark_replied(args[idx + 1])
        else:
            print('Usage: correspondence_tracker.py --mark-replied "subject fragment"')
    elif '--status' in args:
        state = load_state()
        pending = [m for m in state.get('pending_reply', []) if not m.get('replied')]
        print(f'Pending reply: {len(pending)} messages')
        print(f'Total seen:    {len(state.get("seen_message_ids", []))} messages')
        print(f'Last scanned:  {state.get("last_scanned", "never")}')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
