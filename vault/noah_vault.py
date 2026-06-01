#!/usr/bin/env python3
"""
N.O.A.H. Vault Writer — Hermes utility for writing to the Obsidian vault.

Functions:
  write_inbox(title, content)   → /root/obsidian-vault/00-INBOX/
  write_task(title, content)    → /root/obsidian-vault/01-TASKS/
  write_log(content, folder)    → daily log in any vault folder
  read_inbox()                  → list files in 00-INBOX with status: new

CLI:
  python3 noah_vault.py inbox "Title" "Content"
  python3 noah_vault.py task  "Title" "Content"
  python3 noah_vault.py log   "Content" "FRONT-OFFICE/03-Business"
"""
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

VAULT_ROOT = Path("/root/obsidian-vault")
AST_OFFSET = timedelta(hours=-4)  # UTC-4


def _now_ast() -> datetime:
    return datetime.now(timezone.utc).astimezone(timezone(AST_OFFSET))


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _frontmatter(**fields) -> str:
    lines = ["---"]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def write_inbox(title: str, content: str) -> Path:
    """Create a new markdown note in 00-INBOX/."""
    now = _now_ast()
    filename = now.strftime("%Y-%m-%d-%H-%M") + f"-{_slug(title)}.md"
    dest = VAULT_ROOT / "00-INBOX" / filename

    fm = _frontmatter(
        date=now.strftime("%Y-%m-%d %H:%M"),
        source="hermes",
        status="new",
    )
    dest.write_text(f"{fm}\n\n# {title}\n\n{content}\n")
    return dest


def write_task(title: str, content: str, area: str = "01-TASKS") -> Path:
    """Create a task note in 01-TASKS/ (or a custom area folder)."""
    now = _now_ast()
    filename = now.strftime("%Y-%m-%d-%H-%M") + f"-{_slug(title)}.md"
    folder = VAULT_ROOT / area
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / filename

    fm = _frontmatter(
        date=now.strftime("%Y-%m-%d %H:%M"),
        status="open",
        area=area,
    )
    dest.write_text(f"{fm}\n\n# {title}\n\n{content}\n")
    return dest


def write_log(content: str, folder: str) -> Path:
    """Append a timestamped entry to today's daily log in the given vault folder."""
    now = _now_ast()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    log_folder = VAULT_ROOT / folder
    log_folder.mkdir(parents=True, exist_ok=True)
    dest = log_folder / f"{date_str}-log.md"

    entry = f"\n## {time_str}\n\n{content}\n"

    if not dest.exists():
        header = _frontmatter(date=date_str, type="log")
        dest.write_text(f"{header}\n\n# Log — {date_str}\n{entry}")
    else:
        with dest.open("a") as f:
            f.write(entry)

    return dest


def read_inbox() -> list[dict]:
    """Return all files in 00-INBOX/ whose frontmatter has status: new."""
    inbox = VAULT_ROOT / "00-INBOX"
    results = []

    for md_file in sorted(inbox.glob("*.md")):
        text = md_file.read_text()
        if "status: new" in text:
            results.append({"file": str(md_file), "name": md_file.name})

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage():
    print(__doc__)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if not args:
        _usage()

    cmd = args[0].lower()

    if cmd == "inbox":
        if len(args) < 3:
            print("Usage: noah_vault.py inbox <title> <content>")
            sys.exit(1)
        path = write_inbox(args[1], args[2])
        print(f"inbox: {path}")

    elif cmd == "task":
        if len(args) < 3:
            print("Usage: noah_vault.py task <title> <content> [area]")
            sys.exit(1)
        area = args[3] if len(args) > 3 else "01-TASKS"
        path = write_task(args[1], args[2], area)
        print(f"task: {path}")

    elif cmd == "log":
        if len(args) < 3:
            print("Usage: noah_vault.py log <content> <folder>")
            sys.exit(1)
        path = write_log(args[1], args[2])
        print(f"log: {path}")

    elif cmd == "read-inbox":
        files = read_inbox()
        if not files:
            print("read-inbox: 0 new items")
        else:
            print(f"read-inbox: {len(files)} new item(s)")
            for f in files:
                print(f"  {f['name']}")

    else:
        _usage()


if __name__ == "__main__":
    main()
