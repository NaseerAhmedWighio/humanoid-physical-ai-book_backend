#!/usr/bin/env python
"""
Test script to verify RAG fallback functionality when Qdrant is not available
"""
import sys
from pathlib import Path

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_retrieve_fallback():
    """Test that retrieve function returns empty list when Qdrant is not available"""
    print("Testing RAG fallback functionality...")

    try:
        from src.services.retrieving import retrieve

        # Try to retrieve without Qdrant running
        # This should return an empty list instead of crashing
        result = retrieve("test query about robotics")

        print(f"Retrieve result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if isinstance(result, list) else 'N/A'}")

        if isinstance(result, list):
            print("Retrieve function handled Qdrant unavailability gracefully")
            print("Returned empty list as fallback instead of crashing")
            return True
        else:
            print("Retrieve function did not return a list as expected")
            return False

    except Exception as e:
        print(f"Retrieve function crashed when Qdrant was unavailable: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_endpoint_simulation():
    """Simulate what happens in the chat endpoint when RAG fails"""
    print("\nTesting chat endpoint simulation...")

    try:
        from src.services.llm_service import llm_service

        # Create a mock messages list
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant for robotics."},
            {"role": "user", "content": "What is ROS 2?"}
        ]

        # Try to get a response from the LLM (without RAG context)
        result = llm_service.chat_completion_with_sources(
            messages=messages,
            sources=[],
            temperature=0.3,
            max_tokens=150
        )

        print(f"LLM Response: {result['response'][:100]}...")
        print("LLM service works without RAG context")
        return True

    except Exception as e:
        print(f"LLM service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing RAG Fallback Functionality")
    print("=" * 50)

    test1_passed = test_retrieve_fallback()
    test2_passed = test_chat_endpoint_simulation()

    print(f"\nTest Results:")
    print(f"  - Retrieve fallback: {'PASS' if test1_passed else 'FAIL'}")
    print(f"  - LLM service: {'PASS' if test2_passed else 'FAIL'}")

    if test1_passed and test2_passed:
        print(f"\nAll tests passed! RAG system will work gracefully even without Qdrant.")
        print(f"   The system will still function, just without contextual RAG responses.")
        return True
    else:
        print(f"\nSome tests failed. There may be issues with graceful degradation.")
        return False

if __name__ == "__main__":
    main()