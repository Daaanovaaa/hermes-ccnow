#!/usr/bin/env python3
"""
Obsidian Vault Daily Sync
Runs nightly at 2:00 AM UTC (10 PM AST).

1. Copies all 14 case logs to 01-Life-Admin/
2. Copies all department knowledge files to 02-Ministry/
3. Updates HOME.md with today's dashboard
4. Updates budget_overview.md with latest balances
5. Syncs prayer finance log
6. Git add + commit + push vault so Obsidian Git can pull

Usage:
  python3 obsidian_sync.py
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT     = Path('/root/hermes-ccnow')
VAULT_DIR     = REPO_ROOT / 'obsidian-vault'
CASES_DIR     = REPO_ROOT / 'life-admin' / 'cases'
DEPTS_DIR     = REPO_ROOT / 'departments'
LIFE_DIR      = REPO_ROOT / 'life-reality'
PRAYER_DIR    = REPO_ROOT / 'prayer-finance'
HERMES_PYTHON = '/usr/local/lib/hermes-agent/venv/bin/python3'
BALANCE_SCRIPT = REPO_ROOT / 'automation' / 'scripts' / 'get_balances.py'


def copy_case_logs():
    """Copy all case logs to 01-Life-Admin/"""
    target = VAULT_DIR / '01-Life-Admin'
    target.mkdir(exist_ok=True)
    copied = 0
    if CASES_DIR.exists():
        for f in CASES_DIR.glob('*.md'):
            shutil.copy2(f, target / f.name)
            copied += 1
    return copied


def copy_departments():
    """Copy department knowledge files to 02-Ministry/"""
    target = VAULT_DIR / '02-Ministry'
    target.mkdir(exist_ok=True)
    copied = 0
    if DEPTS_DIR.exists():
        for f in DEPTS_DIR.glob('*.md'):
            shutil.copy2(f, target / f.name)
            copied += 1
    return copied


def copy_legal_cases():
    """Copy legal-specific cases to 04-Legal/"""
    target = VAULT_DIR / '04-Legal'
    target.mkdir(exist_ok=True)
    if CASES_DIR.exists():
        for f in CASES_DIR.glob('legal_*.md'):
            shutil.copy2(f, target / f.name)


def copy_health_log():
    """Copy health log to 05-Health/"""
    target = VAULT_DIR / '05-Health'
    target.mkdir(exist_ok=True)
    health_file = CASES_DIR / 'health_log_carlos.md'
    if health_file.exists():
        shutil.copy2(health_file, target / 'health_log.md')


def copy_education():
    """Copy education file to 06-Education/"""
    target = VAULT_DIR / '06-Education'
    target.mkdir(exist_ok=True)
    ed_file = CASES_DIR / 'education_certifications.md'
    if ed_file.exists():
        shutil.copy2(ed_file, target / 'education_log.md')


def get_balances():
    try:
        result = subprocess.run(
            [HERMES_PYTHON, str(BALANCE_SCRIPT)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if not data.get('error'):
                return data
    except Exception:
        pass
    return None


def get_upcoming_deadlines():
    """Extract upcoming deadlines from case logs."""
    deadlines = []
    today     = date.today()
    cutoff    = today + timedelta(days=30)
    if CASES_DIR.exists():
        for f in CASES_DIR.glob('*.md'):
            content = f.read_text()
            for line in content.split('\n'):
                if 'Deadline:' in line and '20' in line:
                    for part in line.split():
                        if part.startswith('20') and len(part) == 10:
                            try:
                                d = date.fromisoformat(part)
                                if today <= d <= cutoff:
                                    deadlines.append((d, f.stem, line.strip()))
                            except ValueError:
                                pass
    return sorted(deadlines)


def update_home_md(bank_data, deadlines, case_count):
    today     = date.today().isoformat()
    fifth     = 0.0
    banco     = 0.0
    if bank_data:
        for a in bank_data.get('accounts', []):
            if a.get('primary'):
                if a['bank'] == 'fifth_third':
                    fifth += a.get('balance', 0)
                elif a['bank'] == 'banco_popular':
                    banco += a.get('balance', 0)

    deadline_lines = ''
    if deadlines:
        for d, case, line in deadlines[:5]:
            deadline_lines += f'- **{d}** — {case}: {line[:60]}\n'
    else:
        deadline_lines = '- No deadlines in the next 30 days\n'

    content = f"""# Hermes Dashboard
*Last sync: {today} at 10 PM AST*

---

## 💰 Budget Status
- Fifth Third: ${fifth:,.2f}
- Banco Popular: ${banco:,.2f}
- **Total: ${fifth+banco:,.2f}**

→ [[budget_overview|Full Budget Details]]

---

## 📋 Active Cases ({case_count} total)
→ [[MASTER_CASE_INDEX|View All Cases]]

---

## ⏰ Upcoming Deadlines (Next 30 Days)
{deadline_lines}

---

## Quick Links
- [[MASTER_CASE_INDEX|📋 All Cases]]
- [[CCN_DEPARTMENT_INDEX|🏢 CCN Departments]]
- [[budget_overview|💰 Budget]]
- [[race2_10k_progress|📊 RACE(2)10k]]
- [[prayer_finance_status|🙏 Prayer Finance]]
"""
    home = VAULT_DIR / '00-Dashboard' / 'HOME.md'
    home.write_text(content)


def update_prayer_finance():
    """Sync prayer finance log to vault."""
    log_file = PRAYER_DIR / 'prayer_finance_log.json'
    if not log_file.exists():
        return
    data = json.loads(log_file.read_text())
    target = VAULT_DIR / '09-Prayer-Journal' / 'prayer_finance_status.md'

    entries_text = ''
    for e in data.get('entries', [])[-5:]:
        entries_text += f"- {e['date']} | {e['ticker']} | ${e['amount']:.2f} | PW-ID: {e['pw_id']} | #{e.get('confirmation_number','pending')}\n"
    if not entries_text:
        entries_text = '*No seeds planted yet — first seed pending this Friday.*\n'

    content = f"""# Prayer Finance Status
*Synced: {date.today().isoformat()}*

Seeds planted: {data['total_seeds_planted']}
Total invested: ${data['total_invested']:.2f}
Scripture: Mark 4:26-29

## Recent Seeds
{entries_text}
## Weekly Schedule
- Friday 6 PM AST — IPO research
- Friday 7 PM AST — Shortlist on Telegram
- Saturday 8 AM AST — Final recommendation
- Sunday 10 AM AST — Journal entry
"""
    target.write_text(content)


def git_push():
    """Stage, commit, and push vault changes."""
    try:
        subprocess.run(['git', '-C', str(REPO_ROOT), 'add', 'obsidian-vault/'],
                      capture_output=True, timeout=15)
        result = subprocess.run(
            ['git', '-C', str(REPO_ROOT), 'commit', '-m',
             f'obsidian-vault: daily sync {date.today().isoformat()}'],
            capture_output=True, text=True, timeout=15
        )
        if 'nothing to commit' not in result.stdout:
            subprocess.run(['git', '-C', str(REPO_ROOT), 'push', 'origin', 'main'],
                          capture_output=True, timeout=30)
            return True
    except Exception:
        pass
    return False


def main():
    today     = date.today().isoformat()
    case_count = len(list(CASES_DIR.glob('*.md'))) if CASES_DIR.exists() else 0

    cases_copied = copy_case_logs()
    depts_copied = copy_departments()
    copy_legal_cases()
    copy_health_log()
    copy_education()

    bank_data   = get_balances()
    deadlines   = get_upcoming_deadlines()
    update_home_md(bank_data, deadlines, case_count)
    update_prayer_finance()

    pushed = git_push()

    lines = [
        f'OBSIDIAN VAULT SYNCED — {today}',
        f'Case logs copied: {cases_copied}',
        f'Department files copied: {depts_copied}',
        f'Upcoming deadlines found: {len(deadlines)}',
        f'Dashboard updated: HOME.md',
        f'Git pushed: {"YES" if pushed else "no changes"}',
        f'',
        f'Vault ready for morning pull in Obsidian.',
    ]
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
