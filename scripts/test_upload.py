"""
Test script to process a single markdown file and upload to Qdrant
"""
import os
import glob
from pathlib import Path
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import cohere

# Load environment variables
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "humanoid_ai_book_new_docs_test")

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

def chunk_text(text: str, max_chars: int = 1200) -> list:
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

def embed_text(text: str) -> list:
    """Create embedding for text using Cohere"""
    response = cohere_client.embed(
        model="embed-english-v3.0",
        input_type="search_document",
        texts=[text],
    )
    return response.embeddings[0]

def test_connection():
    """Test the connection to Qdrant and Cohere"""
    print("Testing Qdrant connection...")
    try:
        collections = qdrant_client.get_collections()
        print(f"[OK] Qdrant connection successful! Available collections: {[c.name for c in collections.collections]}")
    except Exception as e:
        print(f"[ERROR] Qdrant connection failed: {e}")
        return False

    print("Testing Cohere connection...")
    try:
        test_embedding = cohere_client.embed(
            model="embed-english-v3.0",
            input_type="search_document",
            texts=["test"],
        )
        print("[OK] Cohere connection successful!")
    except Exception as e:
        print(f"[ERROR] Cohere connection failed: {e}")
        return False

    return True

def test_single_file(file_path: str):
    """Test processing a single file"""
    print(f"\nTesting with file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Content length: {len(content)} characters")

    # Convert markdown to text
    text = markdown_to_text(content)
    print(f"Text length after conversion: {len(text)} characters")

    # Create chunks
    chunks = chunk_text(text[:2000])  # Only process first 2000 chars for test
    print(f"Number of chunks: {len(chunks)}")

    # Test embedding
    if chunks:
        sample_chunk = chunks[0][:200]  # First 200 chars of first chunk
        print(f"Sample chunk length: {len(sample_chunk)} characters")

        try:
            embedding = embed_text(sample_chunk)
            print(f"[OK] Embedding created successfully! Vector size: {len(embedding)}")
        except Exception as e:
            print(f"[ERROR] Embedding creation failed: {e}")
            return False

    return True

def test_qdrant_upload():
    """Test uploading to Qdrant"""
    print(f"\nTesting Qdrant upload to collection: {COLLECTION_NAME}")

    # Create test collection
    try:
        qdrant_client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except:
        print(f"Collection {COLLECTION_NAME} didn't exist, creating new one...")

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,  # Cohere embed-english-v3.0 dimension
            distance=Distance.COSINE
        )
    )
    print(f"[OK] Collection {COLLECTION_NAME} created successfully!")

    # Upload a test point
    test_text = "This is a test document for the Humanoid AI Textbook."
    vector = embed_text(test_text)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=1,
                vector=vector,
                payload={
                    "source_file": "test.md",
                    "title": "Test Document",
                    "text": test_text,
                    "chunk_id": 1
                }
            )
        ]
    )
    print("[OK] Test document uploaded to Qdrant successfully!")

    # Verify upload
    points = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1
    )
    print(f"[OK] Verified upload - found {len(points[0])} points in collection")

    return True

if __name__ == "__main__":
    print("Humanoid AI Textbook - Qdrant Upload Test")
    print("=" * 50)

    # Verify environment variables
    if not all([QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY]):
        print("❌ Error: Missing required environment variables!")
        print("- QDRANT_URL")
        print("- QDRANT_API_KEY")
        print("- COHERE_API_KEY")
        exit(1)

    print("[OK] Environment variables are set")

    # Test connections
    if not test_connection():
        exit(1)

    # Test with a single file
    test_file = "../frontend/docs/index.md"
    if not os.path.exists(test_file):
        print(f"❌ Test file does not exist: {test_file}")
        # Try to find any markdown file
        files = glob.glob("../frontend/docs/**/*.md", recursive=True)
        if files:
            test_file = files[0]
            print(f"Using alternative file: {test_file}")
        else:
            print("❌ No markdown files found!")
            exit(1)

    if not test_single_file(test_file):
        exit(1)

    # Test Qdrant upload
    if not test_qdrant_upload():
        exit(1)

    print(f"\n[SUCCESS] All tests passed! The upload process is working correctly.")
    print(f"You can now run the full script: python scripts/process_docs_to_qdrant.py")