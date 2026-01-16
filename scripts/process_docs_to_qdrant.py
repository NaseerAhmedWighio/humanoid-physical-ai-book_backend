"""
Script to process local markdown files from the docs directory and upload them to Qdrant
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
from fastembed import TextEmbedding
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
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "humanoid_ai_book_new")

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

def get_next_chunk_id(qdrant_client, collection_name):
    """Get the next available chunk ID by checking existing points in Qdrant"""
    try:
        # Get all points to find the highest existing ID
        # Scroll through all points to find the maximum ID
        offset = None
        max_id = 0
        while True:
            scroll_result = qdrant_client.scroll(
                collection_name=collection_name,
                limit=1000,  # Process in batches
                offset=offset,
                with_payload=False,
                with_vector=False
            )
            points, next_page = scroll_result

            if not points:
                break

            for point in points:
                if point.id > max_id:
                    max_id = point.id

            if next_page is None:
                break
            offset = next_page

        return max_id + 1 if max_id > 0 else 1
    except Exception as e:
        logger.warning(f"Error getting next chunk ID, starting from 1: {e}")
        return 1

# Initialize embedding model and Qdrant client (moved inside main to handle potential errors)
def initialize_clients():
    """Initialize embedding model and Qdrant client"""
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Connect to Qdrant with proper error handling
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30  # Add timeout to prevent hanging
    )

    return embedding_model, qdrant_client

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

def embed_text_with_retry(text: str, embedding_model, max_retries: int = 3) -> List[float]:
    """Create embedding for text using FastEmbed with retry logic"""
    for attempt in range(max_retries):
        try:
            embeddings = list(embedding_model.embed([text]))
            return embeddings[0].tolist()  # Convert to list for serialization
        except Exception as e:
            logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue
            else:
                raise e

def create_qdrant_collection(qdrant_client):
    """Create Qdrant collection if it doesn't exist"""
    try:
        # Check if collection exists
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' already exists. Using existing collection.")
        # Don't recreate the collection to preserve existing data
        return
    except Exception as e:
        logger.info(f"Collection '{COLLECTION_NAME}' does not exist. Creating...")

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,  # BGE-small-en-v1.5 dimension
            distance=Distance.COSINE
        )
    )
    logger.info(f"Collection '{COLLECTION_NAME}' created successfully!")

def save_chunk_to_qdrant_with_retry(chunk: str, chunk_id: int, source_file: str, title: str, embedding_model, qdrant_client, max_retries: int = 3):
    """Save a text chunk to Qdrant with retry logic"""
    for attempt in range(max_retries):
        try:
            vector = embed_text_with_retry(chunk, embedding_model)

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
            return True  # Success
        except Exception as e:
            logger.warning(f"Save attempt {attempt + 1} failed for chunk {chunk_id}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            else:
                logger.error(f"Failed to save chunk {chunk_id} after {max_retries} attempts: {e}")
                return False

def process_markdown_file(file_path: str, global_id: int, embedding_model, qdrant_client) -> int:
    """Process a single markdown file and add to Qdrant"""
    logger.info(f"Processing: {file_path}")

    # Extract title from filename or first heading
    filename = Path(file_path).stem
    title = filename.replace('-', ' ').replace('_', ' ').title()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return global_id

    # Convert markdown to text
    text = markdown_to_text(content)

    # Create chunks
    chunks = chunk_text(text)

    # Save each chunk to Qdrant
    chunks_processed = 0
    for i, chunk in enumerate(chunks):
        if chunk.strip():  # Only save non-empty chunks
            success = save_chunk_to_qdrant_with_retry(chunk, global_id, file_path, title, embedding_model, qdrant_client)
            if success:
                logger.info(f"  Saved chunk {global_id} (part {i+1}) from {file_path}")
                global_id += 1
                chunks_processed += 1
            else:
                logger.error(f"  Failed to save chunk {global_id} (part {i+1}) from {file_path}")
                global_id += 1  # Still increment ID to avoid conflicts

    logger.info(f"Completed processing {file_path} - {chunks_processed} chunks saved")
    return global_id

def process_docs_directory(docs_path: str = "../../frontend/docs"):
    """Process all markdown files in the docs directory"""
    # Convert to absolute path relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    abs_docs_path = os.path.join(script_dir, docs_path)
    abs_docs_path = os.path.abspath(abs_docs_path)
    logger.info(f"Starting to process markdown files from: {abs_docs_path}")

    # Initialize clients
    try:
        embedding_model, qdrant_client = initialize_clients()
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return

    # Create Qdrant collection
    create_qdrant_collection(qdrant_client)

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

    # Get the next chunk ID to continue from where we left off
    global_id = get_next_chunk_id(qdrant_client, COLLECTION_NAME)
    logger.info(f"Starting upload from chunk ID: {global_id}")

    success_count = 0
    error_count = 0

    for file_path in remaining_files:
        try:
            old_global_id = global_id
            global_id = process_markdown_file(file_path, global_id, embedding_model, qdrant_client)
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

    logger.info(f"\nProcessing completed!")
    logger.info(f"Files processed successfully: {success_count}")
    logger.info(f"Files with errors: {error_count}")
    logger.info(f"Total chunks stored: {global_id - 1}")

if __name__ == "__main__":
    logger.info("Humanoid AI Textbook - Docs to Qdrant Processor (Resumable)")
    logger.info("=" * 60)

    # Verify environment variables
    if not all([QDRANT_URL, QDRANT_API_KEY]):
        logger.error("Error: Missing required environment variables!")
        logger.error("- QDRANT_URL")
        logger.error("- QDRANT_API_KEY")
        exit(1)

    process_docs_directory()