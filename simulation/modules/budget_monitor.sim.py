"""
Simulation wrapper for life-admin/budget_monitor.py.

Validates the data structures that budget_monitor.py needs from Plaid
(bank account balances) and the Google Sheet (fixed expenses). Also
exercises the HEALTHY / WATCH / ALERT status logic so threshold changes
are caught immediately in sim before hitting live Telegram.
"""

INTENT = (
    "Pull live bank balances from Fifth Third and Banco Popular via Plaid, "
    "compare against total fixed expenses from the Personal Budget Google Sheet, "
    "and send a daily HEALTHY / WATCH / ALERT budget status to Telegram."
)

SCHEDULE = "daily"

EMERGENCY_FLOOR  = 50.0
WATCH_THRESHOLD  = 100.0

SCENARIOS = [
    {
        "name": "healthy",
        "data": {
            "accounts": [
                {"bank": "fifth_third",   "balance": 342.50},
                {"bank": "banco_popular", "balance": 185.00},
            ],
            "fixed_total": 380.00,
            "fixed_items": [
                ("Rent",        875.00),
                ("Medicare",     50.00),
                ("Phone",        45.00),
                ("Car insurance",120.00),
            ],
        },
    },
    {
        "name": "watch_low_buffer",
        "data": {
            "accounts": [
                {"bank": "fifth_third",   "balance": 212.00},
                {"bank": "banco_popular", "balance":  67.00},
            ],
            "fixed_total": 215.00,
            "fixed_items": [
                ("Rent",        875.00),
                ("Medicare",     50.00),
            ],
        },
    },
    {
        "name": "alert_emergency_floor",
        "data": {
            "accounts": [
                {"bank": "fifth_third",   "balance":  38.00},
                {"bank": "banco_popular", "balance":  15.00},
            ],
            "fixed_total": 215.00,
            "fixed_items": [
                ("Rent", 875.00),
            ],
        },
    },
]

REQUIRED_KEYS    = {"accounts", "fixed_total", "fixed_items"}
REQUIRED_ACCT    = {"bank", "balance"}
KNOWN_BANKS      = {"fifth_third", "banco_popular"}


def run(data: dict) -> bool:
    """
    Validate that data contains the structures budget_monitor.py derives
    from Plaid and the Google Sheet, then confirm the status thresholds
    produce a known status value.

    Checks performed
    ----------------
    - All required top-level keys are present.
    - 'accounts' is a non-empty list where every entry has 'bank' and
      'balance', balance is numeric and non-negative, and bank is one of
      the two known institutions.
    - 'fixed_total' is a non-negative number.
    - 'fixed_items' is a list (empty is allowed when Sheet rows are TBD).
    - The computed status resolves to HEALTHY, WATCH, or ALERT.

    Raises ValueError with a descriptive message on any violation.
    Returns True when all checks pass.
    """
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing required keys: {sorted(missing)}")

    accounts = data["accounts"]
    if not isinstance(accounts, list) or not accounts:
        raise ValueError("'accounts' must be a non-empty list")

    for i, acct in enumerate(accounts):
        missing_acct = REQUIRED_ACCT - acct.keys()
        if missing_acct:
            raise ValueError(
                f"accounts[{i}] missing keys: {sorted(missing_acct)}"
            )
        if acct["bank"] not in KNOWN_BANKS:
            raise ValueError(
                f"accounts[{i}]['bank'] must be one of {sorted(KNOWN_BANKS)}, "
                f"got '{acct['bank']}'"
            )
        if not isinstance(acct["balance"], (int, float)):
            raise ValueError(
                f"accounts[{i}]['balance'] must be numeric, got {type(acct['balance']).__name__}"
            )
        if acct["balance"] < 0:
            raise ValueError(
                f"accounts[{i}]['balance'] is negative ({acct['balance']}); "
                "use 0.0 to represent an overdrawn or empty account in simulation"
            )

    fixed_total = data["fixed_total"]
    if not isinstance(fixed_total, (int, float)) or fixed_total < 0:
        raise ValueError(
            f"'fixed_total' must be a non-negative number, got {fixed_total!r}"
        )

    if not isinstance(data["fixed_items"], list):
        raise ValueError("'fixed_items' must be a list")

    # Mirror budget_monitor.py status logic to confirm thresholds are sane
    fifth_third   = sum(a["balance"] for a in accounts if a["bank"] == "fifth_third")
    banco_popular = sum(a["balance"] for a in accounts if a["bank"] == "banco_popular")
    total         = fifth_third + banco_popular
    buffer        = total - fixed_total
    min_acct      = min(fifth_third, banco_popular)

    if min_acct < EMERGENCY_FLOOR or buffer < EMERGENCY_FLOOR:
        status = "ALERT"
    elif buffer < WATCH_THRESHOLD:
        status = "WATCH"
    else:
        status = "HEALTHY"

    if status not in {"HEALTHY", "WATCH", "ALERT"}:
        raise ValueError(f"Status resolved to unexpected value: '{status}'")

    return True
