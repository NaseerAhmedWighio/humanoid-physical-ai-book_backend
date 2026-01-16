"""
Script to process local markdown files from the docs directory and upload them to Qdrant
with resume capability and rate limit handling
"""
import os
import glob
import time
import json
from pathlib import Path
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import cohere
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "humanoid_ai_book_new")

# Initialize clients
cohere_client = cohere.Client(COHERE_API_KEY)
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def markdown_to_text(md_content: str) -> str:
    """Convert markdown content to plain text"""
    # Convert markdown to HTML
    html = markdown.markdown(md_content)
    # Parse HTML and extract text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

def chunk_text(text: str, max_chars: int = 1200) -> List[str]:
    """Split text into chunks of maximum length"""
    chunks = []
    while len(text) > max_chars:
        # Try to split at sentence boundaries
        split_pos = text[:max_chars].rfind('. ')
        if split_pos == -1:
            # If no sentence boundary found, split at max_chars
            split_pos = max_chars
        chunks.append(text[:split_pos + 1])
        text = text[split_pos + 1:].lstrip()
    if text:
        chunks.append(text)
    return chunks

def embed_text_with_retry(text: str, max_retries: int = 5) -> List[float]:
    """Create embedding for text using Cohere with retry logic for rate limits"""
    for attempt in range(max_retries):
        try:
            response = cohere_client.embed(
                model="embed-english-v3.0",
                input_type="search_document",
                texts=[text],
            )
            # Add a small delay to respect rate limits
            time.sleep(0.1)
            return response.embeddings[0]
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate" in error_msg or "limit" in error_msg:
                wait_time = (2 ** attempt) + 1  # Exponential backoff
                logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Embedding error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)

    raise Exception(f"Failed to embed text after {max_retries} attempts")

def create_qdrant_collection():
    """Create Qdrant collection if it doesn't exist"""
    try:
        # Check if collection exists
        qdrant_client.get_collection(COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' already exists. Recreating...")
        qdrant_client.delete_collection(COLLECTION_NAME)
    except:
        logger.info(f"Collection '{COLLECTION_NAME}' does not exist. Creating...")

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,  # Cohere embed-english-v3.0 dimension
            distance=Distance.COSINE
        )
    )
    logger.info(f"Collection '{COLLECTION_NAME}' created successfully!")

def save_chunk_to_qdrant(chunk: str, chunk_id: int, source_file: str, title: str = ""):
    """Save a text chunk to Qdrant"""
    vector = embed_text_with_retry(chunk)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "source_file": source_file,
                    "title": title,
                    "text": chunk,
                    "chunk_id": chunk_id
                }
            )
        ]
    )

def process_markdown_file(file_path: str, global_id: int) -> int:
    """Process a single markdown file and add to Qdrant"""
    logger.info(f"Processing: {file_path}")

    # Extract title from filename or first heading
    filename = Path(file_path).stem
    title = filename.replace('-', ' ').replace('_', ' ').title()

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert markdown to text
    text = markdown_to_text(content)

    # Create chunks
    chunks = chunk_text(text)

    # Save each chunk to Qdrant
    chunks_processed = 0
    for i, chunk in enumerate(chunks):
        if chunk.strip():  # Only save non-empty chunks
            try:
                save_chunk_to_qdrant(chunk, global_id, file_path, title)
                logger.info(f"  Saved chunk {global_id} (part {i+1}) from {file_path}")
                global_id += 1
                chunks_processed += 1
            except Exception as e:
                logger.error(f"Error saving chunk {global_id} from {file_path}: {e}")
                # Continue with next chunk instead of failing the whole file
                global_id += 1

    logger.info(f"Completed processing {file_path} - {chunks_processed} chunks saved")
    return global_id

def load_processed_files():
    """Load list of already processed files from a checkpoint file"""
    checkpoint_file = "upload_checkpoint.json"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return []

def save_processed_file(file_path):
    """Save processed file to checkpoint"""
    checkpoint_file = "upload_checkpoint.json"
    processed_files = load_processed_files()
    if file_path not in processed_files:
        processed_files.append(file_path)
        with open(checkpoint_file, 'w') as f:
            json.dump(processed_files, f)

def process_docs_directory(docs_path: str = "../frontend/docs"):
    """Process all markdown files in the docs directory"""
    # Convert to absolute path to handle execution from any directory
    abs_docs_path = os.path.abspath(docs_path)
    logger.info(f"Starting to process markdown files from: {abs_docs_path}")

    # Create Qdrant collection
    create_qdrant_collection()

    # Find all markdown files using absolute path
    markdown_files = glob.glob(f"{abs_docs_path}/**/*.md", recursive=True)
    logger.info(f"Found {len(markdown_files)} markdown files")

    if not markdown_files:
        logger.error("No markdown files found!")
        logger.info("Make sure you're running this script from the backend directory")
        logger.info("Or verify that markdown files exist in the docs directory")
        return

    # Load already processed files
    processed_files = load_processed_files()
    logger.info(f"Resuming from checkpoint - {len(processed_files)} files already processed")

    # Filter out already processed files
    remaining_files = [f for f in markdown_files if f not in processed_files]
    logger.info(f"{len(remaining_files)} files remaining to process")

    if not remaining_files:
        logger.info("All files have already been processed!")
        return

    # Find the next chunk ID by checking existing points in Qdrant
    try:
        # Get the highest existing ID to continue from there
        scroll_result = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1,
            with_payload=False,
            with_vector=False
        )
        points, next_page = scroll_result
        if points:
            # Get the max ID currently in the collection
            max_id = max(point.id for point in points)
            global_id = max_id + 1
        else:
            global_id = 1
    except:
        global_id = 1  # Start from 1 if collection is empty or error occurs

    logger.info(f"Starting upload from chunk ID: {global_id}")

    success_count = 0
    error_count = 0

    for file_path in remaining_files:
        try:
            old_global_id = global_id
            global_id = process_markdown_file(file_path, global_id)
            chunks_saved = global_id - old_global_id

            if chunks_saved > 0:
                save_processed_file(file_path)
                success_count += 1
                logger.info(f"Successfully processed {file_path} - {chunks_saved} chunks")
            else:
                # Still mark as processed if no chunks were saved (empty file)
                save_processed_file(file_path)

        except Exception as e:
            logger.error(f"Fatal error processing {file_path}: {e}")
            error_count += 1

            # If it's a rate limit issue, we should stop and resume later
            if "rate" in str(e).lower() or "limit" in str(e).lower() or "429" in str(e):
                logger.error("Rate limit reached. Stopping to avoid further errors. Resume later.")
                break

    logger.info(f"\nProcessing completed!")
    logger.info(f"Files processed successfully: {success_count}")
    logger.info(f"Files with errors: {error_count}")
    logger.info(f"Total chunks stored: {global_id - 1}")

if __name__ == "__main__":
    logger.info("Humanoid AI Textbook - Docs to Qdrant Processor (Resumable)")
    logger.info("=" * 60)

    # Verify environment variables
    if not all([QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY]):
        logger.error("Error: Missing required environment variables!")
        logger.error("- QDRANT_URL")
        logger.error("- QDRANT_API_KEY")
        logger.error("- COHERE_API_KEY")
        exit(1)

    process_docs_directory()