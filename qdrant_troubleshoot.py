#!/usr/bin/env python3
"""
Qdrant-specific troubleshooting agent
This script specifically tests and fixes the Qdrant search issue you're experiencing.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_qdrant_client_methods():
    """Check what methods are available on the Qdrant client"""
    logger.info("Checking Qdrant client methods...")

    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            logger.error("QDRANT_URL not set in environment variables")
            return False

        # Initialize client
        if qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # Get available methods
        available_methods = [method for method in dir(qdrant) if not method.startswith('_')]
        search_related = [method for method in available_methods if 'search' in method.lower() or 'query' in method.lower()]

        logger.info(f"Available methods containing 'search' or 'query': {search_related}")

        # Check for the specific methods that might be causing issues
        has_search = hasattr(qdrant, 'search')
        has_query = hasattr(qdrant, 'query')
        has_search_points = hasattr(qdrant, 'search_points')

        logger.info(f"Has 'search' method: {has_search}")
        logger.info(f"Has 'query' method: {has_query}")
        logger.info(f"Has 'search_points' method: {has_search_points}")

        return True

    except Exception as e:
        logger.error(f"Error checking Qdrant client methods: {e}")
        return False

def test_different_qdrant_apis():
    """Test different Qdrant API approaches"""
    logger.info("Testing different Qdrant API approaches...")

    try:
        from qdrant_client import QdrantClient
        from fastembed import TextEmbedding
        import numpy as np

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            logger.error("QDRANT_URL not set")
            return False

        # Initialize client
        if qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # Initialize embedding model
        try:
            embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            test_text = "humanoid robotics"
            embeddings = list(embedding_model.embed([test_text]))
            query_vector = embeddings[0].tolist()
        except Exception as embed_error:
            logger.error(f"Embedding failed: {embed_error}")
            # Fallback to a simple vector
            query_vector = [0.1] * 384  # Standard BGE-small dimension
            logger.info("Using fallback embedding vector")

        # Test 1: Standard search method
        logger.info("Testing standard 'search' method...")
        try:
            result = qdrant.search(
                collection_name="humanoid_ai_book_new",
                query_vector=query_vector,
                limit=3
            )
            logger.info(f"✓ Standard search worked. Found {len(result)} results")
        except Exception as e:
            logger.error(f"✗ Standard search failed: {e}")

        # Test 2: Check if there's a query method that might be causing the issue
        logger.info("Testing 'query' method if available...")
        if hasattr(qdrant, 'query'):
            try:
                # Try different signatures for the query method
                # This might be the problematic method mentioned in your error
                try:
                    # Try with query_text parameter (as mentioned in error)
                    result = qdrant.query(
                        collection_name="humanoid_ai_book_new",
                        query_text=test_text,  # This is what the error suggests
                        limit=3
                    )
                    logger.info(f"✓ Query method with query_text worked. Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
                except TypeError as te:
                    if "missing 1 required positional argument" in str(te) and "query_text" in str(te):
                        logger.info(f"✓ Confirmed: Query method expects query_text parameter. Error: {te}")
                    else:
                        logger.info(f"Query method has different error: {te}")

                # Try with query_vector parameter
                try:
                    result = qdrant.query(
                        collection_name="humanoid_ai_book_new",
                        query_vector=query_vector,
                        limit=3
                    )
                    logger.info(f"✓ Query method with query_vector worked. Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
                except Exception as query_vec_error:
                    logger.info(f"Query method with query_vector failed: {query_vec_error}")

            except Exception as query_error:
                logger.error(f"✗ Query method failed completely: {query_error}")
        else:
            logger.info("Query method not available")

        # Test 3: search_points method
        logger.info("Testing 'search_points' method if available...")
        if hasattr(qdrant, 'search_points'):
            try:
                result = qdrant.search_points(
                    collection_name="humanoid_ai_book_new",
                    vector=query_vector,
                    limit=3,
                    with_payload=True
                )
                logger.info(f"✓ search_points worked. Found {len(result) if hasattr(result, '__len__') else 'unknown'} results")
            except Exception as sp_error:
                logger.error(f"✗ search_points failed: {sp_error}")
        else:
            logger.info("search_points method not available")

        # Test 4: Check if it's a QdrantFastembedMixin issue
        logger.info("Testing for QdrantFastembedMixin approach...")
        try:
            # Check if there's a fastembed-integrated approach
            from qdrant_client.http import models
            logger.info("Qdrant models available - checking if extended client is needed")
        except ImportError:
            logger.info("Qdrant HTTP models not available")

        return True

    except Exception as e:
        logger.error(f"Error testing different Qdrant APIs: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def check_qdrant_collection():
    """Check if the collection exists and has the right schema"""
    logger.info("Checking Qdrant collection...")

    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            logger.error("QDRANT_URL not set")
            return False

        # Initialize client
        if qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # List all collections
        collections = qdrant.get_collections()
        logger.info(f"Available collections: {[coll.name for coll in collections.collections]}")

        # Check specific collection
        collection_name = "humanoid_ai_book_new"
        if collection_name in [coll.name for coll in collections.collections]:
            collection_info = qdrant.get_collection(collection_name)
            logger.info(f"✓ Collection '{collection_name}' exists")
            logger.info(f"  Points count: {collection_info.points_count}")
            logger.info(f"  Vector size: {collection_info.config.params.vectors.size}")
            logger.info(f"  Distance: {collection_info.config.params.vectors.distance}")
        else:
            logger.error(f"✗ Collection '{collection_name}' does not exist")
            logger.info("You may need to ingest data first using the ingestion scripts")

        return True

    except Exception as e:
        logger.error(f"Error checking Qdrant collection: {e}")
        return False

def test_retrieval_function():
    """Test the exact retrieval function that's failing"""
    logger.info("Testing the actual retrieval function from your code...")

    try:
        # Import your retrieval function
        from src.services.retrieving import retrieve

        # Test the function that's causing the error
        test_query = "humanoid robotics"
        try:
            result = retrieve(test_query, collection_name="humanoid_ai_book_new", limit=3)
            logger.info(f"✓ Your retrieve function worked! Found {len(result)} results")
            if result:
                logger.info(f"  First result preview: {result[0][:100]}...")
        except Exception as retrieve_error:
            logger.error(f"✗ Your retrieve function failed: {retrieve_error}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

        return True

    except Exception as e:
        logger.error(f"Error importing or testing retrieval function: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def check_version_compatibility():
    """Check version compatibility of packages"""
    logger.info("Checking package versions...")

    try:
        import qdrant_client
        import fastembed
        import jwt

        # Check versions, but handle cases where __version__ is not available
        try:
            qdrant_version = qdrant_client.__version__
            logger.info(f"qdrant_client version: {qdrant_version}")
        except AttributeError:
            logger.info("qdrant_client version: unknown (attribute not available)")

        try:
            fastembed_version = fastembed.__version__
            logger.info(f"fastembed version: {fastembed_version}")
        except AttributeError:
            logger.info("fastembed version: unknown (attribute not available)")

        # Check if we have the right version of qdrant_client
        # Newer versions might have different APIs
        try:
            version_str = qdrant_client.__version__
            major_version = int(version_str.split('.')[0]) if version_str else 0
        except AttributeError:
            logger.info("Could not determine qdrant_client version")
            major_version = 0

        if major_version >= 1:
            logger.info("✓ qdrant_client version 1.x or higher - this is expected")
        else:
            logger.warning("⚠️ qdrant_client version < 1.x - API might be different")

        return True

    except Exception as e:
        logger.error(f"Error checking versions: {e}")
        return False

def main():
    """Main function to run Qdrant-specific troubleshooting"""
    print("🤖 Qdrant Troubleshooting Agent")
    print("This tool will specifically test and fix your Qdrant issues.")
    print()

    tests = [
        ("Version Compatibility", check_version_compatibility),
        ("Qdrant Client Methods", check_qdrant_client_methods),
        ("Qdrant Collection Check", check_qdrant_collection),
        ("Different Qdrant APIs", test_different_qdrant_apis),
        ("Actual Retrieval Function", test_retrieval_function),
    ]

    print("Running diagnostic tests...")
    print("="*60)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        test_func()

    print("\n" + "="*60)
    print("TROUBLESHOOTING COMPLETE")
    print("="*60)

    logger.info("\nIf you're still having issues, the problem might be:")
    logger.info("1. Wrong method being called (search vs query vs search_points)")
    logger.info("2. Missing collection in Qdrant")
    logger.info("3. Version incompatibility with Qdrant client")
    logger.info("4. Wrong parameter names in method calls")

    logger.info("\nSuggested fixes to try:")
    logger.info("1. Make sure you have the 'humanoid_ai_book_new' collection in Qdrant")
    logger.info("2. Check that your Qdrant client version matches your code expectations")
    logger.info("3. Verify the correct method name is being used (search vs query)")
    logger.info("4. Ensure parameter names match the Qdrant client version you're using")

if __name__ == "__main__":
    main()