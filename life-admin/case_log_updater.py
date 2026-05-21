#!/usr/bin/env python3
"""
Life Admin Layer — Case Log Updater
Accepts a Telegram message and prepends a new dated log entry to the
matching case file.

Called by Hermes agent when Carlos sends a message starting with "Case update:"

Message format:
  Case update: [keyword] | [what happened] | [next step] | [deadline]

Example:
  Case update: bankruptcy | Emailed Marggie Rodriguez today requesting
  Chapter 7 consultation | Wait for her reply | none

Usage:
  python3 case_log_updater.py "bankruptcy | Emailed Marggie today | Wait for reply | none"
  python3 case_log_updater.py --list       # show all case files and keywords
  python3 case_log_updater.py --status     # show one-line status for each case
"""

import re
import sys
from datetime import date
from pathlib import Path

CASES_DIR = Path(__file__).parent / 'cases'

# Keyword → case filename mapping
KEYWORD_MAP = [
    (['traffic', 'mz2026', 'mz2026mu01480', 'ticket', 'tickets', 'massa'],
     'legal_MZ2026MU01480_traffic_tickets.md',
     'Traffic Tickets MZ2026MU01480'),

    (['section8', 'section 8', 'housing', 'hud', 'hap', 'recertification'],
     'benefits_section8_recertification.md',
     'Section 8 Recertification'),

    (['snap', 'pan', 'food', 'food assistance', 'departamento', 'ases'],
     'benefits_SNAP_PAN_recertification.md',
     'SNAP / PAN Recertification'),

    (['bankruptcy', 'marggie', 'chapter7', 'chapter 7', 'quiebra', 'halsted'],
     'legal_bankruptcy_chapter7.md',
     'Bankruptcy Chapter 7'),

    (['vehicle', 'marbete', 'jvl660', 'car', 'cesco', 'dtop', 'license plate'],
     'vehicle_JVL660_marbete_license.md',
     'Vehicle JVL660 / Marbete'),

    (['civil', 'cc004806', '16-2022', 'storage zone', 'neyza', 'alegria'],
     'legal_civil_case_162022CC004806.md',
     'Civil Case 16-2022-CC-004806'),

    (['medicare', 'health', 'medicaid', 'enrollment', 'open enrollment'],
     'benefits_medicare_enrollment.md',
     'Medicare Open Enrollment'),

    (['fulkrum', 'nathan', 'adrian', 'video', 'editing', 'retainer'],
     'business_fulkrum_studios_retainer.md',
     'Fulkrum Studios Retainer'),

    (['songtrust', 'music', 'royalty', 'royalties', 'pro', 'publishing', 'historia del nino'],
     'business_songtrust_royalties.md',
     'Songtrust Royalties'),

    (['landlord', 'labor', 'exchange', 'maintenance', 'repair', 'inspection prep'],
     'landlord_labor_exchange_log.md',
     'Landlord Labor Exchange'),
    (['identity', 'license', 'id card', 'cesco', 'antecedentes', 'dtop id', 'real id', 'v451'],
     'identity_PR_license_and_ID.md',
     'PR Driver\'s License & ID Card'),
]

LOG_ENTRIES_MARKER = '## LOG ENTRIES (newest first)'


def find_case(keyword):
    """Return (filename, case_name) for the best keyword match, or (None, None)."""
    kw_lower = keyword.lower().strip()
    for keywords, filename, case_name in KEYWORD_MAP:
        for kw in keywords:
            if kw in kw_lower:
                return filename, case_name
    return None, None


def build_entry(what_happened, next_step, deadline, today):
    """Build a formatted log entry block."""
    deadline_str = deadline.strip() if deadline.strip().lower() not in ('none', 'n/a', '') else 'None'
    lines = [
        f'### {today} — Update',
        f'What happened: {what_happened.strip()}',
        f'Next step: {next_step.strip()}',
        f'Documents added: None',
        f'Deadline: {deadline_str}',
        '',
    ]
    return '\n'.join(lines)


def prepend_entry(file_path, entry_text):
    """Prepend entry_text immediately after the LOG ENTRIES header line."""
    content = file_path.read_text()

    marker_pos = content.find(LOG_ENTRIES_MARKER)
    if marker_pos == -1:
        return False, 'LOG ENTRIES section not found in file.'

    # Find the end of the marker line
    insert_pos = content.find('\n', marker_pos) + 1

    # Skip any blank lines right after the marker before first entry
    while insert_pos < len(content) and content[insert_pos] == '\n':
        insert_pos += 1

    new_content = content[:insert_pos] + '\n' + entry_text + '\n' + content[insert_pos:]

    # Also update "Last updated" date
    new_content = re.sub(
        r'^Last updated:.*$',
        f'Last updated: {date.today().isoformat()}',
        new_content,
        flags=re.MULTILINE
    )

    file_path.write_text(new_content)
    return True, 'OK'


def update_master_index(case_name, next_step, deadline, today):
    """Update the Last Updated column in MASTER_CASE_INDEX.md for this case."""
    index_path = CASES_DIR / 'MASTER_CASE_INDEX.md'
    if not index_path.exists():
        return

    content = index_path.read_text()
    # Update last updated date for this case row (match on case name fragment)
    name_fragment = case_name.split('/')[0].split('—')[0].strip()[:20]
    new_content = re.sub(
        r'^Last updated:.*$',
        f'Last updated: {today}',
        content,
        count=1,
        flags=re.MULTILINE
    )
    index_path.write_text(new_content)


def cmd_update(message):
    """
    Parse a pipe-delimited message and update the matching case log.
    Format: keyword | what happened | next step | deadline
    """
    parts = [p.strip() for p in message.split('|')]
    if len(parts) < 2:
        print('Error: message must be: keyword | what happened | next step | deadline')
        sys.exit(1)

    keyword      = parts[0]
    what_happened = parts[1] if len(parts) > 1 else ''
    next_step    = parts[2] if len(parts) > 2 else 'See case log.'
    deadline     = parts[3] if len(parts) > 3 else 'None'

    filename, case_name = find_case(keyword)
    if not filename:
        print(f'No case matched keyword: "{keyword}"')
        print('Run with --list to see all keywords.')
        sys.exit(1)

    file_path = CASES_DIR / filename
    if not file_path.exists():
        print(f'Case file not found: {file_path}')
        sys.exit(1)

    today = date.today().isoformat()
    entry = build_entry(what_happened, next_step, deadline, today)
    ok, msg = prepend_entry(file_path, entry)

    if not ok:
        print(f'Error updating {filename}: {msg}')
        sys.exit(1)

    update_master_index(case_name, next_step, deadline, today)

    # Confirmation message for Telegram delivery
    deadline_display = f' | Deadline: {deadline}' if deadline.lower() not in ('none', 'n/a', '') else ''
    print(
        f'Case log updated: {case_name}\n'
        f'Entry added: {today}\n'
        f'What: {what_happened[:80]}{"..." if len(what_happened) > 80 else ""}'
        f'{deadline_display}'
    )


def cmd_list():
    """List all case files with their keyword triggers."""
    print('CASE LOG FILES AND KEYWORDS')
    print('─' * 50)
    for keywords, filename, case_name in KEYWORD_MAP:
        exists = '✓' if (CASES_DIR / filename).exists() else '✗'
        print(f'{exists} {case_name}')
        print(f'  Keywords: {", ".join(keywords[:5])}')
        print(f'  File: {filename}')
        print()


def cmd_status():
    """Print one-line status for each case."""
    print(f'CASE STATUS — {date.today().isoformat()}')
    print('─' * 60)
    for _, filename, case_name in KEYWORD_MAP:
        file_path = CASES_DIR / filename
        if not file_path.exists():
            print(f'  MISSING  {case_name}')
            continue
        content = file_path.read_text()
        status_match = re.search(r'^Status:\s*(.+)$', content, re.MULTILINE)
        status = status_match.group(1).strip() if status_match else 'Unknown'
        print(f'  {status[:30]:30s}  {case_name}')


def main():
    args = sys.argv[1:]

    if not args or '--help' in args:
        print(__doc__)
        return

    if '--list' in args:
        cmd_list()
        return

    if '--status' in args:
        cmd_status()
        return

    # Everything else is treated as the update message
    message = ' '.join(args)
    cmd_update(message)


if __name__ == '__main__':
    main()
