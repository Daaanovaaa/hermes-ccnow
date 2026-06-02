#!/usr/bin/env python3
"""
N.O.A.H. Vault Notifier
Reads vault_changes.log, sends a Telegram summary to Hermes, then clears the log.
Run via cron every 15 minutes.
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

ENV_PATH = "/root/.hermes/.env"
CHANGE_LOG = "/root/hermes-ccnow/vault-watcher/vault_changes.log"

AST = timezone(timedelta(hours=-4))


def load_env():
    env = dotenv_values(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = (
        env.get("TELEGRAM_CHAT_ID")
        or env.get("TELEGRAM_HOME_CHANNEL")
        or os.environ.get("TELEGRAM_CHAT_ID")
        or os.environ.get("TELEGRAM_HOME_CHANNEL")
    )
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not found in " + ENV_PATH)
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID / TELEGRAM_HOME_CHANNEL not found in " + ENV_PATH)
    return token, chat_id


def read_and_clear_log():
    if not os.path.exists(CHANGE_LOG):
        return []
    with open(CHANGE_LOG, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if lines:
        open(CHANGE_LOG, "w").close()
    return lines


def parse_entries(lines):
    entries = []
    for line in lines:
        parts = line.split(" | ", 2)
        if len(parts) == 3:
            _, event_type, path = parts
            entries.append((event_type.strip(), path.strip()))
    return entries


def build_message(entries):
    now = datetime.now(AST).strftime("%Y-%m-%d %H:%M AST")
    file_lines = "\n".join(f"- {path} ({event})" for event, path in entries)
    return (
        f"🧠 NOAH Vault Update — {now}\n\n"
        f"Changed files:\n{file_lines}\n\n"
        f"Run `hermes vault-scan` to review or reply IGNORE to dismiss."
    )


async def send_telegram(token, chat_id, message):
    from telegram import Bot
    bot = Bot(token=token)
    await bot.send_message(chat_id=int(chat_id), text=message)


def main():
    lines = read_and_clear_log()
    if not lines:
        return

    entries = parse_entries(lines)
    if not entries:
        return

    token, chat_id = load_env()
    message = build_message(entries)
    asyncio.run(send_telegram(token, chat_id, message))
    print("Telegram notification sent.")
    print(message)


if __name__ == "__main__":
    main()
