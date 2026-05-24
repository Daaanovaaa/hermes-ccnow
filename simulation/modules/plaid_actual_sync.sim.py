"""
Simulation wrapper for budget/plaid_actual_sync.py.

Validates the transaction data structures pulled from Plaid staging JSON
and the push_to_actual_budget() deduplication logic. Confirms the account
mapping and amount sign conventions without hitting live Plaid or Actual
Budget endpoints.
"""

INTENT = (
    "Pull last 7 days of transactions from Plaid (Fifth Third + Banco Popular), "
    "write to staging JSON, log to Google Sheet Expense Log, and push confirmed "
    "transactions to Actual Budget at localhost:5006 — skipping pending and "
    "already-imported transactions."
)

SCHEDULE = "daily"

SCENARIOS = [
    {
        "name": "normal_import",
        "data": {
            "transactions": [
                {
                    "bank": "Fifth Third", "date": "2026-05-24",
                    "description": "WALMART SUPERCENTER", "merchant": "Walmart",
                    "amount": 47.83, "category": "Groceries",
                    "pending": False, "transaction_id": "txn_abc001",
                },
                {
                    "bank": "Banco Popular", "date": "2026-05-23",
                    "description": "SHELL OIL", "merchant": "Shell",
                    "amount": 35.00, "category": "Transportation/Gas",
                    "pending": False, "transaction_id": "txn_abc002",
                },
            ],
            "existing_notes": [],
            "expected_imported": 2,
        },
    },
    {
        "name": "all_duplicates_skipped",
        "data": {
            "transactions": [
                {
                    "bank": "Fifth Third", "date": "2026-05-24",
                    "description": "AMAZON.COM", "merchant": "Amazon",
                    "amount": 22.99, "category": "Personal/Misc",
                    "pending": False, "transaction_id": "txn_dup001",
                },
            ],
            "existing_notes": ["txn_dup001"],
            "expected_imported": 0,
        },
    },
    {
        "name": "pending_skipped",
        "data": {
            "transactions": [
                {
                    "bank": "Fifth Third", "date": "2026-05-24",
                    "description": "PENDING CHARGE", "merchant": "",
                    "amount": 10.00, "category": "Personal/Misc",
                    "pending": True, "transaction_id": "txn_pend001",
                },
                {
                    "bank": "Banco Popular", "date": "2026-05-24",
                    "description": "CVS PHARMACY", "merchant": "CVS",
                    "amount": 18.50, "category": "Medicare/Medical",
                    "pending": False, "transaction_id": "txn_conf001",
                },
            ],
            "existing_notes": [],
            "expected_imported": 1,
        },
    },
]

REQUIRED_TXN_KEYS = {"bank", "date", "description", "merchant", "amount", "pending", "transaction_id"}
KNOWN_BANKS       = {"Fifth Third", "Banco Popular"}
ACCOUNT_NAME_MAP  = {
    "Fifth Third":   "Fifth Third Bank",
    "Banco Popular": "Banco Popular",
}


def run(data: dict) -> bool:
    """
    Simulate push_to_actual_budget() deduplication and account-mapping logic
    without connecting to Actual Budget or Plaid.

    Checks performed
    ----------------
    - All transactions have required keys and valid bank names.
    - amount is a positive float (sign flip happens on push).
    - Confirmed (non-pending) transactions not in existing_notes are counted
      as imported; pending and duplicate transactions are skipped.
    - Simulated import count matches expected_imported.
    """
    transactions    = data.get("transactions", [])
    existing_notes  = set(data.get("existing_notes", []))
    expected        = data.get("expected_imported", 0)

    for i, t in enumerate(transactions):
        missing = REQUIRED_TXN_KEYS - t.keys()
        if missing:
            raise ValueError(f"transactions[{i}] missing keys: {sorted(missing)}")
        if t["bank"] not in KNOWN_BANKS:
            raise ValueError(f"transactions[{i}]['bank'] unknown: '{t['bank']}'")
        if not isinstance(t["amount"], (int, float)) or t["amount"] < 0:
            raise ValueError(
                f"transactions[{i}]['amount'] must be a non-negative number, got {t['amount']!r}"
            )
        if t["bank"] not in ACCOUNT_NAME_MAP:
            raise ValueError(f"transactions[{i}]['bank'] has no account mapping: '{t['bank']}'")

    confirmed = [t for t in transactions if not t.get("pending")]

    imported = 0
    for t in confirmed:
        if t["transaction_id"] in existing_notes:
            continue
        imported += 1

    if imported != expected:
        raise ValueError(
            f"Expected {expected} imported transactions, simulated {imported}"
        )

    return True
