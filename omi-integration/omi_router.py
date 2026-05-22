#!/usr/bin/env python3
"""
Omi AI Transcript Router
Receives transcripts via HTTP webhook on port 5007 and routes parsed content
to the correct Hermes systems.

Webhook endpoint: POST http://[vps-ip]:5007/omi
Payload: {"text": "transcript...", "created_at": "...", "duration": 120}

Usage:
  python3 omi_router.py               # start webhook server
  python3 omi_router.py --process "transcript text"   # process manually
  python3 omi_router.py --port 5007   # override port
"""

import json
import os
import re
import subprocess
import sys
import threading
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

CONFIG_FILE = Path(__file__).parent / 'omi_config.json'
RAW_DIR     = Path('/root/hermes-ccnow/omi-integration/raw')
OBSIDIAN_DIR = Path('/root/hermes-ccnow/obsidian-vault/08-Omi-Transcripts')
CASES_DIR   = Path('/root/hermes-ccnow/life-admin/cases')
UPDATER     = Path('/root/hermes-ccnow/life-admin/case_log_updater.py')

HERMES_ENV = Path('/root/.hermes/.env')


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def send_telegram(msg):
    """Send message to Telegram via bot API."""
    try:
        from dotenv import load_dotenv
        load_dotenv(HERMES_ENV)
        token   = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_HOME_CHANNEL')
        if not token or not chat_id:
            return
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': msg}).encode()
        urllib.request.urlopen(
            f'https://api.telegram.org/bot{token}/sendMessage', data=data
        )
    except Exception:
        pass


def detect_action_items(text, keywords):
    """Find action items in transcript."""
    items = []
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in keywords):
            items.append(s.strip())
    return items


def detect_case_updates(text, config):
    """Check if transcript mentions any tracked case topics."""
    updates = {}
    text_lower = text.lower()
    for case_key, keywords in config.get('case_log_keywords', {}).items():
        if any(kw in text_lower for kw in keywords):
            updates[case_key] = keywords[0]
    return updates


def save_raw_transcript(text, timestamp):
    """Save raw transcript to file."""
    RAW_DIR.mkdir(exist_ok=True)
    ts_str  = timestamp.strftime('%Y%m%d_%H%M%S')
    fname   = RAW_DIR / f'{ts_str}_transcript.txt'
    fname.write_text(f"Timestamp: {timestamp.isoformat()}\n\n{text}")
    return fname


def save_obsidian_note(text, timestamp, action_items, case_updates, ideas):
    """Save processed note to Obsidian vault."""
    OBSIDIAN_DIR.mkdir(exist_ok=True)
    date_str = timestamp.strftime('%Y-%m-%d')
    fname    = OBSIDIAN_DIR / f'{date_str}_omi_note.md'

    content = f"""# Omi Note — {timestamp.strftime('%Y-%m-%d %H:%M')}

## Transcript
{text}

## Action Items
{''.join(f"- [ ] {item}\\n" for item in action_items) if action_items else "*None detected*"}

## Case Updates Flagged
{''.join(f"- {k}: mentions '{v}'\\n" for k, v in case_updates.items()) if case_updates else "*None detected*"}

## Ideas Captured
{''.join(f"- {idea}\\n" for idea in ideas) if ideas else "*None detected*"}
"""
    # Append if file exists (multiple notes same day)
    if fname.exists():
        fname.write_text(fname.read_text() + '\n---\n' + content)
    else:
        fname.write_text(content)
    return fname


def process_transcript(text, timestamp=None):
    """Full processing pipeline for a transcript."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    config = load_config()

    # 1. Save raw
    raw_file = save_raw_transcript(text, timestamp)

    # 2. Detect content
    action_items  = detect_action_items(text, config.get('action_keywords', []))
    case_updates  = detect_case_updates(text, config)
    ideas         = detect_action_items(text, config.get('ministry_keywords', []))
    biz_items     = detect_action_items(text, config.get('business_keywords', []))

    # 3. Save to Obsidian
    note_file = save_obsidian_note(text, timestamp, action_items, case_updates, ideas + biz_items)

    # 4. Send Telegram summary
    duration_est = max(1, len(text.split()) // 130)  # ~130 wpm estimate
    summary = (
        f"OMI TRANSCRIPT PROCESSED — {timestamp.strftime('%H:%M')}\n"
        f"Duration: ~{duration_est} min\n"
        f"Action items found: {len(action_items)}\n"
        f"Case updates: {len(case_updates)}\n"
        f"Ideas captured: {len(ideas)}\n"
        f"Saved to vault: {note_file.name}"
    )

    if action_items:
        summary += "\n\nACTION ITEMS:\n" + '\n'.join(f"• {a[:60]}" for a in action_items[:3])

    if config.get('route_to_telegram', True):
        send_telegram(summary)

    return {
        'action_items':  action_items,
        'case_updates':  case_updates,
        'ideas':         ideas,
        'biz_items':     biz_items,
        'raw_file':      str(raw_file),
        'note_file':     str(note_file),
    }


class OmiWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/omi':
            self.send_response(404)
            self.end_headers()
            return

        length  = int(self.headers.get('Content-Length', 0))
        body    = self.rfile.read(length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        text      = payload.get('text', payload.get('transcript', ''))
        created   = payload.get('created_at', '')
        try:
            ts = datetime.fromisoformat(created.replace('Z', '+00:00'))
        except Exception:
            ts = datetime.now(timezone.utc)

        if text:
            threading.Thread(target=process_transcript, args=(text, ts), daemon=True).start()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')

    def log_message(self, format, *args):
        pass  # Suppress default access logs


def start_server(port=5007):
    server = HTTPServer(('0.0.0.0', port), OmiWebhookHandler)
    print(f"Omi webhook listening on port {port}")
    print(f"Endpoint: POST http://[vps-ip]:{port}/omi")
    server.serve_forever()


def main():
    args = sys.argv[1:]

    if '--process' in args:
        idx  = args.index('--process')
        text = ' '.join(args[idx+1:])
        result = process_transcript(text)
        print(f"Processed: {len(result['action_items'])} actions, {len(result['case_updates'])} case updates")
        return

    port = 5007
    if '--port' in args:
        idx  = args.index('--port')
        if idx + 1 < len(args):
            port = int(args[idx+1])

    start_server(port)


if __name__ == '__main__':
    main()
