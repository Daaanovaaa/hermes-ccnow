---
name: cc_now_sales_automation
description: Automates marketing and sales tracking for Conscious Culture NOW! book, merchandise, and music sales
version: 1.0
author: Hermes Agent
---

# CC NOW! Sales Automation Skill

This skill automates the marketing and sales tracking for Conscious Culture NOW! book, merchandise, music, and other revenue streams. It runs autonomous promotional sequences, monitors sales data via Google Sheet, and provides regular updates to the user. The Google Sheet is the product brain and numbered Google Drive folders are the asset inboxes - together forming the business operating system.

## Triggers
- Designed to be run daily via cron job at 9:00 AM local Puerto Rico time (before morning rap block)
- Upon new sale detection (if webhook or file-based system configured)
- Weekly on Sundays for performance review

## Tools Required
- terminal: For running scripts and checking file systems
- file: For reading/writing sales logs and promotional content
- send_message: For delivering updates via Telegram
- execute_code: For processing sales data and generating reports
- google-workspace: For accessing Google Sheet (product brain) and Google Drive (asset inboxes)

## Setup Instructions
1. Ensure the Google Sheet "CC NOW Store Sheet" is accessible and lists your sellable items with online locations (this is the product brain)
2. Place promotional content templates in `/root/Hetzner/CC_NOW/automation/promotions/` (mirrored to Google Drive)
3. Populate the sequential inbox folders (`01_BOOK_...`, `02_MERCH_...`, etc.) in Google Drive under the CC_NOW folder with the corresponding assets (PDFs, images, audio, copy, etc.) - these are the asset inboxes
4. Configure any external store webhooks to POST JSON to a local endpoint (future enhancement)
5. The VPS mirror system exists as a backup sync layer but follows Google Drive (not the reverse)

## Autonomous Actions

### Daily Marketing Sequence
At 9:00 AM each day, the skill:
1. Checks for new sales since last run
2. Selects next promotional message from sequence
3. Logs promotional activity
4. Sends a brief update to user via Telegram

### Sales Monitoring
Continuously monitors:
- `/root/Hetzner/CC_NOW/sales/daily.csv` for new entries
- Any JSON webhook payloads in `/root/Hetzner/CC_NOW/sales/webhooks/`
- Updates running totals and revenue tracking

### Weekly Review
Every Sunday at 8:00 PM:
1. Compiles weekly sales report
2. Calculates ROI on time invested
3. Suggests next promotional focus
4. Sends comprehensive summary to user

## Promotional Sequences
The skill maintains rotating sequences for:
- **Book promotions**: Highlight excerpts, reviews, bundle offers
- **Merchandise**: Product spotlights, limited-time discounts, customer photos
- **Music**: New release announcements, lyric videos, streaming milestones
- **Virtual Concert**: Ticket sales, early bird discounts, live stream reminders

## Error Handling
- If sales directory missing, creates it and logs warning
- If promotional sequence exhausted, restarts from beginning
- Network/store API failures are logged and retried with exponential backoff
- All errors reported in weekly summary

## Verification Steps
1. Check that skill runs at scheduled time (9:00 AM daily)
2. Verify promotional logs are written to `/root/Hetzner/CC_NOW/automation/logs/`
3. Confirm Telegram updates are received
4. Validate sales data accumulation in CSV files

## Execution via Cron Job
The skill is designed to be triggered by a cron job that runs the provided script `daily_run.py` from the `automation/scripts` directory. This ensures the promotional sequence rotates and sales are logged each day.
- Adjust the cron schedule to match your local time zone (Puerto Rico is AST, UTC-4). For example, to run at 9:00 AM local time, use `0 13 * * *` in UTC.
- The cron job should be configured with `no_agent=true` and the workdir set to the script directory.
- See the deployed cron job (ID: a10f101bb3e7) as an example.

## Reference Materials
- See `references/inbox_store_sheet_system.md` for detailed explanation of the sequential inbox and store sheet system.

## Reference Materials
- See `references/inbox_store_sheet_system.md` for detailed explanation of the sequential inbox and store sheet system.

## Future Enhancements
- Integrate with PayPal/Stripe APIs for real-time sales tracking
- Add Facebook/Instagram automated posting
- Implement email marketing sequences via SMTP
- Create dashboard for real-time sales visualization

## Q2 2026 Schedule Integration
The Google Sheet (product brain) and numbered Drive folders (asset inboxes) form the business operating system. The daily 9:00 AM cron job is the heartbeat that runs before your morning rap block, checking the Sheet and inboxes, executing the next promotional sequence, and delivering a Telegram summary by breakfast time. This aligns with your existing schedule: the 1:00–3:00 PM admin batch window is where you interact with the system—filling in real data, loading assets into correct folders, and signaling readiness. Hermes executes the rest autonomously.

## The Seven Revenue Streams and Their Cron Priorities
1. **Row 01 — Book on Amazon**: Superposition book. Begin autonomous marketing immediately once assets are loaded. Ready-to-sell inventory generating daily outreach.
2. **Row 02 — Merchandise**: Conscious Culture T‑Shirt. Same as book—autonomous promotion begins when photos and mockups are in the folder.
3. **Row 03 — Music**: La Historia Del Niño single on DistroKid/Spotify. Monitor streams, promote consistently, drive numbers toward monetization thresholds.
4. **Row 04 — Concert**: Monthly Virtual Rap Concert ticket at $25 per head. Recurring monthly campaign cycle. Every month has a concert; Hermes builds and executes a ticket sales sequence starting 3 weeks before the event date.
5. **Row 05 — Magazine**: La Fortaleza PR USA magazine Issue 1. Promote as both a publication and a copyright-protected concept vehicle. Distribute to Puerto Rican Protestant networks on and off the island on the USA.
6. **Row 06 — YouTube Membership**: CC NOW! Channel membership. Drive toward 1,000 subscribers for Google monetization. Consistent content publishing schedule required. Flag when crossing 500 and again at 1,000 subscribers.
7. **Row 07 — Radio Subscription**: THE 5:11 radio subscription at $1 plus bank fee. RACE(2)10k campaign. Target 10,000 subscribers. Treat subscriber growth as highest leverage activity after concert ticket sales.

## Rolling Rock Principle
You do not want to manage this manually. You want Hermes driving you with cron reminders, Telegram prompts, and automated sequences so the rock keeps rolling uphill even on days when your energy is low. Hermes is the momentum when you are tired. The structure is: Hermes runs overnight, you wake up to a summary, you do your creative work, you check in at the 1:00 PM admin window to load assets or approve actions, and Hermes executes the rest autonomously.

## Fulkrum Studios Flag
Monitor your performance revenue monthly. The moment concert ticket income, merch, and book sales cover your production needs, Hermes flags it and helps you prepare a clean exit from the $500 Fulkrum Studios obligation. That dependency should not linger longer than necessary.

## North Star Reminder
Every dollar this system generates is a brick toward El Pabellon de Victoria in Hormigueros. Keep that in the notes column of every product row as motivational context. We are not just selling tickets and t‑shirts—we are buying back a church and building a kingdom platform for the west coast of Puerto Rico.

---\n*Skill designed to fulfill the mandate: "Every admin task I touch is an opportunity to delegate it to you permanently."*\n
*Skill designed to fulfill the mandate: "Every admin task I touch is an opportunity to delegate it to you permanently."*