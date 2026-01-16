"""
Script to check the status of the Qdrant upload process
"""
import os
import json
import glob
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "humanoid_ai_book_new")

def check_upload_status():
    """Check the status of the upload process"""
    print("Checking Qdrant upload status...")
    print("="*50)

    # Connect to Qdrant
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    # Check collection info
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Points count: {collection_info.points_count}")
        print(f"Vectors count: {collection_info.vectors_count}")
    except Exception as e:
        print(f"Collection {COLLECTION_NAME} does not exist or error occurred: {e}")
        return

    # Check checkpoint file
    checkpoint_file = "upload_checkpoint.json"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            processed_files = json.load(f)
        print(f"\nFiles already processed: {len(processed_files)}")
    else:
        processed_files = []
        print(f"\nNo checkpoint file found - no files processed yet")

    # Count total markdown files
    abs_docs_path = os.path.abspath("../frontend/docs")
    all_markdown_files = glob.glob(f"{abs_docs_path}/**/*.md", recursive=True)
    print(f"Total markdown files to process: {len(all_markdown_files)}")
    print(f"Remaining files to process: {len(all_markdown_files) - len(processed_files)}")

    # Show some example files
    if processed_files:
        print(f"\nExample processed files:")
        for file in processed_files[:5]:  # Show first 5
            print(f"  - {os.path.basename(file)}")

    print(f"\nExample remaining files:")
    remaining_files = [f for f in all_markdown_files if f not in processed_files]
    for file in remaining_files[:5]:  # Show first 5
        print(f"  - {os.path.basename(file)}")

if __name__ == "__main__":
    check_upload_status()