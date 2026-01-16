#!/usr/bin/env python3
"""
Quick check script to test your specific issues
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Quick check of environment variables"""
    print("Checking environment variables...")

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")

    print(f"OPENROUTER_API_KEY set: {'YES' if openrouter_key else 'NO'}")
    print(f"QDRANT_URL set: {'YES' if qdrant_url else 'NO'}")
    print(f"QDRANT_API_KEY set: {'YES' if qdrant_key else 'NO'}")

    return bool(openrouter_key and qdrant_url)

def check_imports():
    """Quick check of imports"""
    print("\nChecking imports...")

    try:
        import qdrant_client
        print("+ qdrant_client imported successfully")
        # Some versions of qdrant_client don't have __version__
        try:
            version = qdrant_client.__version__
            print(f"  Version: {version}")
        except AttributeError:
            print("  Version: unknown (attribute not available)")
    except ImportError as e:
        print(f"- qdrant_client import failed: {e}")
        return False

    try:
        import fastembed
        print("+ fastembed imported successfully")
        # Handle version attribute
        try:
            version = fastembed.__version__
            print(f"  Version: {version}")
        except AttributeError:
            print("  Version: unknown (attribute not available)")
    except ImportError as e:
        print(f"- fastembed import failed: {e}")
        return False

    try:
        import jwt
        print("+ jwt imported successfully")
    except ImportError as e:
        print(f"- jwt import failed: {e}")
        return False

    try:
        from openai import OpenAI
        print("+ openai imported successfully")
    except ImportError as e:
        print(f"- openai import failed: {e}")
        return False

    return True

def test_qdrant_client():
    """Test Qdrant client and its methods"""
    print("\nTesting Qdrant client...")

    try:
        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            print("- QDRANT_URL not set")
            return False

        # Initialize client
        if qdrant_url.startswith("https://"):
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)

        # Check for the problematic methods
        methods = ['search', 'query', 'search_points']
        for method in methods:
            has_method = hasattr(qdrant, method)
            status = '+' if has_method else '-'
            print(f"  {status} qdrant.{method} method: {has_method}")

        # Try to connect and get collections
        try:
            collections = qdrant.get_collections()
            print(f"  + Connected to Qdrant. Found {len(collections.collections)} collections")
            collection_names = [coll.name for coll in collections.collections]
            print(f"    Collections: {collection_names}")

            if "humanoid_ai_book_new" in collection_names:
                print("  + 'humanoid_ai_book_new' collection exists")
            else:
                print("  ! 'humanoid_ai_book_new' collection does NOT exist")

        except Exception as conn_error:
            print(f"  - Connection test failed: {conn_error}")

        return True

    except Exception as e:
        print(f"- Qdrant client test failed: {e}")
        import traceback
        print(f"  Full error: {traceback.format_exc()}")
        return False

def test_retrieval_issue():
    """Test the specific retrieval issue"""
    print("\nTesting retrieval function (the main issue)...")

    try:
        from src.services.retrieving import retrieve

        # Test the function that's causing the error
        print("  Attempting to call retrieve function...")
        result = retrieve("test query", collection_name="humanoid_ai_book_new", limit=1)
        print(f"  + Retrieve function worked! Got {len(result)} results")
        return True

    except Exception as e:
        print(f"  - Retrieve function failed: {e}")
        print(f"  Error type: {type(e).__name__}")

        # Check if it's the specific error you mentioned
        error_str = str(e)
        if "QdrantFastembedMixin.query() missing 1 required positional argument" in error_str:
            print("  !! This is the exact error you reported!")
        elif "search" in error_str and "attribute" in error_str:
            print("  !! This is related to the search method issue!")

        import traceback
        print(f"  Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Main function"""
    print("Quick Check for Your Backend Issues")
    print("="*50)

    # Run checks
    env_ok = check_environment()
    imports_ok = check_imports()
    qdrant_ok = test_qdrant_client()
    retrieval_ok = test_retrieval_issue()

    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Environment: {'PASS' if env_ok else 'FAIL'}")
    print(f"Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"Qdrant: {'PASS' if qdrant_ok else 'FAIL'}")
    print(f"Retrieval: {'PASS' if retrieval_ok else 'FAIL'}")

    print("\nNext Steps:")
    if not env_ok:
        print("  1. Set your environment variables (OPENROUTER_API_KEY, QDRANT_URL, QDRANT_API_KEY)")
    if not retrieval_ok:
        print("  1. Run 'python qdrant_troubleshoot.py' for detailed Qdrant debugging")
        print("  2. Check that your 'humanoid_ai_book_new' collection exists in Qdrant")
        print("  3. Verify the correct method is being called in retrieving.py")

    if env_ok and imports_ok and qdrant_ok and retrieval_ok:
        print("  All checks passed! Your system should be working.")
    else:
        print("  Some issues found. See above for details.")

if __name__ == "__main__":
    main()