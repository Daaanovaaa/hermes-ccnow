#!/usr/bin/env python3
"""
Embedding Generator for CCN Voice Corpus
Creates embeddings from text files and stores them in ChromaDB

Upgraded: Auto-detects rich metadata from filename + chunk headers
Metadata dimensions:
  - content_type: magazine | book | video_transcript | blog | website | reference
  - language: EN | ES | UNK
  - source_url: extracted from chunk header
  - date_published: YYYYMMDD integer for time-aware retrieval
  - year: integer year for filtering
"""
import os
import logging
import requests
import re
from typing import List
import chromadb

# Setup directories
BASE_DIR = "/root/hermes-ccnow/voice-corpus"
RAW_TEXT_DIR = os.path.join(BASE_DIR, "raw_text")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "corpus.db")

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

# Configuration
OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
COLLECTION_NAME = "ccn_voice"
CHUNK_SIZE = 400
OVERLAP_SIZE = 50


# ─────────────────────────────────────────────
# METADATA DETECTION — The Dewey Decimal Layer
# ─────────────────────────────────────────────

# Magazine publish dates — Issue number → YYYYMMDD
MAGAZINE_PUBLISH_DATES = {
    1:  20250301,  # March 2025
    2:  20250401,  # April 2025
    3:  20250501,  # May 2025
    4:  20250601,  # June 2025
    5:  20250701,  # July 2025
    6:  20250801,  # August 2025
    7:  20250901,  # September 2025
    8:  20251001,  # October 2025
    9:  20251101,  # November 2025
    10: 20251201,  # December 2025
    11: 20260101,  # January 2026
    12: 20260201,  # February 2026
    13: 20260301,  # March 2026
    14: 20260401,  # April 2026
}

def get_magazine_publish_date(filename: str) -> tuple:
    """
    Extract issue number from magazine filename and return
    actual publish date as (date_int, year_int).
    Returns (0, 0) if not found.
    """
    fn = filename.lower()

    # Match "Issue_N" or "Issue N" pattern
    issue_match = re.search(r'issue[_\s-]*(\d+)', fn, re.IGNORECASE)
    if issue_match:
        issue_num = int(issue_match.group(1))
        date_int = MAGAZINE_PUBLISH_DATES.get(issue_num, 0)
        year_int = date_int // 10000 if date_int else 0
        return (date_int, year_int)

    # March 2025 original (no issue number in filename)
    if "march_2025" in fn or ("march" in fn and "2025" in fn):
        return (20250301, 2025)

    return (0, 0)

def detect_content_type(filename: str) -> tuple:
    """
    Detect content type and human-readable label from filename.
    Returns (content_type, content_label)
    """
    fn = filename.lower()

    if "la_fortaleza" in fn or ("issue" in fn and "official" in fn) or "copy_of_official" in fn:
        return ("magazine", "La Fortaleza Magazine PR")

    if "superposicion" in fn or "superposicio" in fn:
        return ("book", "Superposición Book 1")

    if fn.startswith("yt_") or "conscious_mentality_movie" in fn:
        return ("video_transcript", "YouTube / Video Transcript")

    if "faaaith_org_blog" in fn:
        return ("blog", "faaaith.org Blog")

    if "faaaith_org" in fn:
        return ("website", "faaaith.org Website")

    if "wayback_" in fn:
        return ("archive", "Web Archive")

    if "speakerhub" in fn or "substack" in fn:
        return ("profile", "Speaker / Author Profile")

    return ("reference", "Reference Material")


def extract_header_metadata(text: str) -> dict:
    """
    Extract metadata from YAML-style chunk headers.
    Handles headers like:
      ---
      source: ...
      language: EN
      source_url: https://...
      date_processed: 20260601
      ---
    """
    meta = {
        "language": "UNK",
        "source_url": "",
        "date_published": 0,
        "year": 0,
        "chunk_number": 0,
    }

    # Only scan the first 500 chars for the header
    header_region = text[:500]

    # Language
    lang_match = re.search(r'language:\s*(EN|ES|UNK)', header_region, re.IGNORECASE)
    if lang_match:
        meta["language"] = lang_match.group(1).upper()

    # Source URL
    url_match = re.search(r'source_url:\s*(https?://\S+)', header_region)
    if url_match:
        meta["source_url"] = url_match.group(1).strip()

    # Date processed (stored as YYYYMMDD integer)
    date_match = re.search(r'date_processed:\s*(\d{8})', header_region)
    if date_match:
        date_int = int(date_match.group(1))
        meta["date_published"] = date_int
        meta["year"] = date_int // 10000  # Extract YYYY from YYYYMMDD

    # Chunk number
    chunk_match = re.search(r'chunk:\s*(\d+)', header_region)
    if chunk_match:
        meta["chunk_number"] = int(chunk_match.group(1))

    # Fallback year from filename patterns like "2025" or "2026"
    if meta["year"] == 0:
        year_match = re.search(r'(202[0-9])', header_region)
        if year_match:
            meta["year"] = int(year_match.group(1))

    return meta


def infer_year_from_filename(filename: str) -> int:
    """Extract year from filename as fallback."""
    match = re.search(r'(202[0-9])', filename)
    if match:
        return int(match.group(1))
    # Video transcripts and blog posts without dates
    return 0


# ─────────────────────────────────────────────
# CORE FUNCTIONS (unchanged from original)
# ─────────────────────────────────────────────

def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("Ollama is not responding")
            return False
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        model_found = MODEL_NAME in models or f"{MODEL_NAME}:latest" in models
        if not model_found:
            logger.error(f"Model {MODEL_NAME} not found. Available: {models}")
            return False
        logger.info(f"Ollama is running with model {MODEL_NAME} available")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama: {str(e)}")
        return False


def get_embedding(text: str) -> List[float]:
    try:
        payload = {"model": MODEL_NAME, "prompt": text}
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        embedding = data.get('embedding')
        if embedding is None:
            logger.error(f"No embedding returned: {data}")
            return None
        return embedding
    except Exception as e:
        logger.error(f"Failed to get embedding: {str(e)}")
        return None


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if end >= text_length:
            break
    return chunks


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    logger.info("Starting embedding generation — CCN Knowledge Architecture v2")
    logger.info("Metadata dimensions: content_type | language | source_url | date_published | year")

    if not check_ollama():
        return

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        try:
            client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
        except:
            pass
        collection = client.create_collection(name=COLLECTION_NAME)
        logger.info(f"Created new collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {str(e)}")
        return

    try:
        files = [f for f in os.listdir(RAW_TEXT_DIR) if f.endswith('.txt')]
        logger.info(f"Found {len(files)} text files to process")
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        return

    total_chunks = 0
    total_files_processed = 0

    # Print classification preview
    logger.info("=== Content Classification Preview ===")
    type_counts = {}
    for filename in files:
        ct, _ = detect_content_type(filename)
        type_counts[ct] = type_counts.get(ct, 0) + 1
    for ct, count in sorted(type_counts.items()):
        logger.info(f"  {ct}: {count} files")
    logger.info("=====================================")

    for filename in files:
        filepath = os.path.join(RAW_TEXT_DIR, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            if not text.strip():
                logger.warning(f"Empty file: {filename}")
                continue

            # Detect content type from filename
            content_type, content_label = detect_content_type(filename)

            # Extract metadata from chunk header
            header_meta = extract_header_metadata(text)

            # For magazines: use actual publish date, not processing date
            if content_type == "magazine":
                pub_date, pub_year = get_magazine_publish_date(filename)
                if pub_date > 0:
                    header_meta["date_published"] = pub_date
                    header_meta["year"] = pub_year

            # Year fallback from filename if header has none
            year = header_meta["year"]
            if year == 0:
                year = infer_year_from_filename(filename)

            # Chunk the text
            chunks = chunk_text(text)
            logger.info(f"File {filename}: {len(chunks)} chunks | "
                       f"type={content_type} | lang={header_meta['language']} | year={year}")

            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_{i}"

                embedding = get_embedding(chunk)
                if embedding is None:
                    logger.error(f"Failed to get embedding for chunk {chunk_id}")
                    continue

                # Full metadata for this chunk
                meta_dict = {
                    "source":         filename,
                    "content_type":   content_type,
                    "content_label":  content_label,
                    "language":       header_meta["language"],
                    "source_url":     header_meta["source_url"],
                    "date_published": header_meta["date_published"],
                    "year":           year,
                    "chunk_index":    i,
                    "chunk_number":   header_meta["chunk_number"],
                }

                try:
                    collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        ids=[chunk_id],
                        metadatas=[meta_dict]
                    )
                    total_chunks += 1
                except Exception as e:
                    logger.error(f"Failed to store chunk {chunk_id}: {str(e)}")

            total_files_processed += 1
            logger.info(f"Processed {filename} ({total_files_processed}/{len(files)})")

        except Exception as e:
            logger.error(f"Failed to process file {filename}: {str(e)}")

    logger.info(f"Embedding generation completed. "
                f"Files processed: {total_files_processed}, "
                f"Chunks embedded: {total_chunks}")
    logger.info("Knowledge Architecture dimensions active: "
                "content_type | content_label | language | source_url | date_published | year")

if __name__ == "__main__":
    main()