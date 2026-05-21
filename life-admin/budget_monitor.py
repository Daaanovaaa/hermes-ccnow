#!/usr/bin/env python3
"""
Life Admin Layer — Budget Protection Monitor
Runs daily at 9:15 AM AST (13:15 UTC) — 15 min after daily_run.py.

1. Pulls live bank balances via Plaid (Fifth Third + Banco Popular)
2. Reads total fixed expenses from the Personal Budget Google Sheet
3. Calculates buffer = total balance minus total fixed expenses
4. Reports to Telegram with HEALTHY / WATCH / ALERT status

Output -> stdout -> Hermes no_agent Telegram delivery.

Google Sheet: CCN Personal Budget — Carlos Villanueva
Sheet ID: 1A3Iilsr6DpE5JRtZFnBADpqlyOGXsz2KLvUsFiDOgwg
"""

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERMES_PYTHON   = '/usr/local/lib/hermes-agent/venv/bin/python3'
BALANCE_SCRIPT  = '/root/hermes-ccnow/automation/scripts/get_balances.py'
GWS_SCRIPT      = '/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
BUDGET_SHEET_ID = '1A3Iilsr6DpE5JRtZFnBADpqlyOGXsz2KLvUsFiDOgwg'

EMERGENCY_FLOOR   = 50.0
WATCH_THRESHOLD   = 100.0


def get_balances():
    try:
        result = subprocess.run(
            [HERMES_PYTHON, BALANCE_SCRIPT],
            capture_output=True, text=True, timeout=35
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if not data.get('error'):
                return data
    except Exception:
        pass
    return None


def get_fixed_expenses():
    try:
        result = subprocess.run(
            [sys.executable, GWS_SCRIPT,
             'sheets', 'get', BUDGET_SHEET_ID, "Monthly Budget!A1:G30"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None, []
        rows = json.loads(result.stdout)
        fixed_total = 0.0
        fixed_items = []
        in_fixed = False
        for row in rows:
            if not row:
                continue
            label = str(row[0]).strip()
            if 'EXPENSES' in label and 'FIXED' in label:
                in_fixed = True
                continue
            if in_fixed and ('VARIABLE' in label or 'SAVINGS' in label or 'EXPENSES' in label):
                break
            if in_fixed and len(row) >= 3:
                try:
                    amt = float(str(row[2]).replace('$', '').replace(',', ''))
                    if amt > 0:
                        fixed_total += amt
                        fixed_items.append((label, amt))
                except (ValueError, TypeError):
                    pass
        return fixed_total, fixed_items
    except Exception:
        return None, []


def account_total(bank_data, bank_key):
    return sum(
        a.get('balance', 0.0)
        for a in bank_data.get('accounts', [])
        if a.get('bank') == bank_key
    )


def main():
    today = date.today().isoformat()
    bank_data = get_balances()

    if bank_data is None:
        print(
            f'BUDGET REPORT {today}\n'
            f'Bank balance unavailable (Plaid API unreachable)\n'
            f'Check manually: Fifth Third app / Banco Popular app'
        )
        return

    fifth_third   = account_total(bank_data, 'fifth_third')
    banco_popular = account_total(bank_data, 'banco_popular')
    total         = fifth_third + banco_popular

    fixed_total, fixed_items = get_fixed_expenses()
    has_fixed = fixed_total is not None and fixed_total > 0
    buffer    = total - (fixed_total or 0)

    min_acct = min(fifth_third, banco_popular)
    if min_acct < EMERGENCY_FLOOR or buffer < EMERGENCY_FLOOR:
        status = 'ALERT'
        emoji  = 'ALERT'
    elif buffer < WATCH_THRESHOLD:
        status = 'WATCH'
        emoji  = 'WATCH'
    else:
        status = 'HEALTHY'
        emoji  = 'HEALTHY'

    lines = [
        f'BUDGET REPORT {today}',
        f'Fifth Third:     ${fifth_third:,.2f}',
        f'Banco Popular:   ${banco_popular:,.2f}',
        f'Total Available: ${total:,.2f}',
    ]
    if has_fixed:
        lines.append(f'Fixed Expenses:  ${fixed_total:,.2f}')
    else:
        lines.append('Fixed Expenses:  (TBD — fill in Budget Sheet)')
    lines.append(f'Buffer:          ${buffer:,.2f}')
    lines.append(f'Status: {status}')

    if status == 'ALERT':
        lines.append('ACTION REQUIRED: balance near or below emergency floor.')
        lines.append('Defer non-essential spending immediately.')
    elif status == 'WATCH':
        lines.append('Buffer is low. Review expenses before spending.')
    else:
        lines.append('Budget looks stable. Keep pushing.')

    if not has_fixed:
        lines.append(f'Tip: Fill TBD rows in Budget Sheet to get accurate buffer.')

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
