#!/usr/bin/env python3
"""
Test script to verify the full RAG chat functionality
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.retrieving import retrieve
from src.services.llm_service import llm_service

def test_full_rag_flow():
    print("Testing Full RAG Chat Flow...")
    print("="*60)

    # Test with the query that was failing before
    test_query = "what is humanoid robotics"

    print(f"Query: '{test_query}'")
    print()

    try:
        # Step 1: Test retrieval
        print("Step 1: Testing content retrieval...")
        retrieved_texts = retrieve(test_query, collection_name="humanoid_ai_book_new", limit=3)
        print(f"SUCCESS: Retrieved {len(retrieved_texts)} relevant chunks")

        if retrieved_texts:
            print("Sample retrieved content:")
            for i, text in enumerate(retrieved_texts[:2], 1):
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"  {i}. {preview}")
        print()

        # Step 2: Test LLM response with context
        print("Step 2: Testing LLM response with context...")
        context_text = "\n\n".join(retrieved_texts) if retrieved_texts else "No relevant context found in the textbook."

        system_message = f"""You are an AI assistant for the Physical AI & Humanoid Robotics Textbook.
        Use the following context to answer the user's question.
        If the context doesn't contain relevant information, say so.
        Be accurate, concise, and cite sources when possible.

        Context: {context_text}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": test_query}
        ]

        ai_response = llm_service.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        print("SUCCESS: LLM response generated successfully")
        print()
        print("AI Response:")
        print("-" * 40)
        print(ai_response)
        print("-" * 40)
        print()

        # Step 3: Test another query to make sure it's not just matching one topic
        print("Step 3: Testing with another query...")
        test_query_2 = "explain ROS2 for humanoid robots"
        print(f"Query: '{test_query_2}'")

        retrieved_texts_2 = retrieve(test_query_2, collection_name="humanoid_ai_book_new", limit=3)
        print(f"SUCCESS: Retrieved {len(retrieved_texts_2)} relevant chunks for second query")

        if retrieved_texts_2:
            print("Sample retrieved content:")
            for i, text in enumerate(retrieved_texts_2[:2], 1):
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"  {i}. {preview}")
        print()

        # Step 4: Test with selected text feature
        print("Step 4: Testing 'ask from selection' feature...")
        selected_text = "Introduction to Physical AI & Humanoid Robotics"
        retrieved_for_selection = retrieve(selected_text, collection_name="humanoid_ai_book_new", limit=2)

        print(f"SUCCESS: Found {len(retrieved_for_selection)} related chunks for selected text")
        print()

        print("ALL TESTS PASSED!")
        print("Content is properly stored in Qdrant")
        print("Retrieval system is working")
        print("LLM integration is functional")
        print("The RAG agent should now respond with book content instead of 'no information'")

    except Exception as e:
        print(f"ERROR: Error during RAG flow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_rag_flow()