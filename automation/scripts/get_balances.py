#!/usr/bin/env python3
"""
Plaid balance fetcher — run with Hermes venv Python.
Returns JSON for daily_run.py to consume.
Called as: /usr/local/lib/hermes-agent/venv/bin/python3 get_balances.py
"""
import os, json, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.home() / '.hermes' / '.env')

try:
    from plaid import ApiClient, Configuration, Environment
    from plaid.apis import PlaidApi
    from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
except ImportError:
    print(json.dumps({'error': 'plaid library not available'}))
    sys.exit(0)

PLAID_ENV_STR = os.getenv('PLAID_ENV', 'sandbox').lower()
PLAID_ENV     = Environment.Production if PLAID_ENV_STR == 'production' else Environment.Sandbox

cfg = Configuration(
    host=PLAID_ENV,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID', ''),
        'secret':   os.getenv('PLAID_SECRET', ''),
    }
)
client = PlaidApi(ApiClient(cfg))

BANK_TOKENS = {
    'fifth_third':   os.getenv('FIFTH_THIRD_ACCESS_TOKEN', ''),
    'banco_popular': os.getenv('BANCO_POPULAR_ACCESS_TOKEN', ''),
}

# Accounts to include in the "available balance" summary
PRIMARY_ACCOUNTS = {'Primary', 'e-account'}

result   = {'accounts': [], 'total_primary': 0.0, 'error': None}
total    = 0.0

for bank, token in BANK_TOKENS.items():
    if not token:
        continue
    try:
        resp = client.accounts_balance_get(AccountsBalanceGetRequest(access_token=token))
        for a in resp.accounts:
            balance = a.balances.current or 0
            entry   = {
                'bank':     bank,
                'name':     a.name,
                'balance':  balance,
                'currency': a.balances.iso_currency_code or 'USD',
                'primary':  a.name in PRIMARY_ACCOUNTS,
            }
            result['accounts'].append(entry)
            if entry['primary']:
                total += balance
    except Exception as e:
        result['error'] = str(e)[:200]

result['total_primary'] = round(total, 2)
print(json.dumps(result))
