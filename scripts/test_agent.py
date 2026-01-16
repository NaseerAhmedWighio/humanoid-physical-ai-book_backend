#!/usr/bin/env python3
"""
Terminal script to test the AI agent directly.
This script allows you to interact with the LLM service directly from the command line.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_agent():
    """Test the agent with direct terminal input."""
    try:
        from services.llm_service import llm_service

        print("🤖 AI Agent Terminal Test")
        print("Type your questions below (type 'quit' or 'exit' to stop):")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n>You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q', '']:
                    print("Goodbye! 👋")
                    break

                print("\n🤖 Agent: ", end="", flush=True)

                # Prepare messages for the LLM
                messages = [
                    {"role": "system", "content": "You are an AI assistant for the Physical AI & Humanoid Robotics Textbook. Provide helpful, accurate responses."},
                    {"role": "user", "content": user_input}
                ]

                # Get response from the LLM
                response = llm_service.chat_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )

                print(response)

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please check your environment variables and API keys.")
                break

    except ImportError as e:
        print(f"❌ Error importing LLM service: {e}")
        print("Make sure you're in the correct directory and dependencies are installed.")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print("Check your .env file for proper configuration.")

def test_with_context():
    """Test the agent with RAG context."""
    try:
        from services.llm_service import llm_service
        from services.retrieving import retrieve

        print("🤖 AI Agent Terminal Test (with RAG context)")
        print("Type your questions below (type 'quit' or 'exit' to stop):")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n>You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q', '']:
                    print("Goodbye! 👋")
                    break

                print("\n🔍 Retrieving context...")

                # Retrieve relevant context
                retrieved_texts = retrieve(user_input, limit=3)
                context_text = "\n\n".join(retrieved_texts) if retrieved_texts else "No relevant context found."

                print("\n🤖 Agent: ", end="", flush=True)

                # Prepare messages with context
                system_message = f"""You are an AI assistant for the Physical AI & Humanoid Robotics Textbook.
                Use the following context to answer the user's question.
                If the context doesn't contain relevant information, say so.
                Be accurate, concise, and cite sources when possible.

                Context: {context_text}"""

                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_input}
                ]

                # Get response from the LLM
                response = llm_service.chat_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )

                print(response)

                if retrieved_texts:
                    print(f"\n📋 Sources used: {len(retrieved_texts)} context chunks")

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please check your environment variables, API keys, and vector database connection.")
                break

    except ImportError as e:
        print(f"❌ Error importing services: {e}")
        print("Make sure you're in the correct directory and dependencies are installed.")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print("Check your .env file for proper configuration.")

def main():
    """Main function to run the agent test."""
    print("Choose test mode:")
    print("1. Direct agent test (no context)")
    print("2. RAG-enabled test (with context)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "2":
        test_with_context()
    else:
        test_agent()

if __name__ == "__main__":
    main()