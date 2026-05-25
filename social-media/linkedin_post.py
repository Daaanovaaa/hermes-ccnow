#!/usr/bin/env python3
"""
LinkedIn image-upload + post script for CCN Social Hub.
Called by n8n Execute Command node. Reads post data from env vars.
Handles: register upload slot → download image → upload to LinkedIn → post article.
"""
import json, os, sys, requests

MEMBER_ID = "41q6-gkeGG"
LI_API    = "https://api.linkedin.com"

def load_env():
    env = {}
    with open("/root/.hermes/.env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env

def li_headers(token, binary=False):
    h = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202507",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    if not binary:
        h["Content-Type"] = "application/json"
    return h

def register_image(token):
    r = requests.post(
        f"{LI_API}/rest/images?action=initializeUpload",
        headers=li_headers(token),
        json={"initializeUploadRequest": {"owner": f"urn:li:person:{MEMBER_ID}"}},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()["value"]
    return data["uploadUrl"], data["image"]

def download_image(image_url):
    r = requests.get(image_url, timeout=30)
    r.raise_for_status()
    return r.content

def upload_image(token, upload_url, image_bytes):
    h = li_headers(token, binary=True)
    h["Content-Type"] = "image/jpeg"
    r = requests.put(upload_url, headers=h, data=image_bytes, timeout=60)
    r.raise_for_status()

def post_article(token, message, post_url, title, subtitle, image_urn=None):
    body = {
        "author": f"urn:li:person:{MEMBER_ID}",
        "commentary": message,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if image_urn:
        body["content"] = {
            "article": {
                "source": post_url,
                "thumbnail": image_urn,
                "title": title,
                "description": subtitle or "",
            }
        }
    r = requests.post(
        f"{LI_API}/rest/posts",
        headers=li_headers(token),
        json=body,
        timeout=30,
    )
    r.raise_for_status()
    return r.headers.get("x-restli-id", "")

def main():
    env       = load_env()
    token     = env["LINKEDIN_ACCESS_TOKEN"]
    title     = os.environ.get("LI_TITLE", "New from CCN")
    subtitle  = os.environ.get("LI_SUBTITLE", "")
    post_url  = os.environ.get("LI_URL", "https://danova.substack.com")
    image_url = os.environ.get("LI_IMAGE_URL", "")
    message   = os.environ.get("LI_MESSAGE", title)

    image_urn = None

    if image_url:
        try:
            upload_url, image_urn = register_image(token)
            image_bytes = download_image(image_url)
            upload_image(token, upload_url, image_bytes)
        except Exception as e:
            print(json.dumps({"warning": f"Image upload failed: {e}, posting without image"}), file=sys.stderr)
            image_urn = None

    post_id = post_article(token, message, post_url, title, subtitle, image_urn)
    print(json.dumps({"linkedInPostId": post_id, "imageUrn": image_urn, "success": True}))

if __name__ == "__main__":
    main()
