#!/usr/bin/env python
"""
Script to test and initialize Qdrant connection for RAG functionality
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding
import logging

def test_qdrant_connection():
    """Test Qdrant connection and ensure the collection exists"""
    print("Testing Qdrant Connection...")

    # Load environment variables
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)

    print(f"Qdrant URL: {qdrant_url}")
    print(f"API Key available: {'Yes' if qdrant_api_key else 'No'}")

    try:
        # Connect to Qdrant
        if qdrant_url and qdrant_url.startswith("https://"):
            # For HTTPS/secure connections
            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
        else:
            # For HTTP/insecure connections (local development)
            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                prefer_grpc=False
            )

        print("+ Successfully connected to Qdrant!")

        # Test connection by getting collections
        collections = client.get_collections()
        print(f"Available collections: {[coll.name for coll in collections.collections]}")

        # Check if our target collection exists
        collection_name = "humanoid_ai_book_new"
        collection_exists = any(coll.name == collection_name for coll in collections.collections)

        if not collection_exists:
            print(f"- Collection '{collection_name}' does not exist")

            # Create the collection with the proper vector size for BGE small model
            print(f"Creating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # BGE small model generates 384-dimensional vectors
                    distance=models.Distance.COSINE
                )
            )
            print(f"+ Collection '{collection_name}' created successfully!")
        else:
            print(f"+ Collection '{collection_name}' exists")

            # Get collection info
            collection_info = client.get_collection(collection_name)
            print(f"Collection points count: {collection_info.points_count}")
            print(f"Vector size: {collection_info.config.params.vectors.size}")
            print(f"Distance: {collection_info.config.params.vectors.distance}")

        # Test embedding
        print("\nTesting embedding functionality...")
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        test_text = "This is a test document for RAG functionality."
        embeddings = list(embedding_model.embed([test_text]))
        test_embedding = embeddings[0].tolist()

        print(f"+ Embedding generated successfully. Vector dimension: {len(test_embedding)}")

        # Test search
        print("\nTesting search functionality...")
        search_results = client.search(
            collection_name=collection_name,
            query_vector=test_embedding,
            limit=1
        )

        print(f"+ Search completed. Found {len(search_results)} results")

        return True

    except Exception as e:
        print(f"- Error connecting to Qdrant: {e}")
        print("Make sure Qdrant server is running and accessible")
        print(f"   Qdrant should be running at: {qdrant_url}")
        return False

def check_content_ingestion():
    """Check if content has been ingested into Qdrant"""
    print("\nChecking content ingestion...")

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)

    try:
        if qdrant_url and qdrant_url.startswith("https://"):
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        collection_name = "humanoid_ai_book_new"

        # Get collection info
        collection_info = client.get_collection(collection_name)
        print(f"Collection '{collection_name}' has {collection_info.points_count} points")

        if collection_info.points_count == 0:
            print("No content has been ingested yet. You need to ingest content to enable RAG functionality.")
            print("Run the content ingestion script to populate the vector database.")
            return False
        else:
            print(f"Content has been ingested. Ready for RAG queries.")
            # Show a sample point to verify content
            sample_points = client.scroll(
                collection_name=collection_name,
                limit=1
            )
            if sample_points[0]:
                sample_point = sample_points[0][0]
                content = sample_point.payload.get('text', sample_point.payload.get('content', 'N/A'))[:100] + "..."
                print(f"Sample content: {content}")
            return True

    except Exception as e:
        print(f"Error checking content: {e}")
        return False

def main():
    print("Qdrant Connection and Content Checker")
    print("=" * 50)

    # Test connection
    connection_ok = test_qdrant_connection()

    if connection_ok:
        # Check content
        content_ok = check_content_ingestion()

        if content_ok:
            print("\nRAG system is ready for use!")
        else:
            print("\nRAG system needs content to be ingested before it can work properly.")
            print("\nTo ingest content, you can run:")
            print("   python scripts/process_docs_to_qdrant.py")
    else:
        print("\nRAG system is not ready. Please fix Qdrant connection issues first.")

if __name__ == "__main__":
    main()