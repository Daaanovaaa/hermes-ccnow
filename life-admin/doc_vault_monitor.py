#!/usr/bin/env python3
"""
Life Admin Layer — Document Vault Monitor
Scans leeegaaal@gmail.com Google Drive for life-admin documents across
all 7 categories. Detects new files and alerts via Telegram.

Runs daily at 9:00 AM AST (13:00 UTC) via Hermes cron.
Output → stdout → Telegram (Hermes no_agent delivery).
Prints [SILENT] if no new files and no missing-critical alerts.

Usage:
  python3 doc_vault_monitor.py           # daily scan + alert if new
  python3 doc_vault_monitor.py --status  # print full vault status
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ADMIN_DIR   = Path(__file__).parent
INDEX_FILE  = ADMIN_DIR / 'doc_vault_index.json'
GWS_SCRIPT  = Path('/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py')
LEEGAL_HOME = '/root/.hermes/profiles/leeegaaal'

# Categories that must never be empty — alert even with no new files
CRITICAL_CATEGORIES = {'section8', 'snap_pan', 'bankruptcy', 'legal_correspondence'}


def load_index():
    with open(INDEX_FILE) as f:
        return json.load(f)


def save_index(data):
    data['last_scanned'] = date.today().isoformat()
    with open(INDEX_FILE, 'w') as f:
        json.dump(data, f, indent=2)


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


def search_drive_for_category(cat_key, cat_data):
    """Search Drive for files matching any of the category's search terms."""
    found = []
    seen_ids = set()
    for term in cat_data.get('drive_search_terms', []):
        results = gws(['drive', 'search', term, '--max', '20'])
        if results:
            for f in results:
                fid = f.get('id', '')
                if fid and fid not in seen_ids:
                    seen_ids.add(fid)
                    found.append({
                        'id':       fid,
                        'name':     f.get('name', '?'),
                        'modified': f.get('modifiedTime', '')[:10],
                        'type':     f.get('mimeType', '').split('.')[-1],
                    })
    return found


def scan_all_categories():
    """Scan Drive for all categories. Returns dict: cat_key → list of files found."""
    index = load_index()
    results = {}
    new_files = []
    known = index.get('known_drive_files', {})

    for cat_key, cat_data in index['categories'].items():
        files = search_drive_for_category(cat_key, cat_data)
        results[cat_key] = files

        # Detect new files (not in known_drive_files)
        for f in files:
            fid = f['id']
            if fid not in known:
                new_files.append({**f, 'category': cat_key,
                                   'category_label': cat_data['label']})
                known[fid] = {
                    'name':     f['name'],
                    'category': cat_key,
                    'first_seen': date.today().isoformat(),
                }

    index['known_drive_files'] = known
    save_index(index)
    return results, new_files, index


def format_new_file_alert(new_files):
    lines = [
        'DOCUMENT VAULT — NEW FILE DETECTED',
        f'Date: {date.today().isoformat()}',
        '─' * 36,
        '',
    ]
    for f in new_files:
        lines += [
            f"📄 {f['name']}",
            f"   Category: {f['category_label']}",
            f"   Modified: {f['modified']}",
            '',
        ]
    lines += [
        'Action: Review in leeegaaal Google Drive.',
        'If this is a critical document, confirm it in doc_vault_index.json.',
    ]
    return '\n'.join(lines)


def format_status_report(results, index):
    lines = [
        'DOCUMENT VAULT STATUS',
        f'Scanned: {date.today().isoformat()} | Profile: leeegaaal@gmail.com',
        '─' * 40,
        '',
    ]
    for cat_key, cat_data in index['categories'].items():
        found     = results.get(cat_key, [])
        expected  = cat_data.get('expected_documents', [])
        confirmed = cat_data.get('documents_confirmed', [])
        status    = '✓' if found else '⚠ EMPTY'
        critical  = ' [CRITICAL]' if cat_key in CRITICAL_CATEGORIES else ''
        lines.append(f"{status} {cat_data['label']}{critical}")
        lines.append(f"  Found in Drive: {len(found)} file(s)")
        lines.append(f"  Expected: {len(expected)} | Confirmed: {len(confirmed)}")
        if found:
            for f in found[:3]:
                lines.append(f"    • {f['name']} ({f['modified']})")
            if len(found) > 3:
                lines.append(f"    ... and {len(found) - 3} more")
        missing = [e for e in expected if e not in confirmed]
        if missing and cat_key in CRITICAL_CATEGORIES:
            lines.append(f"  Missing: {', '.join(missing[:2])}"
                         + (f" +{len(missing)-2} more" if len(missing) > 2 else ""))
        lines.append('')
    return '\n'.join(lines)


def format_critical_empty_alert(empty_critical, index):
    lines = [
        'DOCUMENT VAULT — CRITICAL CATEGORIES EMPTY',
        f'Date: {date.today().isoformat()}',
        '─' * 36,
        '',
        'The following critical document categories have NO files in Drive:',
        '',
    ]
    for cat_key in empty_critical:
        cat = index['categories'][cat_key]
        lines.append(f"⚠️  {cat['label']}")
        for doc in cat['expected_documents'][:3]:
            lines.append(f"     Needed: {doc}")
        lines.append('')
    lines += [
        'Upload documents to leeegaaal@gmail.com Google Drive.',
        'These documents protect your housing, food, and legal standing.',
    ]
    return '\n'.join(lines)


def main():
    status_mode = '--status' in sys.argv

    if not INDEX_FILE.exists():
        print('ERROR: doc_vault_index.json not found.')
        sys.exit(1)

    results, new_files, index = scan_all_categories()

    if status_mode:
        print(format_status_report(results, index))
        return

    output_parts = []

    # Alert on new files (highest priority)
    if new_files:
        output_parts.append(format_new_file_alert(new_files))

    # Alert if critical categories are empty (once per week — suppress if already sent today)
    empty_critical = [
        k for k in CRITICAL_CATEGORIES
        if not results.get(k)
    ]
    last_alert = index.get('last_alert_sent')
    today = date.today().isoformat()
    alert_due = (last_alert is None or
                 (date.fromisoformat(last_alert) + __import__('datetime').timedelta(days=7)
                  <= date.today()))

    if empty_critical and alert_due and not new_files:
        output_parts.append(format_critical_empty_alert(empty_critical, index))
        index['last_alert_sent'] = today
        save_index(index)

    if not output_parts:
        print('[SILENT]')
        return

    print('\n\n'.join(output_parts))


if __name__ == '__main__':
    main()
