# Omi AI Integration — Setup Instructions

## What This Does
Your Omi wearable records ambient conversations and ideas throughout the day.
This integration routes those transcripts into Hermes automatically:
- Action items → Telegram alert
- Case updates → Updates the correct case log
- Ministry ideas → Saved to creative vault
- Business info → Logged to CRM if contact named
- Prayer requests → Prayer Finance journal
- Health notes → Health log

## Step 1: Find Your VPS IP Address
In your Hermes CLI, type: curl ifconfig.me
Note the IP address.

## Step 2: Configure Omi Webhook
1. Open the Omi app on your phone
2. Go to Settings → Integrations → Webhook (or Developer)
3. Enter: http://[your-vps-ip]:5007/omi
4. Set method: POST
5. Save

## Step 3: Test
Say something to your Omi device.
Within 1-2 minutes you should receive a Telegram message:
"🎙 OMI TRANSCRIPT PROCESSED..."

## Step 4: Email Fallback (if webhook not available)
If your Omi plan doesn't support webhooks:
- Set up email forwarding in Omi to: faaaithmusicmovies@gmail.com
- The correspondence tracker will detect Omi emails
- Manual processing: tell Hermes "Process Omi email: [paste transcript]"

## Port Note
Port 5007 is bound to 0.0.0.0 (accessible from internet).
This is required for Omi's servers to POST transcripts.
The endpoint only accepts POST requests with valid transcript format.
It does not expose any other system data.

## Service Management
Check status: systemctl status omi-webhook
View logs: journalctl -u omi-webhook -n 50
Restart: systemctl restart omi-webhook
