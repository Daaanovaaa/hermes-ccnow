# Hermes Life Admin Layer

Built: 2026-05-20  
Profile: leeegaaal@gmail.com (Google Drive + Gmail)

This layer monitors and manages the administrative infrastructure that protects
Carlos's housing, food assistance, healthcare, and legal standing.

---

## Components

### Component 1 — Document Vault Monitor (`doc_vault_monitor.py`)
Scans leeegaaal Google Drive for life-critical documents across 7 categories.
- Categories: Section 8, SNAP/PAN, Medicare, Bankruptcy, Credit History, Vehicle, Legal
- Alerts via Telegram when new documents are detected in Drive
- Weekly alert if critical categories remain empty
- Run: `python3 doc_vault_monitor.py` (cron: daily 9 AM AST)
- Status: `python3 doc_vault_monitor.py --status`
- Config: `doc_vault_index.json`

### Component 2 — Correspondence Tracker (`correspondence_tracker.py`)
Monitors leeegaaal Gmail for life-admin keyword emails.
- Keywords: Section 8, HUD, SNAP, PAN, Medicare, bankruptcy, Chapter 7, Marggie, Rodriguez, legal services
- Immediate alert on new matching email
- Weekly Monday 8 AM AST summary of pending correspondence
- Run scan: `python3 correspondence_tracker.py --scan` (cron: every 2 hours)
- Run weekly: `python3 correspondence_tracker.py --weekly` (cron: Monday 12 UTC)
- Mark replied: `python3 correspondence_tracker.py --mark-replied "subject fragment"`
- State: `correspondence_state.json`

### Component 3 — Landlord Labor Exchange Log (`labor_exchange_add.py`)
Tracks labor performed in exchange for rent consideration / Section 8 inspection prep.
- Telegram command: tell Hermes "Log labor: [description], [hours], [value], [Section8_inspection or general]"
- Hermes calls: `python3 labor_exchange_add.py --add --who Carlos --description "..." --hours 2 --value 100 --related Section8_inspection`
- List: `python3 labor_exchange_add.py --list`
- Summary: `python3 labor_exchange_add.py --summary`
- Data: `labor_exchange.json`

### Component 4 — Bankruptcy Case File (`bankruptcy_case.md`)
Structured case file for Chapter 7 pro bono filing.
- Attorney: Marggie Rodriguez, Mayagüez PR
- Tracks document checklist, timeline, and next actions
- Update manually as case progresses
- Related court notice: MZ2026MU01480

---

## Cron Jobs (register in Hermes)

| Name | Schedule | Script | Mode |
|---|---|---|---|
| life-admin-doc-vault | 0 13 * * * (9 AM AST) | doc_vault_monitor.py | no_agent |
| life-admin-correspondence-scan | 0 */2 * * * (every 2h) | correspondence_tracker.py --scan | no_agent |
| life-admin-correspondence-weekly | 0 12 * * 1 (Mon 8 AM AST) | correspondence_tracker.py --weekly | no_agent |

All three deliver to Telegram chat 1401562511.
