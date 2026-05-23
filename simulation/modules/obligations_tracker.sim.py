"""
Simulation wrapper for life-reality/obligations_tracker.py.

Validates the structure of obligations.json entries that the tracker
reads to compute deadline alerts. Three scenarios cover the full
alert lifecycle: nothing due (silent), a 7-day threshold firing, and
an overdue obligation demanding immediate action.
"""

INTENT = (
    "Check government and civic deadlines (Section 8, SNAP, Medicare, vehicle) "
    "daily against ALERT_DAYS thresholds of 30/14/7/1 days and send a Telegram "
    "alert — or print [SILENT] if nothing is due within 30 days."
)

SCHEDULE = "daily"

ALERT_DAYS    = [30, 14, 7, 1]
DATE_SENTINEL = "YYYY-MM-DD"

SCENARIOS = [
    {
        "name": "all_clear_silent",
        "data": {
            "obligations": [
                {
                    "name":        "SNAP Renewal",
                    "category":    "benefits",
                    "due_date":    "2026-09-01",
                    "contact":     "ASES Mayagüez office",
                    "notes":       "Annual renewal — bring income docs",
                    "alert_sent":  {},
                },
                {
                    "name":        "Medicare Part B Premium",
                    "category":    "benefits",
                    "due_date":    "2026-08-15",
                    "contact":     "Social Security Administration",
                    "notes":       "",
                    "alert_sent":  {"30": "2026-07-16"},
                },
            ],
        },
    },
    {
        "name": "threshold_7day_alert",
        "data": {
            "obligations": [
                {
                    "name":           "Section 8 Recertification",
                    "category":       "housing_assistance",
                    "due_date":       "2026-05-30",
                    "what_to_bring":  "Income verification, government-issued ID, current lease copy",
                    "contact":        "HUD office Mayagüez — (787) 555-0100",
                    "notes":          "Critical — missing this deadline terminates housing assistance",
                    "alert_sent":     {"30": "2026-04-30", "14": "2026-05-16"},
                },
            ],
        },
    },
    {
        "name": "overdue_critical",
        "data": {
            "obligations": [
                {
                    "name":        "DTOP Lien Removal",
                    "category":    "vehicle",
                    "due_date":    "2026-05-20",
                    "contact":     "DTOP Mayagüez — visit in person",
                    "notes":       "Must clear lien before marbete renewal on JVL660",
                    "alert_sent":  {"30": "2026-04-20", "14": "2026-05-06", "7": "2026-05-13", "1": "2026-05-19"},
                },
                {
                    "name":        "FAFSA Balance Verification",
                    "category":    "education",
                    "due_date":    DATE_SENTINEL,
                    "notes":       "Check studentaid.gov — date TBD",
                    "alert_sent":  {},
                },
            ],
        },
    },
]

REQUIRED_OBL_KEYS = {"name", "category", "due_date"}
VALID_CATEGORIES  = {
    "housing_assistance", "benefits", "vehicle", "legal",
    "education", "health", "civic", "financial",
}


def run(data: dict) -> bool:
    """
    Validate that data contains a well-formed obligations list matching
    the schema that obligations_tracker.py reads from obligations.json.

    Checks performed
    ----------------
    - 'obligations' key is present and is a list.
    - Every obligation has 'name', 'category', and 'due_date'.
    - 'name' and 'category' are non-empty strings.
    - 'category' is one of the known civic/government categories.
    - 'due_date' is either the DATE_SENTINEL placeholder or a valid
      ISO-format date string (YYYY-MM-DD).
    - Optional string fields ('what_to_bring', 'contact', 'notes') are
      strings if present.
    - 'alert_sent', if present, is a dict whose keys are stringified
      threshold integers and values are ISO date strings.

    Raises ValueError with a descriptive message on any violation.
    Returns True when all checks pass.
    """
    if "obligations" not in data:
        raise ValueError("Missing required key: 'obligations'")

    obligations = data["obligations"]
    if not isinstance(obligations, list):
        raise ValueError("'obligations' must be a list")

    for i, obl in enumerate(obligations):
        missing = REQUIRED_OBL_KEYS - obl.keys()
        if missing:
            raise ValueError(
                f"obligations[{i}] missing required keys: {sorted(missing)}"
            )

        if not isinstance(obl["name"], str) or not obl["name"].strip():
            raise ValueError(f"obligations[{i}]['name'] must be a non-empty string")

        if not isinstance(obl["category"], str) or not obl["category"].strip():
            raise ValueError(f"obligations[{i}]['category'] must be a non-empty string")

        if obl["category"] not in VALID_CATEGORIES:
            raise ValueError(
                f"obligations[{i}]['category'] '{obl['category']}' not in known "
                f"categories: {sorted(VALID_CATEGORIES)}"
            )

        due = obl["due_date"]
        if not isinstance(due, str):
            raise ValueError(f"obligations[{i}]['due_date'] must be a string")
        if due != DATE_SENTINEL and "YYYY" not in due:
            try:
                from datetime import date as _date
                _date.fromisoformat(due)
            except ValueError:
                raise ValueError(
                    f"obligations[{i}]['due_date'] '{due}' is not a valid ISO date "
                    f"and not the sentinel '{DATE_SENTINEL}'"
                )

        for opt_key in ("what_to_bring", "contact", "notes"):
            if opt_key in obl and not isinstance(obl[opt_key], str):
                raise ValueError(
                    f"obligations[{i}]['{opt_key}'] must be a string, "
                    f"got {type(obl[opt_key]).__name__}"
                )

        alert_sent = obl.get("alert_sent", {})
        if not isinstance(alert_sent, dict):
            raise ValueError(f"obligations[{i}]['alert_sent'] must be a dict")
        for threshold_key, sent_date in alert_sent.items():
            if not str(threshold_key).isdigit():
                raise ValueError(
                    f"obligations[{i}]['alert_sent'] key '{threshold_key}' "
                    "must be a stringified integer threshold (e.g. '7', '30')"
                )
            try:
                from datetime import date as _date
                _date.fromisoformat(sent_date)
            except (ValueError, TypeError):
                raise ValueError(
                    f"obligations[{i}]['alert_sent']['{threshold_key}'] "
                    f"'{sent_date}' is not a valid ISO date"
                )

    return True
