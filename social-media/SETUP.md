# CCN Social Hub — Setup Instructions

## What's Built
- n8n running on port 5678
- Substack API connected to danova.substack.com
- Facebook + Threads workflow ready to activate
- Instagram workflow ready (needs image URL per post)

## Next Steps to Go Live

### Step A — Get Meta Page Access Token
1. Go to: https://developers.facebook.com/tools/explorer
2. Select app: CCN Social Hub
3. Click "Generate Access Token"
4. Add permissions: pages_manage_posts, pages_read_engagement,
   instagram_basic, instagram_content_publish,
   threads_basic, threads_content_publish
5. Click Generate — copy the token

### Step B — Get your Page IDs
1. Facebook Page ID: Go to your CCN Facebook page
   Settings > About > scroll to bottom — Page ID is there
2. Instagram Account ID: Use Graph API Explorer
   GET /me/accounts — find your IG account ID
3. Threads User ID: Use Graph API Explorer
   GET /me?fields=id with Threads scope

### Step C — Add to n8n
1. Open n8n at localhost:5678
2. Go to Settings > Variables
3. Add all 4 variables from n8n.env.template

### Step D — Import and Activate Workflow
1. In n8n: Workflows > Import
2. Upload: n8n-workflows/substack_to_meta.json
3. Review the workflow
4. Toggle Active = ON

### Step E — Test
Run workflow manually once to verify posting works.

## Posting Schedule
Mon / Wed / Fri / Sun at 9:00 AM AST
Posts latest Substack article to Facebook + Threads automatically.

## Phase 2 — Coming Next
- Instagram (with auto image generation)
- Twitter/X
- LinkedIn
- TikTok
