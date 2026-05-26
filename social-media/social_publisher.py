#!/usr/bin/env python3
"""
CCN Social Publisher — native Python replacement for n8n social media automation.
Reads latest Substack post and publishes to LinkedIn, Facebook (x2), and Threads.
Schedule: Mon/Wed/Fri/Sun 9AM AST (13:00 UTC)
"""
# API references:
#   LinkedIn ugcPosts: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api
#   Facebook Graph feed: https://developers.facebook.com/docs/graph-api/reference/page/feed/
#   Threads API: https://developers.facebook.com/docs/threads/posts

import json
import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
POSTED_FILE = BASE_DIR / "posted.json"
LOG_FILE    = BASE_DIR / "logs" / "publisher.log"
ENV_FILE    = Path("/root/.hermes/.env")

# ── Config ──────────────────────────────────────────────────────────────────
SUBSTACK_FEED  = "https://danova.substack.com/feed"
MEMBER_URN     = "urn:li:person:41q6-gkeGG"
LI_API         = "https://api.linkedin.com"
FB_GRAPH_API   = "https://graph.facebook.com/v19.0"
THREADS_API    = "https://graph.threads.net/v1.0"
HASHTAGS       = "#ConsciousCultureNOW #CCNow #Kingdom #Faith #HipHop #ElPabellon"


# ── Helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def send_telegram(msg: str):
    """Send notification via Hermes; fallback to direct Bot API."""
    env = dotenv_values(ENV_FILE)
    result = subprocess.run(
        ["hermes", "send", "--to", "telegram", msg],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_HOME_CHANNEL", "")
    if token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=15,
            )
        except Exception as e:
            log(f"Telegram fallback error: {e}")


def load_posted() -> set:
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()


def save_posted(posted: set):
    POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2))


def format_message(title: str, subtitle: str, url: str) -> str:
    sub = subtitle.strip() if subtitle else ""
    if sub:
        return f"✝️ {title}\n\n{HASHTAGS}\n\n{sub}\n\nRead the full post: {url}"
    return f"✝️ {title}\n\n{HASHTAGS}\n\nRead the full post: {url}"


# ── RSS Fetch ────────────────────────────────────────────────────────────────

def fetch_latest_post() -> dict | None:
    """Return the most recent Substack post as {title, subtitle, url, guid}."""
    resp = requests.get(SUBSTACK_FEED, timeout=20)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    items = root.findall(".//item")
    if not items:
        return None
    item = items[0]
    title    = (item.findtext("title") or "").strip()
    url      = (item.findtext("link") or "").strip()
    guid     = (item.findtext("guid") or url).strip()
    # Substack puts the subtitle in <description> (HTML stripped to plain)
    raw_desc = item.findtext("description") or ""
    # Strip HTML tags for a clean subtitle
    import re
    subtitle = re.sub(r"<[^>]+>", "", raw_desc).strip()[:280]
    return {"title": title, "subtitle": subtitle, "url": url, "guid": guid}


# ── LinkedIn ─────────────────────────────────────────────────────────────────

def post_linkedin(token: str, message: str, url: str, title: str, subtitle: str) -> str:
    """Post via ugcPosts API. Returns post URN or raises."""
    # API ref: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api
    payload = {
        "author": MEMBER_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message},
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "originalUrl": url,
                        "title": {"text": title},
                        "description": {"text": subtitle[:200] if subtitle else ""},
                    }
                ],
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    resp = requests.post(
        f"{LI_API}/v2/ugcPosts",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.headers.get("x-restli-id", resp.json().get("id", "ok"))


# ── Facebook ─────────────────────────────────────────────────────────────────

def post_facebook(page_id: str, token: str, message: str, url: str) -> str:
    """Post to a Facebook Page feed. Returns post ID or raises.
    API ref: https://developers.facebook.com/docs/graph-api/reference/page/feed/
    """
    resp = requests.post(
        f"{FB_GRAPH_API}/{page_id}/feed",
        data={
            "message": message,
            "link": url,
            "access_token": token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("id", "ok")


# ── Threads ──────────────────────────────────────────────────────────────────

def post_threads(user_id: str, token: str, message: str) -> str:
    """Two-step Threads publish: create container then publish.
    API ref: https://developers.facebook.com/docs/threads/posts
    """
    # Step 1: create media container
    resp1 = requests.post(
        f"{THREADS_API}/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": message,
            "access_token": token,
        },
        timeout=30,
    )
    resp1.raise_for_status()
    container_id = resp1.json().get("id")
    if not container_id:
        raise ValueError(f"Threads container creation returned no ID: {resp1.text}")

    # Step 2: publish container
    resp2 = requests.post(
        f"{THREADS_API}/{user_id}/threads_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=30,
    )
    resp2.raise_for_status()
    return resp2.json().get("id", "ok")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    env = dotenv_values(ENV_FILE)

    # Required credentials
    li_token          = env.get("LINKEDIN_ACCESS_TOKEN", "")
    ccn_fb_page_id    = env.get("CCN_FACEBOOK_PAGE_ID", "")
    ccn_fb_token      = env.get("META_CCN_PAGE_ACCESS_TOKEN", "")
    tu_tienda_page_id = env.get("CCN_TUTIENDA_PAGE_ID", "")
    tu_tienda_token   = env.get("CCN_TUTIENDA_PAGE_ACCESS_TOKEN", "")
    threads_user_id   = env.get("CCN_THREADS_USER_ID", "")
    threads_token     = env.get("CCN_THREADS_ACCESS_TOKEN", "")

    log("CCN Social Publisher starting")

    # Fetch latest post
    try:
        post = fetch_latest_post()
    except Exception as e:
        msg = f"❌ CCN Social Publisher: RSS fetch failed — {e}"
        log(msg)
        send_telegram(msg)
        sys.exit(1)

    if not post:
        log("No posts found in RSS feed")
        sys.exit(0)

    log(f"Latest post: {post['title']} ({post['guid']})")

    # Deduplicate
    posted = load_posted()
    if post["guid"] in posted:
        log(f"Already posted: {post['guid']} — skipping")
        sys.exit(0)

    message = format_message(post["title"], post["subtitle"], post["url"])
    results = {}
    failures = []

    # LinkedIn
    if li_token:
        try:
            post_id = post_linkedin(li_token, message, post["url"], post["title"], post["subtitle"])
            log(f"LinkedIn: OK ({post_id})")
            results["linkedin"] = post_id
        except Exception as e:
            log(f"LinkedIn FAILED: {e}")
            failures.append(f"LinkedIn: {e}")
    else:
        log("LinkedIn: skipped (no token)")

    # Facebook — CCN Page
    if ccn_fb_token and ccn_fb_page_id:
        try:
            post_id = post_facebook(ccn_fb_page_id, ccn_fb_token, message, post["url"])
            log(f"Facebook CCN: OK ({post_id})")
            results["facebook_ccn"] = post_id
        except Exception as e:
            log(f"Facebook CCN FAILED: {e}")
            failures.append(f"Facebook CCN: {e}")
    else:
        log("Facebook CCN: skipped (missing token or page ID)")

    # Facebook — Tu Tienda AHORA Page
    if tu_tienda_token and tu_tienda_page_id:
        try:
            post_id = post_facebook(tu_tienda_page_id, tu_tienda_token, message, post["url"])
            log(f"Facebook TuTienda: OK ({post_id})")
            results["facebook_tutienda"] = post_id
        except Exception as e:
            log(f"Facebook TuTienda FAILED: {e}")
            failures.append(f"Facebook TuTienda: {e}")
    else:
        log("Facebook TuTienda: skipped (missing token or page ID)")

    # Threads
    if threads_token and threads_user_id:
        try:
            post_id = post_threads(threads_user_id, threads_token, message)
            log(f"Threads: OK ({post_id})")
            results["threads"] = post_id
        except Exception as e:
            log(f"Threads FAILED: {e}")
            failures.append(f"Threads: {e}")
    else:
        log("Threads: skipped (missing token or user ID)")

    # Mark as posted only if at least one platform succeeded
    if results:
        posted.add(post["guid"])
        save_posted(posted)

    # Telegram summary
    ok_platforms  = list(results.keys())
    ok_str        = ", ".join(ok_platforms) if ok_platforms else "none"
    fail_str      = "\n".join(failures) if failures else ""
    status_icon   = "✅" if not failures else ("⚠️" if ok_platforms else "❌")
    tg_msg = (
        f"{status_icon} <b>CCN Social Publisher</b>\n"
        f"📰 {post['title']}\n"
        f"✔ Posted to: {ok_str}\n"
    )
    if fail_str:
        tg_msg += f"❌ Failed:\n{fail_str}\n"
    tg_msg += f"🔗 {post['url']}"
    send_telegram(tg_msg)

    if failures and not results:
        sys.exit(1)


if __name__ == "__main__":
    main()
