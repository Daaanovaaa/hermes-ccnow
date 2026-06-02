#!/usr/bin/env python3
"""
N.O.A.H. Vault Change Watcher
Watches /root/obsidian-vault/ via inotify and logs .md file changes.
"""

import os
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VAULT_PATH = "/root/obsidian-vault/"
CHANGE_LOG = "/root/hermes-ccnow/vault-watcher/vault_changes.log"

IGNORED_PATTERNS = [
    '.stfolder',
    '.obsidian',
    '.trash',
    '.sops.yaml',
    'secrets/',
    '.stversions',
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)


def is_ignored(path):
    for pattern in IGNORED_PATTERNS:
        if pattern in path:
            return True
    return False


def log_change(event_type, path):
    rel = os.path.relpath(path, VAULT_PATH)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {event_type} | {rel}\n"
    with open(CHANGE_LOG, "a") as f:
        f.write(line)
    logging.info("Logged: %s %s", event_type, rel)


class VaultHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".md"):
            return
        if is_ignored(event.src_path):
            return
        log_change("created", event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".md"):
            return
        if is_ignored(event.src_path):
            return
        log_change("modified", event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".md"):
            return
        if is_ignored(event.src_path):
            return
        log_change("deleted", event.src_path)


if __name__ == "__main__":
    logging.info("Vault watcher starting — watching %s", VAULT_PATH)
    handler = VaultHandler()
    observer = Observer()
    observer.schedule(handler, VAULT_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
