# Hetzner/ Directory Cleanup Report
Generated: 2026-05-22
Status: AWAITING CARLOS APPROVAL — do not delete until approved

---

## SUMMARY
The /root/Hetzner/ directory contains old files from early Hermes development.
Most are superseded by files in /root/hermes-ccnow/.
This report identifies what can be safely removed and what to keep.

**Awaiting approval to delete.** Nothing has been removed yet.

---

## FILE ANALYSIS

### DUPLICATE SCRIPTS (old versions superseded)

| File in Hetzner/ | Status | Matching file in hermes-ccnow/ | Recommendation |
|---|---|---|---|
| CC_NOW/automation/scripts/daily_run.py (64 lines) | OLD version | automation/scripts/daily_run.py (451 lines) | **DELETE** — old, cron was corrected to point at hermes-ccnow version |
| CC_NOW/automation/scripts/get_balances.py | IDENTICAL | automation/scripts/get_balances.py | DELETE — exact duplicate |
| CC_NOW/automation/scripts/hermes_calendar.py | IDENTICAL | automation/scripts/hermes_calendar.py | DELETE — exact duplicate |
| Google_Drive/CC_NOW/automation/scripts/daily_run.py | OLDEST version | automation/scripts/daily_run.py | DELETE — oldest draft |

### DUPLICATE DATA FILES

| File in Hetzner/ | Recommendation | Reason |
|---|---|---|
| CC_NOW/automation/state.json | KEEP | Active runtime state for promo sequencing |
| Google_Drive/CC_NOW/automation/state.json | DELETE | Duplicate of above |
| CC_NOW/sales/daily.csv | KEEP | Active sales log — fallback when Sheets offline |
| Google_Drive/CC_NOW/sales/daily.csv | DELETE | Exact duplicate |
| CC_NOW/store_sheet.csv | KEEP | Local mirror of Google Sheet |
| Google_Drive/CC_NOW/store_sheet.csv | DELETE | Exact duplicate |

### DUPLICATE PROMOTION SEQUENCES

| Path | Recommendation |
|---|---|
| CC_NOW/automation/promotions/ (7 subdirs) | KEEP — this is what the active cron reads |
| Google_Drive/CC_NOW/automation/promotions/ (partial, 5 of 7) | DELETE — incomplete copy, active cron uses CC_NOW/ |

### PRAYER MINISTRY FILES (3 copies exist)

| File | Recommendation |
|---|---|
| prayer_ministries.json (root) | KEEP — likely the authoritative copy |
| Google_Drive/prayer_ministries.json | DELETE — duplicate |
| Roxsanna_Nivar/prayer_ministries/ (folder) | KEEP — Roxsanna-specific version, different context |
| Google_Drive/Roxsanna_Nivar/prayer_ministries/ | DELETE — duplicate of above |

### EMAIL DRAFT ARTIFACTS

| File | Recommendation | Reason |
|---|---|---|
| Nathan_Bortz/nathan_reply_may15_2026.txt | ARCHIVE | Email already sent; keep for records |
| Nathan_Bortz/reply_to_nathan_may15.txt | DELETE | Draft superseded by final_reply_to_nathan.txt |
| Nathan_Bortz/workflow_expectations_email.txt | ARCHIVE | Keep for reference |
| Nathan_Bortz/final_reply_to_nathan.txt | KEEP | Final sent version |
| Nathan_Bortz/WORKFLOW_TRACKING.md | ARCHIVE | Historical tracking |
| Roxsanna_Nivar/initial_proposal_email.txt | ARCHIVE | Sent email, keep for records |
| Roxsanna_Nivar/reply_email.txt | ARCHIVE | Sent reply |
| Roxsanna_Nivar/email_followup_spiritual_firewall_spanish.txt | ARCHIVE | Sent |
| Roxsanna_Nivar/email_sequential_workflow_spanish.txt | KEEP | Active SOP |
| Google_Drive/Roxsanna_Nivar/email_sequential_workflow_spanish.txt | DELETE | Duplicate |
| Roxsanna_Nivar/WORKFLOW_TRACKING.md | KEEP | Active tracking |
| Google_Drive/Roxsanna_Nivar/WORKFLOW_TRACKING.md | DELETE | Duplicate |

### DUPLICATE PASTOR TRACKER DIRECTORIES (naming artifacts)

| Directory | Recommendation |
|---|---|
| DaNova_Pastor_Carlos_Schedule/ | DELETE — empty except one tracker MD |
| Pastor_Carlos_DaNova_Villanueva/ | KEEP — has Activity_Tracking_Log + DaNova_Daily_Tracker + Financial_Tracker |
| "Pastor: Carlos M.C. DaNova..." (special chars) | DELETE — artifact with same file as above |

### ACTIVITY LOGS (keep for now)

| File | Recommendation |
|---|---|
| CC_NOW/automation/logs/activity_*.log | KEEP for 90 days — operational history |
| Google_Drive/CC_NOW/automation/logs/activity_20260516.log | DELETE — single old partial copy |

### MISCELLANEOUS

| File | Recommendation |
|---|---|
| CC_NOW/sync_test.txt | DELETE — test artifact |
| Hetzner/sync_gdrive.sh | REVIEW — may still be needed for Google Drive sync |
| test_email_to_faaaithmusicmovies_spanish.txt | DELETE — test email |
| CC_NOW/accountability/memory_log.csv | KEEP — accountability history |
| CC_NOW/accountability/record_accountability.py | REVIEW — check if still called anywhere |

---

## DELETION SUMMARY (pending approval)

**SAFE TO DELETE (duplicates/artifacts):**
- Google_Drive/CC_NOW/ (entire folder except prayer_ministries.json)
- Hetzner/CC_NOW/automation/scripts/get_balances.py (duplicate)
- Hetzner/CC_NOW/automation/scripts/hermes_calendar.py (duplicate)
- Hetzner/CC_NOW/automation/scripts/daily_run.py (old 64-line version)
- DaNova_Pastor_Carlos_Schedule/ (directory)
- "Pastor: Carlos..." directory (special chars artifact)
- sync_test.txt
- test_email_to_faaaithmusicmovies_spanish.txt
- Nathan_Bortz/reply_to_nathan_may15.txt (superseded draft)
- Google_Drive/Roxsanna_Nivar/WORKFLOW_TRACKING.md (duplicate)
- Google_Drive/Roxsanna_Nivar/email_sequential_workflow_spanish.txt (duplicate)

**ESTIMATED CLEANUP:** ~15-20 files removed, ~5 directories removed.
No active data or operational scripts would be lost.

---

## NEXT STEP
Reply with: "Execute Hetzner cleanup" and Hermes will delete only the items marked
DELETE in this report. Or review and modify the list first.
