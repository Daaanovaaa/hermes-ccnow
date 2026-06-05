#!/usr/bin/env python3
import os
import subprocess
import logging

BASE_DIR = "/root/hermes-ccnow/voice-corpus"
RAW_TEXT_DIR = os.path.join(BASE_DIR, "raw_text")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(RAW_TEXT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "corpus.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CHANNELS = [
    {
        "url": "https://www.youtube.com/@DominaloConCRISTO/videos",
        "cookies": "/root/hermes-ccnow/voice-corpus/cookies_dominalo.txt"
    },
    {
        "url": "https://www.youtube.com/@carlosvillanueva1012/videos",
        "cookies": "/root/hermes-ccnow/voice-corpus/cookies_carlos1012.txt"
    },
    {
        "url": "https://www.youtube.com/@carlosvillanueva219/videos",
        "cookies": "/root/hermes-ccnow/voice-corpus/cookies_carlos219.txt"
    }
]

def get_channel_videos(channel_url, cookies):
    try:
        cmd = ["yt-dlp", "--cookies", cookies, "--flat-playlist",
               "--print", "%(webpage_url)s", channel_url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [u for u in result.stdout.strip().split("\n") if u]
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get videos for {channel_url}: {e.stderr}")
        return []

def download_transcript(video_url, cookies):
    video_id = video_url.split("v=")[-1]
    output_file = os.path.join(RAW_TEXT_DIR, f"yt_{video_id}.txt")
    if os.path.exists(output_file):
        logger.info(f"Skipping already downloaded: {video_id}")
        return True
    try:
        cmd = [
            "yt-dlp", "--cookies", cookies,
            "--skip-download",
            "--write-auto-sub", "--sub-lang", "en",
            "--convert-subs", "txt",
            "-o", os.path.join(RAW_TEXT_DIR, f"yt_{video_id}.%(ext)s"),
            video_url
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        subtitle_file = os.path.join(RAW_TEXT_DIR, f"yt_{video_id}.en.txt")
        if os.path.exists(subtitle_file):
            os.rename(subtitle_file, output_file)
            logger.info(f"Downloaded transcript: {video_id}")
            return True
        else:
            logger.warning(f"No English transcript for: {video_id}")
            return False
    except Exception as e:
        logger.error(f"Failed for {video_id}: {str(e)}")
        return False

def main():
    logger.info("Starting YouTube transcripts downloader")
    total_processed = 0
    total_downloaded = 0
    for channel in CHANNELS:
        logger.info(f'Processing: {channel["url"]}')
        video_urls = get_channel_videos(channel["url"], channel["cookies"])
        if not video_urls:
            logger.warning(f'No videos found for {channel["url"]}')
            continue
        logger.info(f"Found {len(video_urls)} videos")
        for video_url in video_urls:
            total_processed += 1
            if download_transcript(video_url, channel["cookies"]):
                total_downloaded += 1
    logger.info(f"Completed. Processed: {total_processed}, Downloaded: {total_downloaded}")

if __name__ == "__main__":
    main()
