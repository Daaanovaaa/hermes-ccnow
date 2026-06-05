#!/usr/bin/env python3
"""
CCN Voice Corpus Crawler
Fetches web pages from urls.txt, strips HTML, saves clean text
"""
import os
import time
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import re
from datetime import datetime

# Setup directories
BASE_DIR = "/root/hermes-ccnow/voice-corpus"
RAW_TEXT_DIR = os.path.join(BASE_DIR, "raw_text")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
URLS_FILE = os.path.join(BASE_DIR, "urls.txt")

# Ensure directories exist
os.makedirs(RAW_TEXT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "corpus.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def slugify(url):
    """Convert URL to a safe filename"""
    parsed = urlparse(url)
    # Remove protocol and www, replace special chars
    slug = parsed.netloc.replace('www.', '') + parsed.path
    # Replace non-alphanumeric with underscores
    slug = ''.join(c if c.isalnum() else '_' for c in slug)
    # Remove leading/trailing underscores and reduce multiple underscores
    slug = slug.strip('_')
    while '__' in slug:
        slug = slug.replace('__', '_')
    return slug or 'index'

def extract_date(soup):
    """Extract publish date from page"""
    # Try common patterns
    # 1. <time> tag with datetime attribute
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime']
    # 2. meta property="article:published_time"
    meta = soup.find('meta', property='article:published_time')
    if meta and meta.get('content'):
        return meta['content']
    # 3. meta name="date" or "pubdate"
    meta = soup.find('meta', attrs={'name': ['date', 'pubdate']})
    if meta and meta.get('content'):
        return meta['content']
    # 4. Look for any date-like string in the text (last resort)
    # We'll skip this for now to avoid incorrect dates
    return None

def extract_content_type(url, soup):
    """Determine content type from URL or page"""
    url_lower = url.lower()
    if '/blog/' in url_lower:
        return 'blog'
    if '/ccn-episode-' in url_lower:
        return 'episode'
    if '/statement-of-faith' in url_lower:
        return 'bio'
    if '/about-us' in url_lower:
        return 'bio'
    if '/tv' in url_lower:
        return 'video'
    if 'substack.com' in url_lower:
        return 'social'
    if 'speakerhub.com' in url_lower:
        return 'bio'
    # Default
    return 'general'

def fetch_and_clean(url):
    """Fetch URL and return clean text and metadata"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract metadata
        date_published = extract_date(soup)
        content_type = extract_content_type(url, soup)
        
        metadata = {
            'source_url': url,
            'date_published': date_published,
            'content_type': content_type
        }
        
        return text, metadata
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {str(e)}")
        return None, None

def main():
    logger.info("Starting voice corpus crawler")
    
    # Read URLs
    try:
        with open(URLS_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"URLs file not found: {URLS_FILE}")
        return
    
    logger.info(f"Found {len(urls)} URLs to process")
    
    for url in urls:
        slug = slugify(url)
        output_file = os.path.join(RAW_TEXT_DIR, f"{slug}.txt")
        meta_file = os.path.join(RAW_TEXT_DIR, f"{slug}.json")
        
        # Skip if already crawled (we'll check both files)
        if os.path.exists(output_file) and os.path.exists(meta_file):
            logger.info(f"Skipping already crawled: {url}")
            continue
        
        logger.info(f"Crawling: {url}")
        text, metadata = fetch_and_clean(url)
        
        if text is not None and len(text.strip()) > 0 and metadata is not None:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved {len(text)} characters to {output_file}")
            logger.info(f"Saved metadata to {meta_file}")
        else:
            logger.warning(f"No text extracted from {url}")
        
        # Be respectful - delay between requests
        time.sleep(1)
    
    logger.info("Voice corpus crawler completed")

if __name__ == "__main__":
    main()