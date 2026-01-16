#!/usr/bin/env python3
"""
Test script to check if the LLM service is working properly
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

def test_llm_service():
    print("Testing LLM Service...")
    print("="*50)

    try:
        # Try to import the LLM service
        from src.services.llm_service import llm_service
        print("✓ LLM Service imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import LLM Service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing LLM Service: {e}")
        return False

    # Test with a simple message
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, test message!"}
    ]

    try:
        print("Testing chat completion...")
        response = llm_service.chat_completion(
            messages=test_messages,
            temperature=0.3,
            max_tokens=100
        )
        print("✓ Chat completion successful")
        print(f"Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Error in chat completion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_service()
    if success:
        print("\n🎉 LLM Service is working correctly!")
    else:
        print("\n❌ LLM Service has issues that need to be fixed.")