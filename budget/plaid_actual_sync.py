#!/usr/bin/env python3
"""
Plaid → Actual Budget Sync
Pulls last 7 days of bank transactions from Plaid and logs them.
Runs daily at 9:30 AM AST (13:30 UTC).

Since Actual Budget's API requires the @actual-app/api Node.js SDK,
this script:
1. Pulls transactions from Plaid (both accounts)
2. Writes them to a staging JSON file
3. Sends Telegram summary
4. Logs to the CCN Personal Budget Google Sheet (Expense Log tab)

To import into Actual Budget UI: access localhost:5006 via SSH tunnel,
transactions are auto-categorized and available for review.

Usage:
  python3 plaid_actual_sync.py              # sync last 7 days
  python3 plaid_actual_sync.py --days 30    # sync last 30 days
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

BUDGET_DIR = Path(__file__).parent
STAGING_FILE = BUDGET_DIR / 'transaction_staging.json'
GWS_SCRIPT = '/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
BUDGET_SHEET_ID = '1A3Iilsr6DpE5JRtZFnBADpqlyOGXsz2KLvUsFiDOgwg'
HERMES_PYTHON = '/usr/local/lib/hermes-agent/venv/bin/python3'

load_dotenv(Path.home() / '.hermes' / '.env')
# Expected env vars: PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV,
# FIFTH_THIRD_ACCESS_TOKEN, BANCO_POPULAR_ACCESS_TOKEN,
# TELEGRAM_BOT_TOKEN, ACTUAL_PASSWORD

# Auto-categorization rules: keyword → envelope category
CATEGORY_RULES = [
    (['walmart','costco','supermax','selectos','econo','grocery','food','aldi','kroger','publix'],  'Groceries'),
    (['gas','shell','exxon','bp','texaco','chevron','fuel','gasolinera'],                           'Transportation/Gas'),
    (['doctor','hospital','clinic','pharmacy','cvs','walgreens','medical','health','medicare'],     'Medicare/Medical'),
    (['church','ministry','offering','tithe','donation','pastor','mission'],                        'Ministry Expenses'),
    (['attorney','court','legal','notary','abogado','tribunal','cesco','dtop','vitalchek'],         'Legal/Admin Fees'),
    (['amazon','walmart','target','paypal','online'],                                               'Personal/Misc'),
    (['rent','housing','apartment','hud','section8'],                                               'Rent (my portion)'),
    (['at&t','verizon','t-mobile','claro','liberty','internet','phone'],                            'Phone/Internet'),
    (['insurance','seguro','vehicle','auto'],                                                       'Vehicle Insurance'),
]


def categorize(description, merchant=''):
    text = (description + ' ' + merchant).lower()
    for keywords, category in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return category
    return 'Personal/Misc'


def pull_plaid_transactions(days_back=7):
    """Pull transactions from Plaid using plaid library."""
    try:
        from plaid import ApiClient, Configuration, Environment
        from plaid.apis import PlaidApi
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
    except ImportError:
        return None, "Plaid library not available"

    env_str = os.getenv('PLAID_ENV', 'production').lower()
    plaid_env = Environment.Production if env_str == 'production' else Environment.Sandbox

    cfg = Configuration(
        host=plaid_env,
        api_key={
            'clientId': os.getenv('PLAID_CLIENT_ID', ''),
            'secret':   os.getenv('PLAID_SECRET', ''),
        }
    )
    client = PlaidApi(ApiClient(cfg))

    tokens = {
        'Fifth Third':   os.getenv('FIFTH_THIRD_ACCESS_TOKEN', ''),
        'Banco Popular': os.getenv('BANCO_POPULAR_ACCESS_TOKEN', ''),
    }

    end_date   = date.today()
    start_date = end_date - timedelta(days=days_back)
    all_txns   = []

    for bank, token in tokens.items():
        if not token:
            continue
        try:
            resp = client.transactions_get(TransactionsGetRequest(
                access_token=token,
                start_date=start_date,
                end_date=end_date,
            ))
            for txn in resp.transactions:
                all_txns.append({
                    'bank':        bank,
                    'date':        str(txn.date),
                    'description': txn.name or '',
                    'merchant':    txn.merchant_name or '',
                    'amount':      abs(float(txn.amount)),
                    'category_plaid': txn.category[0] if txn.category else '',
                    'category':    categorize(txn.name or '', txn.merchant_name or ''),
                    'pending':     txn.pending,
                    'transaction_id': txn.transaction_id,
                })
        except Exception as e:
            return None, str(e)[:200]

    return all_txns, None


def log_to_sheet(transactions):
    """Append new transactions to the Budget Sheet Expense Log."""
    if not transactions:
        return 0
    rows = []
    for t in transactions:
        if not t.get('pending'):
            rows.append([
                t['date'], t['description'], t['category'],
                t['amount'], 'Card', t['bank'], t.get('merchant','')
            ])
    if not rows:
        return 0
    subprocess.run(
        [sys.executable, GWS_SCRIPT, 'sheets', 'append',
         BUDGET_SHEET_ID, "'Expense Log'!A1", '--values', json.dumps(rows)],
        capture_output=True, timeout=20
    )
    return len(rows)


def push_to_actual_budget(transactions):
    """Push confirmed transactions to Actual Budget via actualpy, skipping duplicates."""
    try:
        from actual import Actual
        from actual.queries import get_accounts, get_transactions, create_transaction
    except ImportError:
        print("actualpy not installed — skipping Actual Budget push")
        return

    password = os.getenv('ACTUAL_PASSWORD', '')
    if not password:
        print("ACTUAL_PASSWORD not set — skipping Actual Budget push")
        return

    if not transactions:
        print("Actual Budget: no transactions to push.")
        return

    account_name_map = {
        'Fifth Third':   'Fifth Third Bank',
        'Banco Popular': 'Banco Popular',
    }

    try:
        with Actual(base_url='http://localhost:5006', password=password,
                    file='CCN Personal Budget') as actual:
            accounts_list = get_accounts(actual.session)

            def find_account(target_name):
                for acct in accounts_list:
                    if target_name.lower() in (acct.name or '').lower():
                        return acct
                return None

            existing  = get_transactions(actual.session)
            seen_ids  = {t.notes for t in existing if t.notes}

            imported = 0
            for t in transactions:
                if t['transaction_id'] in seen_ids:
                    continue

                target_name = account_name_map.get(t['bank'])
                if not target_name:
                    continue
                account = find_account(target_name)
                if account is None:
                    continue

                txn_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                payee    = t.get('merchant') or t.get('description', '')[:50]
                amount   = -abs(t['amount'])

                create_transaction(
                    actual.session,
                    date=txn_date,
                    account=account,
                    payee=payee,
                    notes=t['transaction_id'],
                    amount=amount,
                )
                imported += 1

            actual.commit()

        print(f"Actual Budget: {imported} transactions imported.")
    except Exception as e:
        print(f"Actual Budget push failed: {e}")


def main():
    args     = sys.argv[1:]
    days_back = 7
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            days_back = int(args[idx + 1])

    today = date.today().isoformat()
    print(f"Plaid sync starting — pulling last {days_back} days...")

    txns, err = pull_plaid_transactions(days_back)

    if err:
        print(f"Plaid sync error: {err}\nCheck credentials and try again.")
        return

    if txns is None:
        print("No transactions returned.")
        return

    # Save to staging file
    STAGING_FILE.write_text(json.dumps(txns, indent=2))

    # Filter non-pending
    confirmed = [t for t in txns if not t.get('pending')]
    pending   = [t for t in txns if t.get('pending')]

    # Log to Google Sheet
    logged = log_to_sheet(confirmed)

    # Build summary
    fifth_count  = sum(1 for t in confirmed if t['bank'] == 'Fifth Third')
    banco_count  = sum(1 for t in confirmed if t['bank'] == 'Banco Popular')
    total        = len(confirmed)

    largest = max(confirmed, key=lambda x: x['amount']) if confirmed else None

    by_cat = {}
    for t in confirmed:
        by_cat[t['category']] = by_cat.get(t['category'], 0) + t['amount']

    lines = [
        f'BANK SYNC COMPLETE — {today}',
        f'Fifth Third: {fifth_count} new transactions',
        f'Banco Popular: {banco_count} new transactions',
        f'Total imported: {total} | Pending: {len(pending)}',
    ]
    if largest:
        lines.append(f'Largest: ${largest["amount"]:.2f} — {largest["description"][:30]} ({largest["category"]})')
    if by_cat:
        lines.append('')
        lines.append('By category:')
        for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1])[:5]:
            lines.append(f'  {cat}: ${amt:.2f}')
    lines += [
        '',
        'Review in Actual Budget: localhost:5006',
        '(SSH tunnel: ssh -L 5006:localhost:5006 root@[vps-ip])',
        f'Also logged to Budget Sheet expense tab.',
    ]
    print('\n'.join(lines))

    push_to_actual_budget(confirmed)


if __name__ == '__main__':
    main()
