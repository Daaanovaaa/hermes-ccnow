#!/usr/bin/env python3
"""
CC NOW! Sunday Review — weekly performance report
Runs every Sunday at 8 PM AST via Hermes cron.
Delivers 7-product report, accountability summary, and Fulkrum Studios flag.
"""
import os
import sys
import json
import subprocess
from datetime import datetime, timezone, date, timedelta

SHEET_ID   = '16Hhs7DgOCrQe2BdVrfG2q-j5bBkyzQQEOlnOFfekZso'
GWS_SCRIPT = '/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
LOG_DIR    = '/root/Hetzner/CC_NOW/automation/logs'
ACCT_SCRIPT = '/root/Hetzner/CC_NOW/accountability/record_accountability.py'

# Fulkrum Studios monthly obligation
FULKRUM_MONTHLY = 500.00

# Product priority labels for report
PRODUCT_PRIORITY = {
    'book':     'URGENT',
    'merch':    'URGENT',
    'music':    'ACTIVE',
    'concert':  'URGENT',
    'magazine': 'ACTIVE',
    'radio':    'BUILDING',
    'youtube':  'BUILDING',
}

CATEGORY_MAP = {
    'book': 'book', 'merch': 'merch', 'music': 'music',
    'concert': 'concert', 'magazine': 'magazine',
    'youtube': 'youtube', 'radio': 'radio',
}

COL = {
    'category': 1, 'name': 2, 'price': 4, 'rev_target': 5,
    'units_sold': 6, 'revenue': 7, 'store_url': 8,
    'assets_loaded': 15, 'promo_status': 17, 'notes': 25,
}

os.makedirs(LOG_DIR, exist_ok=True)


def gws(args):
    try:
        r = subprocess.run([sys.executable, GWS_SCRIPT] + args,
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception:
        pass
    return None


def read_sheet():
    raw = gws(['sheets', 'get', SHEET_ID, 'A2:Z8'])
    if not raw:
        return None
    rows = []
    for row in raw:
        def col(idx):
            return row[idx].strip() if idx < len(row) and row[idx] else ''
        cat = col(COL['category']).lower()
        if cat not in CATEGORY_MAP:
            continue
        rows.append({
            'key':          CATEGORY_MAP[cat],
            'name':         col(COL['name']) or cat.upper(),
            'price':        col(COL['price']),
            'rev_target':   col(COL['rev_target']),
            'units_sold':   col(COL['units_sold']),
            'revenue':      col(COL['revenue']),
            'store_url':    col(COL['store_url']),
            'assets_loaded':col(COL['assets_loaded']),
            'promo_status': col(COL['promo_status']),
            'notes':        col(COL['notes']),
        })
    return rows


def load_weekly_log():
    """Read activity logs from the past 7 days."""
    today  = date.today()
    entries = []
    for i in range(7):
        d = today - timedelta(days=i)
        f = os.path.join(LOG_DIR, f"activity_{d.strftime('%Y%m%d')}.log")
        if os.path.exists(f):
            with open(f) as fh:
                entries += fh.readlines()
    return entries


def load_accountability_report():
    """Get the 7-day accountability pattern report if available."""
    try:
        r = subprocess.run([sys.executable, ACCT_SCRIPT, 'report'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def fulkrum_check(total_revenue):
    """Check if monthly revenue covers the Fulkrum Studios $500 obligation."""
    if total_revenue <= 0:
        return None, False
    covered = total_revenue >= FULKRUM_MONTHLY
    pct     = (total_revenue / FULKRUM_MONTHLY) * 100
    return pct, covered


def main():
    now       = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y-%m-%d')
    week_end  = now.strftime('%Y-%m-%d')
    week_start = (now - timedelta(days=7)).strftime('%Y-%m-%d')

    sheet_rows = read_sheet()
    log_lines  = load_weekly_log()
    acct_report = load_accountability_report()

    # Revenue totals
    total_units = 0
    total_rev   = 0.0
    has_data    = False

    lines = [
        "CC NOW! WEEKLY REVIEW",
        f"Week: {week_start} → {week_end}",
        "=" * 40,
        "",
        "7-PRODUCT PERFORMANCE",
        "─" * 40,
    ]

    if sheet_rows:
        for row in sheet_rows:
            key      = row['key']
            priority = PRODUCT_PRIORITY.get(key, '')
            name     = row['name']
            units    = row['units_sold'] or '—'
            revenue  = row['revenue'] or '—'
            assets   = row['assets_loaded'] or 'No'
            target   = row['rev_target'] or 'TBD'

            try:
                total_units += int(row['units_sold'])
                has_data = True
            except (ValueError, TypeError):
                pass
            try:
                total_rev += float(row['revenue'])
                has_data = True
            except (ValueError, TypeError):
                pass

            lines.append(
                f"[{priority}] {name}\n"
                f"  Units: {units} | Revenue: ${revenue} | Target: ${target}\n"
                f"  Assets loaded: {assets}"
            )
    else:
        lines.append("Sheet offline — no product data available")

    # Revenue summary
    lines += ["", "─" * 40, "REVENUE SUMMARY"]
    if has_data:
        lines.append(f"Total units sold: {total_units}")
        lines.append(f"Total revenue:    ${total_rev:,.2f}")
    else:
        lines.append("No revenue data in sheet yet — update columns G and H")

    # Fulkrum Studios exit threshold
    lines += ["", "FULKRUM STUDIOS EXIT FLAG"]
    if has_data and total_rev > 0:
        pct, covered = fulkrum_check(total_rev)
        if covered:
            lines.append(
                f"EXIT THRESHOLD REACHED — ${total_rev:.2f} >= $500 monthly obligation. "
                f"Time to plan the Fulkrum Studios exit."
            )
        else:
            lines.append(
                f"${total_rev:.2f} of $500 monthly obligation covered ({pct:.0f}%). "
                f"${FULKRUM_MONTHLY - total_rev:.2f} remaining to exit threshold."
            )
    else:
        lines.append(
            f"Monitoring. Exit triggers when monthly revenue >= ${FULKRUM_MONTHLY:.0f}. "
            f"Threshold not reached — revenue data not yet entered in sheet."
        )

    # Automation health
    lines += ["", "AUTOMATION HEALTH"]
    lines.append(f"Cron runs logged this week: {len(log_lines)}")
    if log_lines:
        last = log_lines[-1].strip()[:120]
        lines.append(f"Last run: {last}")

    # Accountability summary
    if acct_report:
        lines += ["", "─" * 40, acct_report]

    lines += [
        "",
        "=" * 40,
        "North Star: El Pabellon de Victoria — Hormigueros, PR",
        "Proverbs 10:22 — The blessing of the LORD, it maketh rich.",
    ]

    print("\n".join(lines))


if __name__ == '__main__':
    main()
