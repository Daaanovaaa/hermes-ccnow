"""
Simulation wrapper for prayer-finance/prayer_finance_engine.py.

Validates both data paths the engine touches each week:
  1. IPO cache (ipo_cache.json) — candidates fed to --shortlist and --recommend
  2. Log entry (prayer_finance_log.json) — written by --confirm after Carlos buys

Three scenarios cover the full weekly cycle: strong IPO week (Friday
shortlist fires), empty IPO week (hold-seed fallback), and a confirmed
seed purchase (Carlos replies with Fidelity confirmation number).
"""

INTENT = (
    "Run the weekly kingdom seed investment cycle: Friday IPO research and "
    "Telegram shortlist, Saturday PW-ID recommendation, log Carlos's Fidelity "
    "confirmation, and generate Sunday journal entry — all for a $1 fractional "
    "seed investment covered in prayer."
)

SCHEDULE = "weekly"

# Mirror scoring constants from prayer_finance_engine.py
SCORE_LABELS = [
    (8.0, "STRONG SEED"),
    (6.0, "GOOD SEED"),
    (4.0, "WATCH"),
    (0.0, "PASS"),
]

REQUIRED_CANDIDATE_KEYS = {
    "ticker", "company", "ipo_date", "price_range", "sector",
    "fractional_eligible", "stability_score", "mission_score",
    "momentum_score", "rationale",
}

REQUIRED_LOG_KEYS = {
    "date", "ticker", "pw_id", "confirmation_number",
    "amount", "status", "platform", "journal_entry",
}

SCENARIOS = [
    {
        "name": "strong_ipo_candidates",
        "data": {
            "candidates": [
                {
                    "ticker":             "KVYO",
                    "company":            "Klaviyo Inc",
                    "ipo_date":           "2026-05-30",
                    "price_range":        "$14.00-$16.00",
                    "price_mid":          15.0,
                    "exchange":           "NYSE",
                    "sector":             "Technology",
                    "fractional_eligible": True,
                    "stability_score":    7,
                    "mission_score":      7,
                    "momentum_score":     8,
                    "rationale": (
                        "NYSE IPO at $14-16, Fidelity fractional eligible. "
                        "Tight price spread signals strong institutional demand. "
                        "Kingdom seed opportunity."
                    ),
                },
                {
                    "ticker":             "HLTH",
                    "company":            "HealthStream Partners",
                    "ipo_date":           "2026-06-02",
                    "price_range":        "$10.00-$12.00",
                    "price_mid":          11.0,
                    "exchange":           "NASDAQ",
                    "sector":             "Healthcare",
                    "fractional_eligible": True,
                    "stability_score":    8,
                    "mission_score":      8,
                    "momentum_score":     7,
                    "rationale": (
                        "NASDAQ healthcare IPO under $12. High mission alignment. "
                        "Fidelity fractional eligible. Kingdom seed opportunity."
                    ),
                },
            ],
            "research_date": "2026-05-23",
            "candidate_count": 2,
        },
    },
    {
        "name": "no_ipo_hold_seed",
        "data": {
            "candidates":      [],
            "research_date":   "2026-05-30",
            "candidate_count": 0,
        },
    },
    {
        "name": "seed_confirmed",
        "data": {
            "log_entry": {
                "date":                "2026-05-24",
                "ticker":              "KVYO",
                "pw_id":               "PW-20260524-KVYO",
                "confirmation_number": "FID7842931",
                "amount":              1.00,
                "status":              "EXECUTED",
                "platform":            "Fidelity",
                "journal_entry":       "",
            },
        },
    },
]


def _score_ipo(c: dict) -> float:
    """Mirror of prayer_finance_engine.score_ipo() for threshold validation."""
    return (
        c.get("stability_score", 5)  * 0.25
        + c.get("mission_score", 5)  * 0.25
        + (10 if c.get("fractional_eligible") else 3) * 0.20
        + c.get("momentum_score", 5) * 0.30
    )


def _get_score_label(score: float) -> str:
    """Mirror of prayer_finance_engine.get_score_label()."""
    for threshold, label in SCORE_LABELS:
        if score >= threshold:
            return label
    return "PASS"


def _validate_candidate(c: dict, index: int):
    """
    Validate one IPO candidate dict against the fields required by
    score_ipo(), format_shortlist(), and format_recommendation().
    Raises ValueError on any violation.
    """
    missing = REQUIRED_CANDIDATE_KEYS - c.keys()
    if missing:
        raise ValueError(
            f"candidates[{index}] missing required keys: {sorted(missing)}"
        )

    if not isinstance(c["ticker"], str) or not c["ticker"].strip():
        raise ValueError(f"candidates[{index}]['ticker'] must be a non-empty string")

    if not isinstance(c["company"], str) or not c["company"].strip():
        raise ValueError(f"candidates[{index}]['company'] must be a non-empty string")

    try:
        from datetime import date as _date
        _date.fromisoformat(c["ipo_date"])
    except (ValueError, TypeError):
        raise ValueError(
            f"candidates[{index}]['ipo_date'] '{c['ipo_date']}' is not a valid ISO date"
        )

    if not isinstance(c["price_range"], str) or not c["price_range"].startswith("$"):
        raise ValueError(
            f"candidates[{index}]['price_range'] must be a '$'-prefixed string, "
            f"got '{c['price_range']}'"
        )

    if not isinstance(c["fractional_eligible"], bool):
        raise ValueError(
            f"candidates[{index}]['fractional_eligible'] must be bool, "
            f"got {type(c['fractional_eligible']).__name__}"
        )

    for score_key in ("stability_score", "mission_score", "momentum_score"):
        val = c[score_key]
        if not isinstance(val, (int, float)) or not (0 <= val <= 10):
            raise ValueError(
                f"candidates[{index}]['{score_key}'] must be a number in [0, 10], got {val!r}"
            )

    composite = _score_ipo(c)
    label = _get_score_label(composite)
    if label not in {"STRONG SEED", "GOOD SEED", "WATCH", "PASS"}:
        raise ValueError(
            f"candidates[{index}] composite score {composite:.2f} resolved to "
            f"unexpected label '{label}'"
        )


def _validate_log_entry(entry: dict):
    """
    Validate a log entry dict against the fields written by cmd_confirm()
    and read by append_csv().
    Raises ValueError on any violation.
    """
    missing = REQUIRED_LOG_KEYS - entry.keys()
    if missing:
        raise ValueError(f"log_entry missing required keys: {sorted(missing)}")

    try:
        from datetime import date as _date
        _date.fromisoformat(entry["date"])
    except (ValueError, TypeError):
        raise ValueError(f"log_entry['date'] '{entry['date']}' is not a valid ISO date")

    if not isinstance(entry["ticker"], str) or not entry["ticker"].isupper():
        raise ValueError(
            f"log_entry['ticker'] must be an uppercase string, got '{entry['ticker']}'"
        )

    pw_id = entry["pw_id"]
    parts = str(pw_id).split("-")
    if len(parts) != 3 or parts[0] != "PW" or not parts[1].isdigit() or len(parts[1]) != 8:
        raise ValueError(
            f"log_entry['pw_id'] '{pw_id}' must match format PW-YYYYMMDD-TICKER"
        )

    conf = entry["confirmation_number"]
    if not isinstance(conf, str) or not conf.strip():
        raise ValueError("log_entry['confirmation_number'] must be a non-empty string")

    if not isinstance(entry["amount"], (int, float)) or entry["amount"] <= 0:
        raise ValueError(
            f"log_entry['amount'] must be a positive number, got {entry['amount']!r}"
        )

    if entry["status"] != "EXECUTED":
        raise ValueError(
            f"log_entry['status'] must be 'EXECUTED', got '{entry['status']}'"
        )

    if not isinstance(entry["platform"], str) or not entry["platform"].strip():
        raise ValueError("log_entry['platform'] must be a non-empty string")

    if not isinstance(entry["journal_entry"], str):
        raise ValueError("log_entry['journal_entry'] must be a string (empty is allowed)")


def run(data: dict) -> bool:
    """
    Dispatch to the appropriate validator based on which data path the
    scenario covers.

    If data contains 'candidates' — validates the IPO cache structure used
    by --shortlist and --recommend. An empty candidates list is valid (hold-
    seed week). Each candidate is checked against the fields required by
    score_ipo(), format_shortlist(), and format_recommendation().

    If data contains 'log_entry' — validates the entry dict written by
    --confirm to prayer_finance_log.json and prayer_finance_log.csv.

    Raises ValueError with a descriptive message on any violation.
    Returns True when all checks pass.
    """
    if "candidates" in data:
        candidates = data["candidates"]
        if not isinstance(candidates, list):
            raise ValueError("'candidates' must be a list")

        research_date = data.get("research_date", "")
        if not isinstance(research_date, str) or not research_date:
            raise ValueError("'research_date' must be a non-empty ISO date string")
        try:
            from datetime import date as _date
            _date.fromisoformat(research_date)
        except ValueError:
            raise ValueError(
                f"'research_date' '{research_date}' is not a valid ISO date"
            )

        count = data.get("candidate_count")
        if not isinstance(count, int) or count < 0:
            raise ValueError(
                f"'candidate_count' must be a non-negative integer, got {count!r}"
            )
        if count != len(candidates):
            raise ValueError(
                f"'candidate_count' ({count}) does not match len(candidates) ({len(candidates)})"
            )

        for i, c in enumerate(candidates):
            _validate_candidate(c, i)

        return True

    if "log_entry" in data:
        _validate_log_entry(data["log_entry"])
        return True

    raise ValueError(
        "data must contain either 'candidates' (IPO cache path) "
        "or 'log_entry' (confirmation path)"
    )
