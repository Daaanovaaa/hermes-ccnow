#!/usr/bin/env python3
"""
CC NOW! Daily Automation — Hermes morning run
Reads the live Google Sheet product brain and Drive asset inboxes, delivers
rotating promos for all 7 revenue streams via Telegram, then writes back
status to the sheet.
Runs at 9:00 AM AST (13:00 UTC) daily via Hermes cron job a10f101bb3e7.
"""
import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta

SHEET_ID        = '16Hhs7DgOCrQe2BdVrfG2q-j5bBkyzQQEOlnOFfekZso'
DRIVE_PARENT_ID = '1CbYt3WCayOKBqVHlklNNpdi4KN6aS88K'
GWS_SCRIPT      = '/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py'
BALANCE_SCRIPT  = '/root/Hetzner/CC_NOW/automation/scripts/get_balances.py'
HERMES_PYTHON   = '/usr/local/lib/hermes-agent/venv/bin/python3'
PROMO_BASE      = '/root/Hetzner/CC_NOW/automation/promotions'
SALES_FILE      = '/root/Hetzner/CC_NOW/sales/daily.csv'
LOG_DIR         = '/root/Hetzner/CC_NOW/automation/logs'
STATE_FILE      = '/root/Hetzner/CC_NOW/automation/state.json'
FULKRUM_TARGET  = 500.00

# Maps sheet Category (col B, lowercase) → internal filesystem key.
# Display labels are built live from sheet columns B + C — never hardcoded here.
CATEGORY_MAP = {
    'book':     'book',
    'merch':    'merch',
    'music':    'music',
    'concert':  'concert',
    'magazine': 'magazine',
    'youtube':  'youtube',
    'radio':    'radio',
}

# Maps Drive inbox folder number prefix → filesystem key
# (folder names like "01_BOOK_...", "02_MERCH_..." match sheet row numbers)
INBOX_PREFIX_MAP = {1: 'book', 2: 'merch', 3: 'music', 4: 'concert',
                    5: 'magazine', 6: 'youtube', 7: 'radio'}

# Fallback URLs used when sheet's Online Store URL column (I) is empty
FALLBACK_URLS = {
    'book':     'https://www.amazon.com/gp/aw/d/B0DBLW3JG7',
    'merch':    'https://conscious-culture-now.myspreadshop.com',
    'music':    'https://push.fm/fl/MzC7Tf4k',
    'concert':  '',
    'magazine': 'https://docs.google.com/document/d/1W-tq6VKogA4oa7xymQ7PL9JiMzeqNUGWpC0hISg71j4',
    'youtube':  'https://www.youtube.com/@DominaloConCRISTO',
    'radio':    'https://consciousculturenow.gumroad.com/l/subscription',
}

# Sheet column indices (0-based), header row excluded
COL = {
    'num':           0,   # A
    'category':      1,   # B
    'name':          2,   # C
    'description':   3,   # D
    'price':         4,   # E
    'rev_target':    5,   # F
    'units_sold':    6,   # G
    'revenue':       7,   # H
    'store_url':     8,   # I
    'platform':      9,   # J
    'backup_url':    10,  # K
    'assets_loaded': 15,  # P
    'promo_status':  17,  # R
    'last_action':   23,  # X
    'next_target':   24,  # Y
    'notes':         25,  # Z
}

os.makedirs(LOG_DIR, exist_ok=True)


def gws(args):
    """Run google_api.py with given args, return parsed JSON or None on error."""
    try:
        result = subprocess.run(
            [sys.executable, GWS_SCRIPT] + args,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def read_sheet():
    """Fetch all product rows from the sheet. Returns list of row dicts."""
    raw = gws(['sheets', 'get', SHEET_ID, 'A2:Z8'])
    if not raw:
        return None

    rows = []
    for row in raw:
        def col(idx):
            return row[idx].strip() if idx < len(row) and row[idx] else ''

        category = col(COL['category']).lower()
        if category not in CATEGORY_MAP:
            continue

        key       = CATEGORY_MAP[category]
        # Label is built from live sheet data so corrections in col C flow through
        name      = col(COL['name']) or category.upper()
        label     = f"{category.upper()} — {name}"
        store_url = col(COL['store_url']) or FALLBACK_URLS.get(key, '')

        rows.append({
            'row_num':       int(col(COL['num']) or 0),
            'key':           key,
            'label':         label,
            'name':          name,
            'price':         col(COL['price']),
            'rev_target':    col(COL['rev_target']),
            'units_sold':    col(COL['units_sold']),
            'revenue':       col(COL['revenue']),
            'store_url':     store_url,
            'assets_loaded': col(COL['assets_loaded']),
            'promo_status':  col(COL['promo_status']),
            'notes':         col(COL['notes']),
        })
    return rows


def check_drive_inboxes():
    """Check each numbered inbox folder for loaded assets.
    Returns dict: key → {'folder_name': str, 'file_count': int, 'files': list}
    Returns None if Drive is unreachable.
    Two API calls: one to list folders, one bulk file search across all inboxes.
    """
    # Step 1: get all subfolders of the parent CC NOW! folder
    folders_raw = gws([
        'drive', 'search', '--raw-query',
        f"'{DRIVE_PARENT_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    ])
    if folders_raw is None:
        return None

    # Build folder_id → key mapping from numeric prefix
    folder_id_to_key = {}
    key_to_folder    = {}
    for folder in folders_raw:
        name = folder.get('name', '')
        fid  = folder.get('id', '')
        parts = name.split('_')
        try:
            prefix = int(parts[0])
        except (ValueError, IndexError):
            continue
        key = INBOX_PREFIX_MAP.get(prefix)
        if key:
            folder_id_to_key[fid] = key
            key_to_folder[key]    = {'folder_name': name, 'folder_id': fid,
                                     'file_count': 0, 'files': []}

    if not folder_id_to_key:
        return {}

    # Step 2: single bulk search for all files across all inbox folders
    parent_clauses = ' or '.join(f"'{fid}' in parents" for fid in folder_id_to_key)
    files_raw = gws([
        'drive', 'search', '--raw-query',
        f"({parent_clauses}) and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
        '--max', '100'
    ])

    # Distribute file counts — Drive search doesn't return parent IDs in results,
    # so we do a lightweight per-folder count only for folders that returned files.
    # We know total file count per folder after this step via individual checks.
    # Trade-off: if bulk search returns files, run individual folder counts.
    if files_raw:
        for fid, key in folder_id_to_key.items():
            folder_files = gws([
                'drive', 'search', '--raw-query',
                f"'{fid}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                '--max', '20'
            ]) or []
            key_to_folder[key]['file_count'] = len(folder_files)
            key_to_folder[key]['files']      = [f['name'] for f in folder_files[:5]]

    return key_to_folder


def write_back(rows, promos, drive_data, timestamp, tomorrow):
    """Write Last Action and Next Target Date back to sheet for all product rows."""
    values = []
    for row in rows:
        key   = row['key']
        promo = promos.get(key, '')
        di    = (drive_data or {}).get(key, {})
        fc    = di.get('file_count', 0)

        if promo:
            action = f"Promo deployed {timestamp}: {promo[:80]}..."
        else:
            action = "No promo — sequence missing"

        if fc:
            action += f" | Drive inbox: {fc} file(s) detected"

        values.append([action, tomorrow])

    if not values:
        return

    gws([
        'sheets', 'update', SHEET_ID, f"X2:Y{1 + len(values)}",
        '--values', json.dumps(values)
    ])


def get_bank_balances():
    """Fetch live bank balances via Plaid using the Hermes venv Python.
    Returns dict with total_primary and account list, or None on failure."""
    try:
        result = subprocess.run(
            [HERMES_PYTHON, BALANCE_SCRIPT],
            capture_output=True, text=True, timeout=35
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if not data.get('error'):
                return data
    except Exception:
        pass
    return None


def format_financials(bank_data, sheet_rows):
    """Build financial header from live bank balances + sheet monthly revenue.
    Bank balance and CC NOW! monthly revenue are distinct metrics — Fulkrum exit
    threshold fires only on monthly CC NOW! revenue, not bank balance.
    """
    lines = []

    # Bank balance — current position
    if bank_data:
        total = bank_data.get('total_primary', 0)
        lines.append(f"Bank balance: ${total:,.2f} (Fifth Third + Banco Popular)")

    # CC NOW! monthly revenue — from sheet cols G + H
    monthly_rev = None
    if sheet_rows:
        total_rev = 0.0
        has_rev   = False
        for row in sheet_rows:
            try:
                total_rev += float(row['revenue'])
                has_rev = True
            except (ValueError, TypeError):
                pass
        if has_rev:
            monthly_rev = total_rev
            lines.append(f"CC NOW! revenue this month: ${total_rev:,.2f}")

    # Fulkrum Studios exit threshold — based on monthly CC NOW! revenue
    if monthly_rev is not None:
        if monthly_rev >= FULKRUM_TARGET:
            lines.append(f"FULKRUM EXIT THRESHOLD REACHED — ${monthly_rev:,.2f}/mo >= ${FULKRUM_TARGET:.0f} obligation")
        else:
            pct = (monthly_rev / FULKRUM_TARGET) * 100
            lines.append(f"Fulkrum: {pct:.0f}% — ${monthly_rev:.0f}/${FULKRUM_TARGET:.0f}/mo (${FULKRUM_TARGET - monthly_rev:.0f} to exit)")
    else:
        lines.append(f"Fulkrum exit: enter monthly revenue in sheet to monitor ${FULKRUM_TARGET:.0f}/mo threshold")

    return lines


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_next_promo(key, state):
    seq_path = os.path.join(PROMO_BASE, key, 'sequence.txt')
    if not os.path.exists(seq_path):
        return None, state
    with open(seq_path, 'r') as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        return None, state
    idx = state.get(key, 0)
    promo = lines[idx % len(lines)]
    state[key] = (idx + 1) % len(lines)
    return promo, state


def count_sales():
    if not os.path.exists(SALES_FILE):
        return 0
    with open(SALES_FILE, 'r') as f:
        lines = [ln for ln in f if ln.strip()]
    return max(0, len(lines) - 1)


def format_revenue(rows):
    """Build a revenue summary line from sheet data if any values exist."""
    total_units = 0
    total_rev   = 0.0
    has_data    = False
    for row in rows:
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
    if not has_data:
        return None
    return f"Units sold this month: {total_units} | Revenue: ${total_rev:,.2f}"


def main():
    now       = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y-%m-%d %H:%M UTC')
    date_str  = now.strftime('%Y%m%d')
    tomorrow  = (now + timedelta(days=1)).strftime('%Y-%m-%d')

    # --- Read product brain ---
    sheet_rows = read_sheet()
    sheet_ok   = sheet_rows is not None

    if sheet_ok:
        product_keys = [r['key'] for r in sheet_rows]
        sheet_by_key = {r['key']: r for r in sheet_rows}
    else:
        product_keys = list(CATEGORY_MAP.keys())
        sheet_by_key = {}

    # --- Check Drive asset inboxes ---
    drive_data = check_drive_inboxes()
    drive_ok   = drive_data is not None

    # --- Bank balances (Plaid, non-blocking) ---
    bank_data = get_bank_balances()

    # --- Promotional sequences ---
    state  = load_state()
    promos = {}
    for key in product_keys:
        promo, state = get_next_promo(key, state)
        promos[key] = promo
    save_state(state)

    # --- Sales count (local CSV) ---
    csv_sales = count_sales()

    # --- Build Telegram message ---
    lines = ["CC NOW! DAILY RUN"]
    lines.append(f"Date: {timestamp}")

    fin_lines = format_financials(bank_data, sheet_rows if sheet_ok else None)
    if fin_lines:
        lines += fin_lines
    elif not sheet_ok:
        lines.append(f"CSV sales logged: {csv_sales} | Sheet: offline — using local data")

    lines += ["", "TODAY'S PROMOTIONAL QUEUE", "─" * 33]

    action_needed = []
    new_assets    = []

    for key in product_keys:
        row   = sheet_by_key.get(key, {})
        label = row.get('label') or key.upper()
        promo = promos.get(key)
        di    = (drive_data or {}).get(key, {})
        fc    = di.get('file_count', 0)
        fnames = di.get('files', [])

        sheet_assets = row.get('assets_loaded', '').lower()
        has_assets   = fc > 0  # Drive is the ground truth for asset presence

        lines.append(f"\n{label}")

        # Drive inbox status line
        if drive_ok:
            if fc > 0:
                preview = ', '.join(fnames[:3]) + (f' +{fc - 3} more' if fc > 3 else '')
                lines.append(f"Drive inbox: {fc} file(s) — {preview}")
                # Flag if Drive has files but sheet column P hasn't been marked
                if sheet_assets in ('no', ''):
                    new_assets.append(label.split(' — ')[0])
            else:
                lines.append("Drive inbox: empty")

        if promo:
            lines.append(promo)
        else:
            lines.append("[Sequence missing — add content to sequence.txt]")

        # Alert only when Drive confirms inbox is actually empty
        if drive_ok and not has_assets:
            action_needed.append(f"ASSETS NEEDED: {label.split(' — ')[0]} — inbox is empty")
        elif not drive_ok and sheet_assets in ('no', ''):
            # Drive offline — fall back to sheet column P
            action_needed.append(f"ASSETS NEEDED: {label.split(' — ')[0]}")

    # Alerts section
    if new_assets or action_needed:
        lines += ["", "ACTION NEEDED", "─" * 33]
        for item in new_assets:
            lines.append(f"NEW ASSETS DETECTED: {item} — update column P in sheet")
        for item in action_needed:
            lines.append(item)

    lines += [
        "",
        "─" * 33,
        "Conscious Culture NOW! | El Pabellon de Victoria",
    ]

    message = "\n".join(lines)

    # --- Write back to sheet ---
    if sheet_ok:
        write_back(sheet_rows, promos, drive_data, timestamp, tomorrow)

    # --- Activity log ---
    drive_summary = {k: v['file_count'] for k, v in (drive_data or {}).items()}
    log_entry = (
        f"{timestamp} | sheet={'ok' if sheet_ok else 'offline'}"
        f" | drive={'ok' if drive_ok else 'offline'}"
        f" | csv_sales={csv_sales}"
        f" | drive_files={drive_summary}"
        f" | promos=" + ",".join(f"{k}={'ok' if promos.get(k) else 'MISSING'}" for k in product_keys)
    )
    log_file = os.path.join(LOG_DIR, f"activity_{date_str}.log")
    with open(log_file, 'a') as f:
        f.write(log_entry + '\n')

    print(message)


if __name__ == '__main__':
    main()
