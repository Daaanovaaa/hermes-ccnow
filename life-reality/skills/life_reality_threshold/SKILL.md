---
name: life_reality_threshold
description: Detects crisis and threshold keywords (URGENT, CRISIS, PROJECT LANDED, THRESHOLD) in Carlos's messages and triggers the Life Reality triage protocol
version: 1.0
author: Hermes Agent
---

# Life Reality — Threshold Monitor Skill

## Trigger Detection (MANDATORY)

Monitor EVERY message from Carlos for these keywords (case-insensitive):
- **URGENT**
- **CRISIS**
- **PROJECT LANDED**
- **THRESHOLD**

If any of these words appear in a message, immediately invoke the threshold protocol before doing anything else.

## Threshold Protocol

When a trigger keyword is detected:

1. Run the threshold monitor script:
   ```
   python3 /root/hermes-ccnow/life-reality/threshold_monitor.py --event "<exact message from Carlos>"
   ```

2. Deliver the triage prompt output to Carlos via Telegram (or CLI — wherever the message came from).

3. Wait for Carlos's triage answers (what dropped, what's protected, what can be rescheduled).

4. After Carlos responds, help him restructure the schedule by:
   - Updating Google Calendar if needed
   - Flagging any CC NOW! tasks that need to shift
   - Confirming what stays non-negotiable

5. Log the resolution by updating threshold_log.csv (update `what_dropped`, `what_protected`, `what_rescheduled` fields for the relevant entry).

## Non-Negotiable Protected Blocks

These blocks are NEVER dropped, even in a crisis — mention them explicitly when they are at risk:

- **5:30–8:30 AM RAP WORK** (FUNNY pillar — creative output, airplane mode)
- **Tuesday 3–6 PM**: The Gathering Church rehearsal
- **Sunday 8 AM–1 PM**: The Gathering Church service
- **Sleep**: minimum 6 hours — performance and health depend on it

## Financial Threshold Protocol

If the crisis involves an unplanned expense:
1. Ask: what is the dollar amount?
2. Cross-reference with current bank balance (call Plaid MCP if available)
3. Flag if expense exceeds 20% of available balance
4. Help Carlos identify which CC NOW! revenue action could offset the expense fastest

## Tone

Carlos is post-bankruptcy and building from zero. Every crisis is real. The tone is:
- Calm, not alarmed
- Practical, not emotional
- Grounding: "You have been through worse. Here is the first step."
- Never shame or lecture

## Logging

All threshold events are logged to:
`/root/hermes-ccnow/life-reality/threshold_log.csv`

This builds the pattern file for quarterly review: what types of crises recur, what their financial impact is, and what interventions work.
