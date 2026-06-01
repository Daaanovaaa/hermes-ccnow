#!/usr/bin/env python3
"""
Voice Query Interface for CCN Voice Corpus
Provides function to query the voice corpus for content generation
"""
import os
import logging
import requests
import json
from typing import List
import chromadb
from chromadb.config import Settings

# Setup directories
BASE_DIR = "/root/hermes-ccnow/voice-corpus"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "corpus.db")

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

# Configuration
OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
COLLECTION_NAME = "ccn_voice"

def check_ollama():
    """Check if Ollama is running and the model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("Ollama is not responding")
            return False
        
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        # Check for exact match or model with :latest suffix
        model_found = MODEL_NAME in models or f"{MODEL_NAME}:latest" in models
        if not model_found:
            logger.error(f"Model {MODEL_NAME} not found in Ollama")
            return False
        
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama: {str(e)}")
        return False

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using Ollama"""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": text
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        embedding = data.get('embedding')
        if embedding is None:
            logger.error(f"No embedding returned from Ollama: {data}")
            return None
        return embedding
    except Exception as e:
        logger.error(f"Failed to get embedding: {str(e)}")
        return None

def query_ccn_voice(topic: str, content_type: str = "general", n: int = 3, recency_filter: str = "historical") -> str:
    """
    Query the CCN voice corpus for relevant content
    
    Args:
        topic: The topic to search for
        content_type: Type of content (social, email, brand, general)
        n: Number of chunks to return
        recency_filter: Filter for recency - "current" (2024 onwards) or "historical" (all)
    
    Returns:
        Concatenated string of top n relevant chunks
    """
    logger.info(f"Querying voice corpus for topic: {topic}, content_type: {content_type}, n: {n}, recency_filter: {recency_filter}")
    
    # Check Ollama
    if not check_ollama():
        logger.error("Ollama not available")
        return ""
    
    # Initialize ChromaDB
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        logger.info(f"Connected to collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {str(e)}")
        return ""
    
    # Get embedding for the query
    query_embedding = get_embedding(topic)
    if query_embedding is None:
        logger.error("Failed to get query embedding")
        return ""
    
    # Query the collection with metadata filtering
    try:
        # Build where clause — ChromaDB requires $and when combining multiple conditions
        where_parts = []

        if recency_filter == "current":
            where_parts.append({"year": {"$gte": 2024}})

        if content_type and content_type != "general":
            where_parts.append({"content_type": {"$eq": content_type}})

        if len(where_parts) == 0:
            where_clause = None
        elif len(where_parts) == 1:
            where_clause = where_parts[0]
        else:
            where_clause = {"$and": where_parts}

        query_kwargs = dict(
            query_embeddings=[query_embedding],
            n_results=n,
            include=['documents', 'distances', 'metadatas'],
        )
        if where_clause:
            query_kwargs["where"] = where_clause

        results = collection.query(**query_kwargs)
        
        if not results['ids'] or len(results['ids'][0]) == 0:
            logger.warning("No results found for query")
            return ""
        
        # Combine the documents
        documents = results['documents'][0]
        distances = results['distances'][0]
        metadatas = results['metadatas'][0]
        
        logger.info(f"Found {len(documents)} relevant chunks")
        for i, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas)):
            logger.debug(f"Result {i+1}: distance={dist:.4f}, source={meta.get('source')}, year={meta.get('year')}")
        
        # Join documents with spacing
        combined_text = "\n\n---\n\n".join(documents)
        return combined_text
        
    except Exception as e:
        logger.error(f"Failed to query collection: {str(e)}")
        return ""

# For testing
if __name__ == "__main__":
    test_topic = "superposición book"
    result = query_ccn_voice(test_topic, "general", 3, "historical")
    print(f"Query: {test_topic}")
    print(f"Result length: {len(result)} characters")
    if result:
        print(result)