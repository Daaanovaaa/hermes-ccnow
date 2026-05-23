#!/usr/bin/env python3
"""
Telegram Handler — Prayer Finance confirmation listener.
Uses Telegram Bot API long polling to watch for Carlos's Fidelity confirmation replies.
Parses confirmation numbers and logs them via prayer_finance_engine.py --confirm.

Usage:
  python3 telegram_handler.py --listen           # Start long-polling daemon
  python3 telegram_handler.py --send "message"   # Send message to home channel
  python3 telegram_handler.py --test             # Send a test ping
"""
import json, os, re, subprocess, sys, time
import urllib.request, urllib.parse, urllib.error
from pathlib import Path

HERMES_ENV  = Path('/root/.hermes/.env')
FINANCE_DIR = Path(__file__).parent
LOG_FILE    = FINANCE_DIR / 'prayer_finance_log.json'
CACHE_FILE  = FINANCE_DIR / 'ipo_cache.json'
ENGINE      = FINANCE_DIR / 'prayer_finance_engine.py'
OFFSET_FILE = FINANCE_DIR / '.telegram_offset'


def _load_env():
    if HERMES_ENV.exists():
        for line in HERMES_ENV.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
TOKEN   = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_HOME_CHANNEL', '')
ALLOWED = set(os.getenv('TELEGRAM_ALLOWED_USERS', '').split(','))

# Regex: alphanumeric strings 6-20 chars that look like confirmation numbers
CONF_RE = re.compile(r'\b([A-Z0-9]{6,20})\b')
CONFIRM_KEYWORDS = {
    'confirm', 'conf', 'confirmation', 'bought', 'purchased',
    'fidelity', 'done', 'order', 'executed', 'filled',
}


def _api(method: str, params: dict, timeout: int = 35) -> dict:
    url  = f'https://api.telegram.org/bot{TOKEN}/{method}'
    data = urllib.parse.urlencode(params).encode()
    req  = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def send_message(text: str) -> bool:
    if not TOKEN or not CHAT_ID:
        print('ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL not set', file=sys.stderr)
        return False
    try:
        _api('sendMessage', {'chat_id': CHAT_ID, 'text': text})
        return True
    except Exception as e:
        print(f'Telegram send error: {e}', file=sys.stderr)
        return False


def get_updates(offset: int = 0) -> list:
    try:
        resp = _api('getUpdates', {'offset': offset, 'timeout': 30, 'limit': 10}, timeout=40)
        return resp.get('result', [])
    except urllib.error.URLError as e:
        print(f'getUpdates network error: {e}', file=sys.stderr)
        return []
    except Exception as e:
        print(f'getUpdates error: {e}', file=sys.stderr)
        return []


def load_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0


def save_offset(offset: int):
    OFFSET_FILE.write_text(str(offset))


def get_pending_ticker() -> str:
    """Return ticker from most recent active recommendation."""
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        candidates = cache.get('candidates', [])
        if candidates:
            return candidates[0].get('ticker', '')
    except Exception:
        pass
    return ''


def is_confirmation(text: str) -> bool:
    text_lower = text.lower()
    words = set(text_lower.split())
    has_keyword = bool(words & CONFIRM_KEYWORDS)
    has_code    = bool(CONF_RE.search(text.upper()))
    return has_keyword or has_code


def extract_conf_number(text: str) -> str:
    matches = CONF_RE.findall(text.upper())
    if matches:
        return max(matches, key=len)
    return text.strip().split()[-1] if text.strip() else 'UNKNOWN'


def handle_update(update: dict):
    msg     = update.get('message', {})
    text    = (msg.get('text') or '').strip()
    from_id = str(msg.get('from', {}).get('id', ''))

    if not text or not from_id:
        return

    if ALLOWED and from_id not in ALLOWED:
        return

    print(f'[{from_id}] {text[:80]}')

    if not is_confirmation(text):
        return

    conf_number = extract_conf_number(text)
    ticker      = get_pending_ticker()

    if not ticker:
        send_message(
            'Received your message, but no active IPO recommendation is on file.\n'
            'To log manually, reply: /confirm TICKER CONF_NUMBER'
        )
        return

    # Check for manual override: /confirm TICKER CONF#
    manual = re.match(r'^/confirm\s+(\w+)\s+(\w+)$', text.strip(), re.IGNORECASE)
    if manual:
        ticker      = manual.group(1).upper()
        conf_number = manual.group(2).upper()

    result = subprocess.run(
        ['python3', str(ENGINE), '--confirm', ticker, conf_number],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        send_message(
            f'Seed planted and logged.\n\n'
            f'Ticker: {ticker}\n'
            f'Confirmation: {conf_number}\n\n'
            f'Mark 4:26-29 — This seed is covered in prayer. '
            f'GOD gives the increase in His timing. Amen.'
        )
        print(f'Logged: {ticker} {conf_number}')
    else:
        err = result.stderr.strip()[:300]
        send_message(f'Logging error — please check manually.\n{err}')
        print(f'Engine error: {err}', file=sys.stderr)


def listen():
    if not TOKEN:
        print('ERROR: TELEGRAM_BOT_TOKEN not set in /root/.hermes/.env', file=sys.stderr)
        sys.exit(1)

    print(f'Prayer Finance Telegram listener started')
    print(f'Bot token: ...{TOKEN[-8:]}  |  Chat: {CHAT_ID}')
    print(f'Allowed users: {ALLOWED}')

    offset = load_offset()
    while True:
        updates = get_updates(offset)
        for upd in updates:
            try:
                handle_update(upd)
            except Exception as e:
                print(f'Update error: {e}', file=sys.stderr)
            offset = upd['update_id'] + 1
            save_offset(offset)
        time.sleep(1)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    if args[0] == '--listen':
        listen()
    elif args[0] == '--send':
        text = ' '.join(args[1:]) if len(args) > 1 else ''
        if not text:
            text = sys.stdin.read().strip()
        ok = send_message(text)
        print('Sent.' if ok else 'Send failed.')
    elif args[0] == '--test':
        ok = send_message('Prayer Finance bot online. Listening for confirmations.')
        print('Test ping sent.' if ok else 'Test ping failed.')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
