"""
Simulation wrapper for life-reality/reality_checkin.py.

Validates the data that reality_checkin.py records when Carlos responds
to a daily Telegram check-in prompt. Covers the --record path because
that is where the critical data contract lives: block name, completion
status, interruption reason, and notes all feed into checkin_log.csv
and downstream pattern learning.
"""

INTENT = (
    "Send Carlos 4 daily Telegram check-ins reviewing his FUNNY/MONEY/HONEY/"
    "SPIRIT/HERMES time blocks and log his YES/PARTIAL/NO responses to build "
    "an honest picture of daily execution."
)

SCHEDULE = "daily"

SCENARIOS = [
    {
        "name": "normal",
        "data": {
            "block":                "afternoon",
            "completed":            "yes",
            "interruption_reason":  "",
            "notes":                "CC NOW! deep work block protected. Rap session fire.",
            "utc_hour":             12,
        },
    },
    {
        "name": "missed_obligations_warning",
        "data": {
            "block":                "evening",
            "completed":            "partial",
            "interruption_reason":  "Section 8 recertification call ran 3 hours",
            "notes":                "Admin batch skipped. Sales outreach missed. Obligations took the afternoon.",
            "utc_hour":             18,
        },
    },
    {
        "name": "crisis_keyword_trigger",
        "data": {
            "block":                "night",
            "completed":            "no",
            "interruption_reason":  "URGENT — landlord posted lockout notice on door",
            "notes":                "CRISIS: legal response needed before 9 AM. threshold_monitor should have caught this.",
            "utc_hour":             22,
        },
    },
]

VALID_BLOCKS    = {"morning", "afternoon", "evening", "night"}
VALID_COMPLETED = {"yes", "partial", "no"}
VALID_UTC_HOURS = {5, 12, 18, 22}
REQUIRED_KEYS   = {"block", "completed", "interruption_reason", "notes", "utc_hour"}


def run(data: dict) -> bool:
    """
    Validate that data contains all keys reality_checkin.py needs to log a
    --record entry and generate a check-in for the correct block.

    Checks performed
    ----------------
    - All required keys are present.
    - 'block' is one of the four named time blocks.
    - 'completed' is one of yes / partial / no.
    - 'interruption_reason' and 'notes' are strings (empty is allowed).
    - 'utc_hour' is one of the four cron-mapped hours (5, 12, 18, 22).

    Raises ValueError with a descriptive message on any violation.
    Returns True when all checks pass.
    """
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing required keys: {sorted(missing)}")

    if not isinstance(data["block"], str) or not data["block"]:
        raise ValueError("'block' must be a non-empty string")
    if data["block"] not in VALID_BLOCKS:
        raise ValueError(
            f"'block' must be one of {sorted(VALID_BLOCKS)}, got '{data['block']}'"
        )

    if not isinstance(data["completed"], str) or not data["completed"]:
        raise ValueError("'completed' must be a non-empty string")
    if data["completed"] not in VALID_COMPLETED:
        raise ValueError(
            f"'completed' must be one of {sorted(VALID_COMPLETED)}, got '{data['completed']}'"
        )

    if not isinstance(data["interruption_reason"], str):
        raise ValueError("'interruption_reason' must be a string (empty is allowed)")

    if not isinstance(data["notes"], str):
        raise ValueError("'notes' must be a string (empty is allowed)")

    if not isinstance(data["utc_hour"], int) or data["utc_hour"] not in VALID_UTC_HOURS:
        raise ValueError(
            f"'utc_hour' must be one of {sorted(VALID_UTC_HOURS)}, got '{data['utc_hour']}'"
        )

    return True
