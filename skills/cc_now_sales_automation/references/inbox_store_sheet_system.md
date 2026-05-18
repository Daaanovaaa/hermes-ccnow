# Sequential Inbox & Store Sheet System

## Overview
This system creates a clear, visual workflow for autonomous marketing and sales operations. The Google Sheet is the product brain and numbered Google Drive folders are the asset inboxes - together forming the business operating system. The user populates the store sheet with product information and loads assets into matching inbox folders. Hermes reads from the sheet and checks the inboxes to determine what to promote and execute autonomous marketing sequences.

## Source of Truth
- **Google Sheet**: "CC NOW Store Sheet" - the master inventory list and product brain
- **Google Drive Folder**: CC_NOW folder containing numbered inbox folders (01_BOOK_*, 02_MERCH_*, etc.) - the asset inboxes
- **VPS Mirror**: A backup sync layer that follows Google Drive (not the reverse)

## Folder Structure (Google Drive)
```
CC_NOW/
├── CC NOW Store Sheet             ← Master inventory list (Google Sheet)
├── sales/
│   └── daily.csv                  ← Sales log (append-only, mirrored to VPS)
├── automation/
│   ├── promotions/                ← Rotating message sequences (mirrored to VPS)
│   ├── logs/                      ← Daily activity logs (mirrored to VPS)
│   └── scripts/                   ← Automation scripts (mirrored to VPS)
└── inboxes/
    ├── 01_BOOK_<Item Name>        ← Assets for first item in store sheet
    ├── 02_MERCH_<Item Name>       ← Assets for second item
    ├── 03_MUSIC_<Item Name>       ← etc.
    └── ... (sequential numbering matches store sheet rows)
```

## VPS Mirror Structure (Backup)
```
/root/Hetzner/CC_NOW/
├── store_sheet.csv                ← Mirror of Google Sheet
├── sales/
│   └── daily.csv                  ← Mirror of sales log
├── automation/
│   ├── promotions/                ← Mirror of promotions sequences
│   ├── logs/                      ← Mirror of activity logs
│   └── scripts/                   ← Mirror of automation scripts
└── inboxes/
    ├── 01_BOOK_<Item Name>        ← Mirror of assets folder
    ├── 02_MERCH_<Item Name>       ← Mirror of assets folder
    └── ... (mirrored from Google Drive)
```

## Workflow
1. **User populates Google Sheet "CC NOW Store Sheet"** with:
   - Category, Item Name, Description, Price
   - Online Location (URL where item is sold)
   - Current Status (Needs Automation / In Progress / Live)
   - Notes (assets needed, ROI assumptions)
   - Inbox Folder # (e.g. 01_BOOK_La Historia Del Niño)
   - Assets Loaded? (Yes / Partial / No)
   - Assets Checklist (comma list of what is inside)
   - Promo Status and social media status columns
   - Last Action by Hermes, Next Target Date, Notes

2. **User loads assets** into matching inbox folders in Google Drive:
   - Folder `01_<Category>_<Item Name>` corresponds to row 1 in store sheet
   - Folder `02_<Category>_<Item Name>` corresponds to row 2
   - etc.

3. **Automation runs daily** (via cron job at 09:00 local time):
   - Reads the live Google Sheet
   - For each item with status "Needs Automation":
     - Checks if assets are present in the matching Google Drive inbox folder
     - Pulls next promotional message from the matching category's sequence.txt
     - Logs the promotional activity
     - (Future: Will post/schedule to social media, email, etc. when APIs are provided)
   - Updates running totals and revenue tracking
   - Updates the Google Sheet with promo status, last action, next target date, and notes

## Benefits
- **Visual Clarity**: User sees exactly what assets are needed for each product in Google Drive
- **Sequence Enforced**: Numbered folders ensure correct ordering
- **Drift Prevention**: Clear handoff points - user loads inboxes and sheet, automation processes them
- **Scalable**: New products added by appending to store sheet and creating new inbox folder
- **Autonomous Ready**: Once store URLs and webhook credentials are provided, full automation possible

## Naming Convention
- Folders: `01_BOOK_<Exact Item Name from Store Sheet>`
- Files within folders: Use descriptive names (e.g., `cover_front.jpg`, `manuscript.pdf`, `promo_copy.txt`)
- Sequence files: `/automation/promotions/<category>/sequence.txt` (one message per line)

## Example
If store_sheet.csv contains:
```
Book,La Historia Del Niño,Testimony-driven Christian rap autobiography,12.99,https://store.com/book/lhn,Needs Automation,PDF+cover+blurb,01_BOOK_La Historia Del Niño,Yes,cover art,manuscript PDF,blurb,Not Started,...,...,...,,...,...,Hermes hasn't acted yet,2026-05-18,Every dollar is a brick toward El Pabellon de Victoria
```
Then:
- Folder `01_BOOK_La Historia Del Niño` in Google Drive should contain the book PDF and cover art
- Automation will pull promotions from `/automation/promotions/book/sequence.txt`
- After running, Hermes will update the sheet with actions taken and next target date
/root/Hetzner/CC_NOW/
├── store_sheet.csv                ← Master inventory list
├── inboxes/
│   ├── 01_BOOK_<Item Name>        ← Assets for first item in store sheet
│   ├── 02_MERCH_<Item Name>       ← Assets for second item
│   ├── 03_MUSIC_<Item Name>       ← etc.
│   └── ... (sequential numbering matches store sheet rows)
├── automation/
│   ├── promotions/                ← Rotating message sequences
│   ├── logs/                      ← Daily activity logs
│   └── scripts/                   ← Automation scripts
└── sales/
    └── daily.csv                  ← Sales log (append-only)
```

## Workflow
1. **User populates store_sheet.csv** with:
   - Category, Item Name, Description, Price
   - Online Location (URL where item is sold)
   - Current Status (Needs Automation / In Progress / Live)
   - Notes (assets needed, ROI assumptions)

2. **User loads assets** into matching inbox folders:
   - Folder `01_<Category>_<Item Name>` corresponds to row 1 in store_sheet.csv
   - Folder `02_<Category>_<Item Name>` corresponds to row 2
   - etc.

3. **Automation runs daily** (via cron job at 09:00 local time):
   - Reads store_sheet.csv
   - For each item with status "Needs Automation":
     - Pulls next promotional message from the matching category's sequence.txt
     - Logs the promotional activity
     - (Future: Will post/schedule to social media, email, etc.)
   - Updates running totals and revenue tracking

## Benefits
- **Visual Clarity**: User sees exactly what assets are needed for each product
- **Sequence Enforced**: Numbered folders ensure correct ordering
- **Drift Prevention**: Clear handoff points - user loads inboxes, automation processes them
- **Scalable**: New products added by appending to store sheet and creating new inbox folder
- **Autonomous Ready**: Once store URLs and webhook credentials are provided, full automation possible

## Naming Convention
- Folders: `01_BOOK_<Exact Item Name from Store Sheet>`
- Files within folders: Use descriptive names (e.g., `cover_front.jpg`, `manuscript.pdf`, ` promo_copy.txt`)
- Sequence files: `/automation/promotions/<category>/sequence.txt` (one message per line)

## Example
If store_sheet.csv contains:
```
Book,La Historia Del Niño,Testimony-driven Christian rap autobiography,12.99,https://store.com/book/lhn,Needs Automation,PDF+cover+blurb
```
Then:
- Folder `01_BOOK_La Historia Del Niño` should contain the book PDF and cover art
- Automation will pull promotions from `/automation/promotions/book/sequence.txt`