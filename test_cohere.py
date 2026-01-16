#!/usr/bin/env python3
"""
Test script to verify Cohere integration is working properly
"""
import os
from dotenv import load_dotenv
load_dotenv()

from src.services.llm_service import llm_service
from src.services.retrieving import get_embedding

def test_cohere_llm():
    print("Testing Cohere LLM integration...")
    print("="*50)

    try:
        # Test the Cohere chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant for the Physical AI & Humanoid Robotics Textbook."},
            {"role": "user", "content": "Hello, can you help me understand humanoid robotics?"}
        ]

        response = llm_service.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=200
        )

        print(f"SUCCESS: Cohere response received!")
        print(f"Response: {response[:200]}...")
        print()

    except Exception as e:
        print(f"ERROR in Cohere LLM: {e}")
        import traceback
        traceback.print_exc()

def test_cohere_embeddings():
    print("Testing Cohere embeddings integration...")
    print("="*50)

    try:
        # Test embedding generation
        text = "humanoid robotics artificial intelligence"
        embedding = get_embedding(text)

        print(f"SUCCESS: Cohere embedding generated!")
        print(f"Embedding length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")
        print()

    except Exception as e:
        print(f"ERROR in Cohere embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Cohere Integration")
    print("="*60)
    test_cohere_llm()
    test_cohere_embeddings()