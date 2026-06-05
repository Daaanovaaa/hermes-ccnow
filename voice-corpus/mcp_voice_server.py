#!/usr/bin/env python3
"""
MCP Server for CCN Voice Corpus
Exposes voice corpus querying and management via MCP protocol
"""
import os
import logging
import subprocess
import sys
from typing import List, Dict, Any
from fastmcp import FastMCP
import chromadb

# Setup directories
BASE_DIR = "/root/hermes-ccnow/voice-corpus"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "corpus.db")
URLS_FILE = os.path.join(BASE_DIR, "urls.txt")

# Ensure directories exist
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

# Initialize FastMCP server
mcp = FastMCP("CCN Voice Corpus")

def run_script(script_name: str) -> bool:
    """Run a Python script in the voice-corpus directory"""
    script_path = os.path.join(BASE_DIR, script_name)
    try:
        logger.info(f"Running script: {script_name}")
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            logger.info(f"Script {script_name} completed successfully")
            if result.stdout:
                logger.debug(f"Script output: {result.stdout}")
            return True
        else:
            logger.error(f"Script {script_name} failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Script stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Failed to run script {script_name}: {str(e)}")
        return False

@mcp.tool()
def query_ccn_voice(topic: str, content_type: str = "general", n: int = 3) -> str:
    """
    Query the CCN voice corpus for relevant content
    
    Args:
        topic: The topic to search for
        content_type: Type of content (social, email, brand, general)
        n: Number of chunks to return
    
    Returns:
        Concatenated string of top n relevant chunks
    """
    logger.info(f"MCP query: topic={topic}, content_type={content_type}, n={n}")
    
    # Import and use the query function from query_voice.py
    sys.path.append(BASE_DIR)
    try:
        from query_voice import query_ccn_voice as query_func
        result = query_func(topic, content_type, n)
        logger.info(f"Query returned {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Failed to query voice corpus: {str(e)}")
        return f"Error querying voice corpus: {str(e)}"

@mcp.tool()
def add_url(url: str) -> Dict[str, Any]:
    """
    Add a URL to the corpus and process it immediately
    
    Args:
        url: The URL to add
    
    Returns:
        Dictionary with status and details
    """
    logger.info(f"MCP add_url: {url}")
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return {
            "status": "error",
            "message": "URL must start with http:// or https://"
        }
    
    # Add to urls.txt
    try:
        with open(URLS_FILE, 'a') as f:
            f.write(url + '\n')
        logger.info(f"Added URL to {URLS_FILE}")
    except Exception as e:
        logger.error(f"Failed to write to urls.txt: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to write to urls.txt: {str(e)}"
        }
    
    # Run crawler for new URLs (it will skip already crawled ones)
    crawler_success = run_script("crawler.py")
    if not crawler_success:
        return {
            "status": "error",
            "message": "Failed to run crawler"
        }
    
    # Run embed to process new content
    embed_success = run_script("embed.py")
    if not embed_success:
        return {
            "status": "error",
            "message": "Failed to run embedder"
        }
    
    return {
        "status": "success",
        "message": f"URL added and processed: {url}",
        "url": url
    }

@mcp.tool()
def list_corpus() -> Dict[str, Any]:
    """
    List corpus statistics and information
    
    Returns:
        Dictionary with corpus details
    """
    logger.info("MCP list_corpus")
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=DB_PATH)
        try:
            collection = client.get_collection(name="ccn_voice")
        except:
            return {
                "status": "error",
                "message": "Collection 'ccn_voice' not found. Run embed.py first."
            }
        
        # Get collection stats
        count = collection.count()
        
        # Get a sample of metadata to show sources
        sample_size = min(10, count)
        if count > 0:
            sample = collection.get(
                limit=sample_size,
                include=['metadatas']
            )
            sources = set()
            for meta in sample['metadatas']:
                if meta and 'source' in meta:
                    sources.add(meta['source'])
        else:
            sources = set()
        
        # Read urls.txt to see what's queued
        try:
            with open(URLS_FILE, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            url_count = len(urls)
        except:
            urls = []
            url_count = 0
        
        # Get last modified time of the database
        try:
            db_stat = os.stat(DB_PATH)
            import datetime
            last_updated = datetime.datetime.fromtimestamp(db_stat.st_mtime).isoformat()
        except:
            last_updated = "unknown"
        
        return {
            "status": "success",
            "collection": "ccn_voice",
            "total_chunks": count,
            "unique_sources_sampled": list(sources)[:10],
            "queued_urls": url_count,
            "last_updated": last_updated,
            "database_path": DB_PATH
        }
        
    except Exception as e:
        logger.error(f"Failed to list corpus: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to list corpus: {str(e)}"
        }

def main():
    """Run the MCP server"""
    logger.info("Starting CCN Voice Corpus MCP Server on port 8765")
    logger.info("Available tools:")
    logger.info("  - query_ccn_voice(topic, content_type, n)")
    logger.info("  - add_url(url)")
    logger.info("  - list_corpus()")
    
    # Run the server
    mcp.run(transport="sse", host="0.0.0.0", port=8765)

if __name__ == "__main__":
    main()