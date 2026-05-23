# Hermes Simulation Framework

## What This Is

The simulation framework lets you validate every Hermes automation module
against realistic scenarios without touching live data. Each real module gets a
thin `.sim.py` wrapper that declares what the module does (`INTENT`), when it
runs (`SCHEDULE`), and a set of test cases (`SCENARIOS`). `sim_runner.py`
discovers all wrappers automatically, walks through a configurable number of
simulated calendar days, fires each module on the right cadence, and writes a
timestamped pass/fail report — giving Carlos and future agents a fast,
repeatable way to confirm the autonomous OS is healthy before any change goes
live.

---

## How To Run

```bash
# Simulate the default 30 days across all discovered modules
python3 simulation/sim_runner.py --days 30

# Simulate 7 days for a single module only
python3 simulation/sim_runner.py --days 7 --module budget_monitor
```

Reports are written to `simulation/reports/run_YYYY-MM-DD/report.txt`.

---

## How To Add A New Module

Create `simulation/modules/<module_name>.sim.py` in the **same session** you
build the real module. The runner auto-discovers it — no registration needed.

**Template** (`simulation/modules/budget_monitor.sim.py`):

```python
"""
Sim wrapper for life-admin/budget_monitor.py.
Validates daily Telegram budget alert under normal and overdraft conditions.
"""
import sys, os
sys.path.insert(0, os.path.join(os.environ.get("HERMES_HOME", "/root/hermes-sim/"),
                                "../hermes-ccnow"))
from life_admin import budget_monitor  # import the real module

INTENT = "Send a daily Telegram alert showing envelope balances vs. targets."

SCHEDULE = "daily"

SCENARIOS = [
    {
        "name": "normal",
        "data": {
            "groceries_balance": 180.00,
            "groceries_target":  200.00,
            "gas_balance":        45.00,
            "gas_target":         60.00,
        },
    },
    {
        "name": "overdraft",
        "data": {
            "groceries_balance": -15.00,
            "groceries_target":  200.00,
            "gas_balance":         0.00,
            "gas_target":          60.00,
        },
    },
    {
        "name": "zero_balances",
        "data": {
            "groceries_balance": 0.00,
            "groceries_target":  200.00,
            "gas_balance":       0.00,
            "gas_target":        60.00,
        },
    },
]


def run(data: dict):
    """
    Called by sim_runner for each scenario. Raise an exception to fail.
    Must complete without error for a scenario to be counted as PASS.
    """
    budget_monitor.validate_balances(data)
```

> **Rule**: Create the `.sim.py` wrapper in the same build session as the real
> module. Never leave a module unwrapped.

---

## Module Schedule Types

| Schedule | Fires when | Typical use |
|---|---|---|
| `daily` | Every simulated day | Morning alerts, balance checks |
| `weekly` | Every 7th day (day 0, 7, 14 …) | IPO research, weekly reviews |
| `monthly` | When simulated date's day-of-month = 1 | Monthly reports, renewals |
| `on-trigger` | Never automatically — manual `--module` only | Webhook handlers, one-off jobs |

---

## Safety Rules

- **Always** set `HERMES_HOME=/root/hermes-sim/` — `sim_runner.py` does this
  automatically; your `run()` function must respect it.
- **Never** hardcode `/root/hermes-ccnow/` paths inside a `.sim.py` file.
  Use `os.environ["HERMES_HOME"]` for all file references.
- **Never** use the live Telegram bot token. Set
  `TELEGRAM_BOT_TOKEN=USE_TEST_BOT_NOT_LIVE` in your test environment or mock
  the send call entirely.
- **Never** call Plaid, NASDAQ, or any paid external API inside a sim scenario.
  Use fixture data in the `data` dict instead.
- If a scenario must write a file, write it under `HERMES_HOME` — never under
  the live repo or live log directories.

---

## Current Modules

These four `.sim.py` wrappers will be built in the next session:

| Module | Real file | Schedule |
|---|---|---|
| `reality_checkin` | `life-reality/reality_checkin.py` | daily |
| `budget_monitor` | `life-admin/budget_monitor.py` | daily |
| `obligations_tracker` | `life-reality/obligations_tracker.py` | daily |
| `prayer_finance_engine` | `prayer-finance/prayer_finance_engine.py` | weekly |
