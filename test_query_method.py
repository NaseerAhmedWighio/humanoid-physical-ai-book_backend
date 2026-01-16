#!/usr/bin/env python3
"""
Test script to figure out the correct Qdrant query method API
"""

import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_query_method_api():
    """Test different ways to call the query method"""
    print("Testing Qdrant query method API...")

    try:
        from qdrant_client import QdrantClient
        from fastembed import TextEmbedding

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            print("QDRANT_URL not set")
            return False

        # Initialize client
        if qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # Initialize embedding model
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        test_text = "humanoid robotics"
        embeddings = list(embedding_model.embed([test_text]))
        query_vector = embeddings[0].tolist()

        print(f"Test text: '{test_text}'")
        print(f"Generated vector of length: {len(query_vector)}")

        # Test 1: query method with query_vector
        print("\n1. Testing query method with query_vector parameter...")
        try:
            result = qdrant.query(
                collection_name="humanoid_ai_book_new",
                query_vector=query_vector,
                limit=2
            )
            print(f"   SUCCESS: Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
        except Exception as e1:
            print(f"   FAILED: {e1}")

        # Test 2: query method with query parameter
        print("\n2. Testing query method with query parameter...")
        try:
            result = qdrant.query(
                collection_name="humanoid_ai_book_new",
                query=query_vector,
                limit=2
            )
            print(f"   SUCCESS: Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
        except Exception as e2:
            print(f"   FAILED: {e2}")

        # Test 3: query method with query_text parameter (as mentioned in the error)
        print("\n3. Testing query method with query_text parameter...")
        try:
            result = qdrant.query(
                collection_name="humanoid_ai_book_new",
                query_text=test_text,
                limit=2
            )
            print(f"   SUCCESS: Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
        except Exception as e3:
            print(f"   FAILED: {e3}")

        # Test 4: Try the raw search_points method
        print("\n4. Testing search_points method...")
        try:
            result = qdrant.search_points(
                collection_name="humanoid_ai_book_new",
                vector=query_vector,
                limit=2,
                with_payload=True
            )
            print(f"   SUCCESS: Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
        except Exception as e4:
            print(f"   FAILED: {e4}")

        # Test 5: Try scroll method if available
        print("\n5. Testing scroll method...")
        try:
            result = qdrant.scroll(
                collection_name="humanoid_ai_book_new",
                limit=2,
                with_payload=True
            )
            print(f"   SUCCESS: Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
        except Exception as e5:
            print(f"   FAILED: {e5}")

        # Test 6: Check for other potential methods
        print("\n6. Checking for other available methods...")
        methods_to_check = [
            'query_batch', 'search_batch', 'recommend',
            'discover', 'context', 'recommend_batch'
        ]

        for method_name in methods_to_check:
            if hasattr(qdrant, method_name):
                print(f"   Found method: {method_name}")
                method = getattr(qdrant, method_name)
                import inspect
                try:
                    sig = inspect.signature(method)
                    print(f"     Signature: {sig}")
                except:
                    print(f"     Could not get signature")
            else:
                print(f"   Method {method_name} not available")

        return True

    except Exception as e:
        print(f"Error in test_query_method_api: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_query_method_api()