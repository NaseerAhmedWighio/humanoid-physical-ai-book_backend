#!/usr/bin/env python3
"""
Test script to verify that the RAG system is working properly
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.retrieving import retrieve

def test_retrieval():
    print("Testing RAG retrieval system...")
    print("="*50)

    # Test with a sample query
    test_query = "what is humanoid robotics"

    try:
        results = retrieve(test_query, collection_name="humanoid_ai_book_new", limit=3)
        print(f"Query: '{test_query}'")
        print(f"Number of results retrieved: {len(results)}")
        print()

        if results:
            print("Retrieved content samples:")
            print("-" * 30)
            for i, content in enumerate(results, 1):
                print(f"Result {i}:")
                # Show first 200 characters of each result
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  {preview}")
                print()
        else:
            print("No results found. This could mean:")
            print("1. The collection 'humanoid_ai_book_new' is empty")
            print("2. The content hasn't been ingested yet")
            print("3. There's an issue with the Qdrant connection")

    except Exception as e:
        print(f"Error during retrieval: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()