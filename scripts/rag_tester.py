#!/usr/bin/env python
"""
CLI-based RAG Agent Tester
Allows testing the RAG agent functionality from the command line with error visibility
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_rag_agent():
    """Test the RAG agent functionality from CLI"""
    print("RAG Agent Tester")
    print("=" * 50)

    # Get base URL
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"Using API base URL: {base_url}")

    # Test the health endpoint first
    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            print("+ API is accessible")
        else:
            print(f"- API health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"- API is not accessible: {e}")
        return

    # Test the chat functionality
    print("\nTesting RAG Chat Functionality")
    print("Enter your questions below (type 'quit' to exit):")

    session_id = "test_session_" + str(hash("cli_test"))  # Simple session ID for testing

    while True:
        try:
            question = input("\n> ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not question:
                continue

            # Prepare the request to the RAG agent
            chat_url = f"{base_url}/v1/chat/sessions/{session_id}/messages"
            payload = {
                "content": question,
                "context_window": 5
            }

            print(f"Sending request to: {chat_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Make the request
            response = requests.post(
                chat_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30  # 30 second timeout
            )

            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    print("\nAI Response:")
                    print(f"   {result.get('response', 'No response found')}")

                    if 'sources' in result and result['sources']:
                        print(f"\nRetrieved {len(result['sources'])} sources:")
                        for i, source in enumerate(result['sources'][:3], 1):  # Show first 3 sources
                            content_preview = source.get('content', '')[:100] + "..." if len(source.get('content', '')) > 100 else source.get('content', '')
                            print(f"   {i}. {content_preview}")
                except json.JSONDecodeError:
                    print(f"- Response is not valid JSON: {response.text}")
            else:
                print(f"- Request failed with status {response.status_code}")
                try:
                    error_result = response.json()
                    print(f"Error details: {error_result}")
                except:
                    print(f"Error text: {response.text}")

        except requests.exceptions.Timeout:
            print("- Request timed out. The server might be busy or the model is taking too long to respond.")
        except requests.exceptions.ConnectionError:
            print(f"- Cannot connect to the API at {base_url}. Make sure the backend server is running.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"- An error occurred: {e}")
            import traceback
            print("Full error traceback:")
            traceback.print_exc()

def test_rag_with_selection():
    """Test the RAG agent with selected text functionality"""
    print("\nTesting RAG Agent with Selected Text")

    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Sample selected text to test
    sample_text = "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software."
    question = "What is ROS 2?"

    print(f"Selected text: {sample_text}")
    print(f"Question: {question}")

    try:
        # Prepare the request to the RAG agent for selected text
        chat_url = f"{base_url}/v1/chat/ask-from-selection"
        payload = {
            "content": f"{sample_text}\n\nQuestion: {question}",
            "context_window": 5
        }

        print(f"Sending request to: {chat_url}")
        response = requests.post(
            chat_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\nAI Response to selected text:")
            print(f"   {result.get('response', 'No response found')}")
        else:
            print(f"- Request failed with status {response.status_code}")
            try:
                error_result = response.json()
                print(f"Error details: {error_result}")
            except:
                print(f"Error text: {response.text}")
    except Exception as e:
        print(f"- An error occurred: {e}")

def show_help():
    """Show help information"""
    print("\nRAG Agent Tester Help")
    print("=" * 30)
    print("This tool allows you to test the RAG agent functionality from the command line.")
    print("\nFeatures:")
    print("- Test chat functionality with context retrieval")
    print("- See full error messages and response details")
    print("- Test selected text functionality")
    print("\nEnvironment Variables:")
    print("- API_BASE_URL: The base URL for the API (default: http://localhost:8000)")
    print("\nMake sure the backend server is running before using this tool.")

def main():
    """Main function for the CLI RAG tester"""
    print("CLI-based RAG Agent Tester")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. Test RAG Chat Functionality")
        print("2. Test RAG with Selected Text")
        print("3. Show Help")
        print("4. Exit")

        try:
            choice = input("\nEnter your choice (1-4): ").strip()

            if choice == '1':
                test_rag_agent()
            elif choice == '2':
                test_rag_with_selection()
            elif choice == '3':
                show_help()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()