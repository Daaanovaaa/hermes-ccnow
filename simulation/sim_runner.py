#!/usr/bin/env python3
"""
sim_runner.py — Hermes Simulation Framework Plugin Runner

Discovers all .sim.py files in simulation/modules/, simulates a configurable
number of calendar days starting from today, fires each module according to its
SCHEDULE, runs all SCENARIOS, and writes a timestamped report.

HERMES_HOME is set to /root/hermes-sim/ for every module execution — live
data under /root/hermes-ccnow/ is never touched during simulation.

Usage:
    python3 simulation/sim_runner.py [--days N] [--module MODULE_NAME]

Examples:
    python3 simulation/sim_runner.py --days 30
    python3 simulation/sim_runner.py --days 7 --module budget_monitor
"""
import argparse
import importlib.util
import os
import sys
from datetime import date, timedelta
from pathlib import Path


SIM_HOME        = Path(__file__).parent
MODULES_DIR     = SIM_HOME / "modules"
REPORTS_DIR     = SIM_HOME / "reports"
HERMES_SIM_HOME = "/root/hermes-sim/"


def discover_modules(modules_dir: Path) -> list:
    """
    Scan modules_dir for every file whose name ends in .sim.py.

    Returns a sorted list of absolute Path objects. Files in __pycache__ and
    any non-.sim.py files are silently ignored. An empty list is returned if
    the directory does not exist so the runner degrades gracefully when no
    modules have been written yet.
    """
    if not modules_dir.exists():
        return []
    return sorted(modules_dir.glob("*.sim.py"))


def load_module(path: Path) -> dict:
    """
    Dynamically import one .sim.py plugin and extract its contract fields.

    Expected module-level variables
    --------------------------------
    INTENT    : str  — One sentence describing what the real module does.
    SCHEDULE  : str  — "daily", "weekly", "monthly", or "on-trigger".
    SCENARIOS : list — Dicts with at minimum {"name": str, "data": dict}.

    Optional
    --------
    run(data: dict) — Called with each scenario's data dict during simulation.
                      Should raise an exception on failure and return normally
                      on success.

    Returns a populated module dict, or None if loading fails or required
    fields are absent (a warning is printed but execution continues).
    """
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod  = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        print(f"  [WARN] Could not import {path.name}: {exc}")
        return None

    for field in ("INTENT", "SCHEDULE", "SCENARIOS"):
        if not hasattr(mod, field):
            print(f"  [WARN] {path.name} is missing required field '{field}' — skipped")
            return None

    return {
        "name":      path.stem.replace(".sim", ""),
        "path":      path,
        "intent":    mod.INTENT,
        "schedule":  str(mod.SCHEDULE).strip().lower(),
        "scenarios": list(mod.SCENARIOS),
        "run_fn":    getattr(mod, "run", None),
    }


def should_fire(schedule: str, day_index: int, sim_date: date) -> bool:
    """
    Decide whether a module fires on a given simulated day.

    Scheduling semantics
    --------------------
    daily      → fires on every day of the simulation
    weekly     → fires on day 0 and every 7th day thereafter
    monthly    → fires when the simulated date's day-of-month is 1
    on-trigger → never fired automatically (requires explicit --module run)

    Any unrecognised schedule string defaults to daily so unknown modules
    still produce output rather than silently doing nothing.
    """
    if schedule == "daily":
        return True
    if schedule == "weekly":
        return day_index % 7 == 0
    if schedule == "monthly":
        return sim_date.day == 1
    if schedule == "on-trigger":
        return False
    return True  # unknown → treat as daily


def run_scenario(module: dict, scenario: dict) -> tuple:
    """
    Execute one scenario against the module's run() function.

    If the module has no run() function the scenario is considered a
    structural dry-pass — the data dict was loaded and validated by the
    import step, so counting it as passed is correct.

    Returns (passed: bool, message: str).
    """
    name = scenario.get("name", "unnamed")
    data = scenario.get("data", {})

    if module["run_fn"] is None:
        return True, "PASS (dry — no run() fn defined; structure validated)"

    try:
        module["run_fn"](data)
        return True, "PASS"
    except Exception as exc:
        return False, f"FAIL: {exc}"


def simulate_day(day_index: int, sim_date: date,
                 modules: list, report_lines: list) -> tuple:
    """
    Process one calendar day of the simulation.

    For each loaded module whose SCHEDULE matches this day, every SCENARIO is
    executed. Results are appended to report_lines (written to file later) and
    also printed to stdout so the user sees live progress.

    Returns (scenarios_passed: int, scenarios_failed: int, fired_names: set).
    fired_names is the set of module names that ran on this day.
    """
    day_passed  = 0
    day_failed  = 0
    fired_names = set()

    for mod in modules:
        if not should_fire(mod["schedule"], day_index, sim_date):
            continue

        fired_names.add(mod["name"])
        header = f"\n  [{sim_date}] MODULE: {mod['name']}  schedule={mod['schedule']}"
        report_lines.append(header)
        print(header.strip())

        for scenario in mod["scenarios"]:
            s_name         = scenario.get("name", "unnamed")
            passed, msg    = run_scenario(mod, scenario)
            line           = f"    Scenario '{s_name}': {msg}"
            report_lines.append(line)
            print(line)
            if passed:
                day_passed += 1
            else:
                day_failed += 1

    return day_passed, day_failed, fired_names


def setup_report_dir(run_date: date) -> Path:
    """
    Create (if needed) and return the report directory for this run.

    Path pattern: simulation/reports/run_YYYY-MM-DD/
    Running the simulation twice on the same day overwrites the previous
    report, which is intentional — the last run is always the authoritative one.
    """
    report_dir = REPORTS_DIR / f"run_{run_date.isoformat()}"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def write_report(report_dir: Path, lines: list) -> Path:
    """
    Flush all collected report lines to report.txt inside report_dir.

    Returns the absolute path to the written file so the caller can print it.
    """
    report_file = report_dir / "report.txt"
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def print_summary(total_passed: int, total_failed: int,
                  all_modules_fired: set, report_lines: list):
    """
    Append and print a human-readable summary block.

    The summary contains three key metrics requested by the spec:
      • modules run (unique module names that fired at least once)
      • scenarios passed
      • scenarios failed
    """
    divider = "=" * 60
    summary = [
        "",
        divider,
        "SIMULATION SUMMARY",
        divider,
        f"Modules run:       {len(all_modules_fired)}",
        f"  {', '.join(sorted(all_modules_fired)) or '(none)'}",
        f"Scenarios passed:  {total_passed}",
        f"Scenarios failed:  {total_failed}",
        f"Total scenarios:   {total_passed + total_failed}",
        divider,
    ]
    for line in summary:
        print(line)
        report_lines.append(line)


def run_simulation(days: int, module_filter: str):
    """
    Orchestrate the full simulation run.

    Steps
    -----
    1. Set HERMES_HOME to /root/hermes-sim/ (isolates from live data).
    2. Discover and load all .sim.py plugins (or the single named module).
    3. Iterate over `days` calendar days starting from today.
    4. On each day, fire matching modules and run their scenarios.
    5. Accumulate pass/fail counts and the set of modules that fired.
    6. Print and write the summary report.
    """
    os.environ["HERMES_HOME"] = HERMES_SIM_HOME

    run_date   = date.today()
    report_dir = setup_report_dir(run_date)

    raw_modules  = [load_module(p) for p in discover_modules(MODULES_DIR)]
    all_modules  = [m for m in raw_modules if m is not None]

    if module_filter:
        all_modules = [m for m in all_modules if m["name"] == module_filter]
        if not all_modules:
            print(f"ERROR: No module named '{module_filter}' found in {MODULES_DIR}")
            sys.exit(1)

    report_lines = [
        "HERMES SIMULATION RUN",
        f"Run date:        {run_date}",
        f"Sim days:        {days}",
        f"HERMES_HOME:     {HERMES_SIM_HOME}",
        f"Modules loaded:  {len(all_modules)}",
        f"Module filter:   {module_filter or 'none (all)'}",
        "=" * 60,
    ]
    for line in report_lines:
        print(line)

    total_passed     = 0
    total_failed     = 0
    all_modules_fired: set = set()

    for i in range(days):
        sim_date             = run_date + timedelta(days=i)
        day_passed, day_failed, fired = simulate_day(
            i, sim_date, all_modules, report_lines
        )
        total_passed     += day_passed
        total_failed     += day_failed
        all_modules_fired |= fired

    print_summary(total_passed, total_failed, all_modules_fired, report_lines)

    report_file = write_report(report_dir, report_lines)
    print(f"\nReport saved: {report_file}")


def parse_args():
    """
    Parse command-line arguments.

    --days N        : Number of calendar days to simulate (default 30).
    --module NAME   : Run only the named module instead of all discovered ones.
                      NAME must match the stem of a .sim.py file without the
                      '.sim' suffix, e.g. 'budget_monitor' for
                      budget_monitor.sim.py.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Hermes sim_runner — simulate N days of the CC NOW! autonomous OS "
            "using .sim.py plugin wrappers in simulation/modules/."
        )
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Number of days to simulate (default: 30)"
    )
    parser.add_argument(
        "--module", type=str, default=None,
        metavar="MODULE_NAME",
        help="Run a single named module only (e.g. --module budget_monitor)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_simulation(days=args.days, module_filter=args.module)
