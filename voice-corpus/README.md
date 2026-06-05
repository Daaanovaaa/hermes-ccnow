# CCN Voice Corpus System

This system builds and maintains a voice corpus from Carlos "DaNova" Villanueva's 10-year ministry library to enable Hermes to generate content in his exact voice.

## Directory Structure
```
/root/hermes-ccnow/voice-corpus/
├── raw_text/           # Cleaned text content from web pages, YouTube transcripts, Wayback Machine
├── logs/               # Log files for all operations
├── corpus.db           # ChromaDB database with voice embeddings
├── urls.txt            # List of URLs to crawl (one per line)
├── crawler.py          # Web page crawler
├── youtube_transcripts.py  # YouTube transcript downloader
├── wayback_crawler.py    # Wayback Machine archival crawler
├── embed.py            # Text chunker and embedder using Ollama + ChromaDB
├── query_voice.py      # Voice querying interface
├── mcp_voice_server.py # MCP server for external access
└── README.md           # This file
```

## Components

### 1. URLs File (`urls.txt`)
Contains the list of web pages to crawl, one URL per line. Initially populated with:
- faaaith.org and its subpages
- danova.substack.com
- speakerhub.com profile

### 2. Crawlers
- **crawler.py**: Fetches web pages from `urls.txt`, strips HTML, saves clean text to `raw_text/`
- **youtube_transcripts.py**: Downloads transcripts from 3 YouTube channels using yt-dlp
- **wayback_crawler.py**: Fetches archived snapshots of faaate.com from Wayback Machine API

### 3. Embedding System (`embed.py`)
- Reads all `.txt` files from `raw_text/`
- Chunks text into 400-token segments with 50-token overlap
- Generates embeddings using `nomic-embed-text` via Ollama (localhost:11434)
- Stores in ChromaDB at `corpus.db` with collection name `ccn_voice`
- Skips already embedded documents

### 4. Query Interface (`query_voice.py`)
- Function: `query_ccn_voice(topic, content_type="general", n=3)`
- Embeds topic query via Ollama
- Returns top n chunks from ChromaDB as a single string
- Used by Hermes MCP for content generation

### 5. MCP Server (`mcp_voice_server.py`)
- FastMCP server running on port 8765
- Exposes `query_ccn_voice` as MCP tool
- Exposes Telegram commands:
  - `/addurl [url]` - adds URL to urls.txt, runs crawler and embed immediately
  - `/corpus list` - returns corpus statistics and information

### 6. Daily Pipeline (Cron Job)
Runs every day at 3:00 AM AST (07:00 UTC):
1. `youtube_transcripts.py` - Download new YouTube transcripts
2. `crawler.py` - Crawl new/updated web pages
3. `wayback_crawler.py` - Fetch new Wayback Machine snapshots
4. `embed.py` - Generate embeddings for new/updated content

All operations are logged to `logs/corpus.log`.

## Usage

### Manually Adding Content via Telegram
Hermes exposes these Telegram commands when the MCP server is running:

**/addurl [url]**
- Adds the URL to `urls.txt`
- Immediately runs the crawler for that URL
- Runs the embedder to process new content
- Example: `/addurl https://faaaith.org/new-sermon`

**/corpus list**
- Returns corpus statistics:
  - Total embedded chunks
  - Sample of unique sources
  - Number of queued URLs in urls.txt
  - Last updated timestamp
  - Database path

### Manual Pipeline Execution
To run the full pipeline manually from bash:

```bash
cd /root/hermes-ccnow/voice-corpus

# Run all components in sequence
python3 youtube_transcripts.py
python3 crawler.py
python3 wayback_crawler.py
python3 embed.py

# Or run individually as needed
```

### Checking Status
- View logs: `tail -f /root/hermes-ccnow/voice-corpus/logs/corpus.log`
- Check database: The ChromaDB is stored at `/root/hermes-ccnow/voice-corpus/corpus.db`
- See raw text: Files in `/root/hermes-ccnow/voice-corpus/raw_text/`

## Requirements
The system requires these Python packages:
- chromadb
- requests
- beautifulsoup4
- yt-dlp

And these external services:
- **Ollama** running with `nomic-embed-text` model:
  ```bash
  ollama pull nomic-embed-text
  ollama serve
  ```

## Notes
- The crawler respects rate limits with 1-second delays between requests
- All components skip already processed content to avoid redundant work
- The system is designed to run continuously, growing the voice corpus over time
- For optimal results, ensure Ollama is running with sufficient resources for embedding generation