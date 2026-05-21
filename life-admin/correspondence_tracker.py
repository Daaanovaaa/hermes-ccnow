#!/usr/bin/env python3
"""
Life Admin Layer — Correspondence Tracker
Monitors TWO Gmail accounts for category-matched emails.

  leeegaaal@gmail.com        — life-admin: housing, benefits, legal, bankruptcy
  faaaithmusicmovies@gmail.com — opportunities: music, film, booking, licensing, collabs

Sends immediate Telegram alerts on new matches.
Sends weekly Monday 8 AM AST (12 UTC) summary across both accounts.

Runs:
  Every 2 hours (scan):   python3 correspondence_tracker.py --scan
  Monday 12 UTC (weekly): python3 correspondence_tracker.py --weekly

Output → stdout → Hermes no_agent Telegram delivery.
Prints [SILENT] if nothing new across either account.
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ADMIN_DIR      = Path(__file__).parent
GWS_SCRIPT     = Path('/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py')

# ── Account configs ────────────────────────────────────────────────────────────

ACCOUNTS = {
    'leeegaaal': {
        'email':      'leeegaaal@gmail.com',
        'home':       '/root/.hermes/profiles/leeegaaal',
        'state_file': ADMIN_DIR / 'correspondence_state.json',
        'label':      'LIFE ADMIN',
        'keyword_groups': {
            'Housing':          ['Section 8', 'HUD', 'Housing Authority', 'HAP contract', 'housing assistance'],
            'Food Assistance':  ['SNAP', 'PAN', 'food stamps', 'Departamento de la Familia', 'ASES'],
            'Healthcare':       ['Medicare'],
            'Legal/Bankruptcy': [
                'bankruptcy', 'Chapter 7', 'Marggie', 'Rodriguez',
                'legal services', 'tribunal', 'notificacion', 'resolucion',
            ],
        },
        'emoji': {
            'Housing':          '🏠',
            'Food Assistance':  '🍽️',
            'Healthcare':       '⚕️',
            'Legal/Bankruptcy': '⚖️',
        },
    },
    'faaaithmusicmovies': {
        'email':      'faaaithmusicmovies@gmail.com',
        'home':       '/root/.hermes/profiles/faaaithmusicmovies',
        'state_file': ADMIN_DIR / 'correspondence_state_faith.json',
        'label':      'MUSIC & FILM',
        'keyword_groups': {
            'Music Opportunity': [
                'booking', 'book you', 'performance', 'show', 'concert', 'gig',
                'feature', 'collab', 'collaboration', 'remix', 'verse', 'feature request',
                'record label', 'label deal', 'A&R', 'distribution deal', 'DistroKid',
                'Spotify', 'Apple Music', 'playlist', 'curator',
            ],
            'Film / Media':      [
                'film', 'movie', 'documentary', 'soundtrack', 'score', 'sync',
                'TV', 'television', 'Netflix', 'Amazon Prime', 'Hulu', 'streaming deal',
                'music video', 'director', 'producer', 'casting',
            ],
            'Licensing':         [
                'license', 'licensing', 'sync license', 'master rights', 'publishing rights',
                'royalty', 'royalties', 'ASCAP', 'BMI', 'PRO', 'Songtrust',
                'mechanical', 'performance rights',
            ],
            'Press / Media':     [
                'interview', 'press', 'feature story', 'article', 'podcast', 'blog',
                'magazine', 'journalist', 'writer', 'review', 'premiere',
            ],
            'Business':          [
                'sponsorship', 'sponsor', 'partnership', 'brand deal', 'endorsement',
                'investment', 'investor', 'funding', 'grant', 'pitch',
            ],
        },
        'emoji': {
            'Music Opportunity': '🎵',
            'Film / Media':      '🎬',
            'Licensing':         '📜',
            'Press / Media':     '📰',
            'Business':          '🤝',
        },
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_state(account_key):
    state_file = ACCOUNTS[account_key]['state_file']
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {
        'account':          account_key,
        'last_scanned':     None,
        'seen_message_ids': [],
        'pending_reply':    [],
        'last_weekly_summary': None,
    }


def save_state(account_key, state):
    state_file = ACCOUNTS[account_key]['state_file']
    state['last_scanned'] = date.today().isoformat()
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def gws(account_key, args, timeout=30):
    """Call google_api.py with the given account's profile."""
    env = os.environ.copy()
    env['HERMES_HOME'] = ACCOUNTS[account_key]['home']
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


def build_query(account_key):
    """Build a Gmail OR search query from all keywords for this account."""
    all_kws = [
        kw
        for group in ACCOUNTS[account_key]['keyword_groups'].values()
        for kw in group
    ]
    terms = [f'"{kw}"' if ' ' in kw else kw for kw in all_kws]
    return ' OR '.join(terms)


def categorize(account_key, msg):
    """Return the first matching category label for this message."""
    text = ' '.join([
        (msg.get('subject') or ''),
        (msg.get('from') or ''),
        (msg.get('snippet') or ''),
    ]).lower()
    for category, keywords in ACCOUNTS[account_key]['keyword_groups'].items():
        for kw in keywords:
            if kw.lower() in text:
                return category
    return 'Uncategorized'


# ── Scan ───────────────────────────────────────────────────────────────────────

def scan_account(account_key):
    """
    Scan one account for new keyword-matched messages.
    Returns list of new message dicts (with 'account' and 'category' added).
    Updates state file in place.
    """
    state = load_state(account_key)
    seen  = set(state.get('seen_message_ids', []))

    results = gws(account_key, ['gmail', 'search', build_query(account_key), '--max', '50'])
    if results is None:
        return []

    new_messages = []
    for msg in results:
        mid = msg.get('id', '')
        if not mid or mid in seen:
            continue
        seen.add(mid)
        cat = categorize(account_key, msg)
        enriched = {**msg, 'account': account_key, 'category': cat,
                    'first_seen': date.today().isoformat()}
        new_messages.append(enriched)

        pending_ids = {m.get('id') for m in state.get('pending_reply', [])}
        if mid not in pending_ids:
            state.setdefault('pending_reply', []).append({
                'id':         mid,
                'subject':    msg.get('subject', '(no subject)'),
                'from':       msg.get('from', '?'),
                'date':       msg.get('date', '?'),
                'category':   cat,
                'account':    account_key,
                'first_seen': date.today().isoformat(),
                'replied':    False,
            })

    state['seen_message_ids'] = list(seen)
    save_state(account_key, state)
    return new_messages


# ── Format ─────────────────────────────────────────────────────────────────────

def format_alert(new_messages):
    """Format a combined alert for new messages across any accounts."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f'CORRESPONDENCE ALERT — {now}', '─' * 40, '']

    # Group by account for clean display
    by_account = {}
    for msg in new_messages:
        by_account.setdefault(msg['account'], []).append(msg)

    for acct_key, msgs in by_account.items():
        acct    = ACCOUNTS[acct_key]
        emoji_map = acct['emoji']
        lines.append(f"📬 {acct['label']} — {acct['email']} ({len(msgs)} new)")
        lines.append('')
        for msg in msgs:
            cat   = msg.get('category', 'Uncategorized')
            emoji = emoji_map.get(cat, '📧')
            lines += [
                f'{emoji} {cat.upper()}',
                f'From:    {msg.get("from", "?")}',
                f'Subject: {msg.get("subject", "(no subject)")}',
                f'Date:    {msg.get("date", "?")[:25]}',
                '',
            ]

    lines.append('Review and reply as needed. Tell Hermes "mark [subject] as replied" to clear.')
    return '\n'.join(lines)


def format_weekly(states_and_pendings):
    """Format weekly summary across all accounts."""
    today = date.today().isoformat()
    lines = [
        'WEEKLY CORRESPONDENCE SUMMARY',
        f'Week ending: {today}',
        '═' * 42,
        '',
    ]

    any_pending = False
    for acct_key, pending in states_and_pendings:
        acct      = ACCOUNTS[acct_key]
        emoji_map = acct['emoji']
        lines.append(f"── {acct['label']} ({acct['email']}) ──")

        if not pending:
            lines.append('  ✓ No pending correspondence.')
            lines.append('')
            continue

        any_pending = True
        by_cat = {}
        for msg in pending:
            cat = msg.get('category', categorize(acct_key, msg))
            by_cat.setdefault(cat, []).append(msg)

        lines.append(f'  Pending: {len(pending)} message(s)')
        lines.append('')
        for cat, msgs in sorted(by_cat.items()):
            emoji = emoji_map.get(cat, '📧')
            lines.append(f'  {emoji} {cat} ({len(msgs)})')
            for msg in msgs[:4]:
                lines.append(f'     • {msg.get("subject","(no subject)")[:55]}')
                lines.append(f'       from: {msg.get("from","?")[:35]}')
            if len(msgs) > 4:
                lines.append(f'     ... and {len(msgs) - 4} more')
            lines.append('')

    lines += [
        '─' * 42,
        'Tell Hermes "mark [subject] as replied" to clear from pending.',
    ]
    return '\n'.join(lines)


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_scan():
    """Scan both accounts. Alert if any new messages found."""
    all_new = []
    for acct_key in ACCOUNTS:
        all_new.extend(scan_account(acct_key))

    if not all_new:
        print('[SILENT]')
        return

    print(format_alert(all_new))


def cmd_weekly():
    """Print weekly summary across both accounts."""
    pairs = []
    for acct_key in ACCOUNTS:
        state   = load_state(acct_key)
        pending = [m for m in state.get('pending_reply', []) if not m.get('replied')]
        state['last_weekly_summary'] = date.today().isoformat()
        save_state(acct_key, state)
        pairs.append((acct_key, pending))

    print(format_weekly(pairs))


def cmd_mark_replied(subject_fragment):
    """Mark matching messages as replied in both account state files."""
    total = 0
    for acct_key in ACCOUNTS:
        state   = load_state(acct_key)
        matched = 0
        for msg in state.get('pending_reply', []):
            if subject_fragment.lower() in msg.get('subject', '').lower():
                msg['replied']      = True
                msg['replied_date'] = date.today().isoformat()
                matched += 1
        if matched:
            save_state(acct_key, state)
            total += matched
    if total:
        print(f'Marked {total} message(s) as replied.')
    else:
        print(f'No pending messages matched: "{subject_fragment}"')


def cmd_status():
    """Print one-line status for both accounts."""
    for acct_key in ACCOUNTS:
        acct    = ACCOUNTS[acct_key]
        state   = load_state(acct_key)
        pending = [m for m in state.get('pending_reply', []) if not m.get('replied')]
        print(f"{acct['email']}")
        print(f"  Pending reply: {len(pending)} | "
              f"Total seen: {len(state.get('seen_message_ids',[]))} | "
              f"Last scanned: {state.get('last_scanned','never')}")


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
        cmd_status()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
