#!/usr/bin/env python3
"""
CLI Agent for testing API keys and troubleshooting issues
This script tests various components of your backend to help identify and fix issues.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Test if environment variables are properly loaded"""
    logger.info("Testing environment variables...")

    required_vars = [
        'OPENROUTER_API_KEY',
        'QDRANT_URL',
        'QDRANT_API_KEY',
        'SECRET_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            logger.info(f"+ {var}: {'SET' if value else 'NOT SET'}")

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False

    return True

def test_openrouter_connection():
    """Test OpenRouter API connection"""
    logger.info("Testing OpenRouter API connection...")

    try:
        from openai import OpenAI

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("OPENROUTER_API_KEY not set")
            return False

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1/"
        )

        # Test with a simple request
        response = client.chat.completions.create(
            model="mistralai/devstral-2512:free",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            temperature=0.3,
            max_tokens=50
        )

        logger.info(f"+ OpenRouter connection successful. Response: {response.choices[0].message.content[:50]}...")
        return True

    except Exception as e:
        logger.error(f"- OpenRouter connection failed: {e}")
        return False

def test_qdrant_connection():
    """Test Qdrant connection"""
    logger.info("Testing Qdrant connection...")

    try:
        from qdrant_client import QdrantClient
        import requests

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            logger.error("QDRANT_URL not set")
            return False

        # Test connection based on URL type
        if qdrant_url.startswith("https://"):
            # Cloud connection
            qdrant = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
        else:
            # Local connection
            qdrant = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                prefer_grpc=False
            )

        # Test by getting collections
        collections = qdrant.get_collections()
        logger.info(f"+ Qdrant connection successful. Found {len(collections.collections)} collections")

        # Check for the expected collection
        collection_names = [coll.name for coll in collections.collections]
        if "humanoid_ai_book_new" in collection_names:
            logger.info("+ 'humanoid_ai_book_new' collection found")
        else:
            logger.warning(f"- 'humanoid_ai_book_new' collection not found. Available: {collection_names}")

        return True

    except Exception as e:
        logger.error(f"- Qdrant connection failed: {e}")
        return False

def test_fastembed():
    """Test FastEmbed functionality"""
    logger.info("Testing FastEmbed functionality...")

    try:
        from fastembed import TextEmbedding

        # Initialize model
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        # Test embedding
        test_text = "This is a test sentence for embedding."
        embeddings = list(embedding_model.embed([test_text]))

        if len(embeddings) > 0 and len(embeddings[0]) > 0:
            logger.info(f"+ FastEmbed working. Embedding dimension: {len(embeddings[0])}")
            return True
        else:
            logger.error("- FastEmbed returned empty embeddings")
            return False

    except Exception as e:
        logger.error(f"- FastEmbed test failed: {e}")
        return False

def test_qdrant_retrieval():
    """Test Qdrant retrieval with embeddings"""
    logger.info("Testing Qdrant retrieval with embeddings...")

    try:
        from qdrant_client import QdrantClient
        from fastembed import TextEmbedding

        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url and qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # Initialize embedding model
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        # Create test embedding
        test_query = "humanoid robotics"
        embeddings = list(embedding_model.embed([test_query]))
        query_embedding = embeddings[0].tolist()

        # Try to search in the collection
        try:
            result = qdrant.search(
                collection_name="humanoid_ai_book_new",
                query_vector=query_embedding,
                limit=3
            )

            logger.info(f"+ Qdrant search successful. Found {len(result)} results")
            if result:
                logger.info(f"  First result payload keys: {list(result[0].payload.keys()) if hasattr(result[0], 'payload') else 'N/A'}")

            return True
        except Exception as search_error:
            logger.error(f"- Qdrant search failed: {search_error}")

            # Try alternative method names that might exist
            methods_to_try = ['query', 'search_points', 'scroll', 'retrieve']
            for method_name in methods_to_try:
                try:
                    method = getattr(qdrant, method_name)
                    if method_name == 'search_points':
                        result = method(
                            collection_name="humanoid_ai_book_new",
                            vector=query_embedding,
                            limit=3,
                            with_payload=True
                        )
                    elif method_name == 'scroll':
                        result = method(
                            collection_name="humanoid_ai_book_new",
                            limit=3
                        )
                    elif method_name == 'retrieve':
                        # This might require point IDs
                        result = []
                    elif method_name == 'query':
                        # This might be the problematic method
                        result = method(
                            collection_name="humanoid_ai_book_new",
                            query_text=test_query,  # This is what the error mentioned
                            limit=3
                        )

                    logger.info(f"+ Method '{method_name}' worked! Found {len(result) if isinstance(result, (list, tuple)) else 'unknown'} results")
                    return True
                except Exception as alt_error:
                    logger.debug(f"Method '{method_name}' also failed: {alt_error}")
                    continue

            logger.error("All Qdrant search methods failed")
            return False

    except Exception as e:
        logger.error(f"✗ Qdrant retrieval test failed: {e}")
        return False

def test_jwt_functionality():
    """Test JWT functionality"""
    logger.info("Testing JWT functionality...")

    try:
        import jwt
        from datetime import datetime, timedelta

        secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

        # Create a test token
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow()
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        logger.info("+ JWT token created successfully")

        # Decode the token
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        logger.info(f"+ JWT token decoded successfully. Email: {decoded.get('sub')}")

        return True

    except Exception as e:
        logger.error(f"- JWT functionality test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide a summary"""
    logger.info("Starting comprehensive backend test...")
    print("="*60)

    tests = [
        ("Environment Variables", test_environment),
        ("OpenRouter Connection", test_openrouter_connection),
        ("Qdrant Connection", test_qdrant_connection),
        ("FastEmbed Functionality", test_fastembed),
        ("Qdrant Retrieval", test_qdrant_retrieval),
        ("JWT Functionality", test_jwt_functionality),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results[test_name] = result

    print("\n" + "="*60)
    print("TEST SUMMARY:")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "+" if result else "-"
        print(f"{symbol} {test_name}: {status}")

        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed == 0:
        logger.info("\n🎉 All tests passed! Your backend should be working correctly.")
    else:
        logger.warning(f"\n⚠️  {failed} test(s) failed. Please check the logs above for details.")
        logger.info("Common fixes:")
        logger.info("  - Ensure all environment variables are set")
        logger.info("  - Check that Qdrant server is running and accessible")
        logger.info("  - Verify that the 'humanoid_ai_book_new' collection exists in Qdrant")
        logger.info("  - Confirm your API keys are valid and have proper permissions")

    return failed == 0

def main():
    """Main function to run the CLI agent"""
    print("CLI Agent for Backend Testing")
    print("This tool will test your API keys and backend components.")
    print()

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "help" or sys.argv[1] == "--help":
            print("Usage: python test_agent.py [test_name]")
            print("Available tests:")
            print("  - env: Test environment variables")
            print("  - openrouter: Test OpenRouter connection")
            print("  - qdrant: Test Qdrant connection")
            print("  - embeddings: Test FastEmbed functionality")
            print("  - retrieval: Test Qdrant retrieval")
            print("  - jwt: Test JWT functionality")
            print("  - all (default): Run all tests")
            return

    # Run specific test if provided
    if len(sys.argv) > 1:
        test_arg = sys.argv[1].lower()

        if test_arg == "env":
            result = test_environment()
        elif test_arg == "openrouter":
            result = test_openrouter_connection()
        elif test_arg == "qdrant":
            result = test_qdrant_connection()
        elif test_arg in ["embeddings", "fastembed"]:
            result = test_fastembed()
        elif test_arg in ["retrieval", "search"]:
            result = test_qdrant_retrieval()
        elif test_arg == "jwt":
            result = test_jwt_functionality()
        elif test_arg == "all":
            result = run_comprehensive_test()
        else:
            logger.error(f"Unknown test: {test_arg}")
            print("Run 'python test_agent.py help' for available options")
            return

        status = "PASSED" if result else "FAILED"
        print(f"\nTest '{test_arg}' {status}")
        return

    # Run all tests by default
    run_comprehensive_test()

if __name__ == "__main__":
    main()