#!/usr/bin/env python3
"""
Terminal script to test the backend API endpoints directly.
This script allows you to test the API without going through the frontend.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test basic API connection."""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    try:
        response = requests.get(f"{api_base_url}/health")
        if response.status_code == 200:
            print("✅ API Connection: SUCCESS")
            print(f"   Health check response: {response.json()}")
            return True
        else:
            print(f"❌ API Connection: FAILED - Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ API Connection: FAILED - Cannot connect to {api_base_url}")
        print("   Make sure the backend server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ API Connection: FAILED - {e}")
        return False

def test_chat_functionality():
    """Test the chat functionality directly."""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    print("\n📝 Testing chat functionality...")

    # Create a session
    try:
        session_response = requests.post(
            f"{api_base_url}/v1/chat/sessions",
            json={"title": "Terminal Test Session"},
            headers={"Content-Type": "application/json"}
        )

        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.status_code}")
            print(f"   Response: {session_response.text}")
            return False

        session_data = session_response.json()
        session_id = session_data.get("session_id")
        print(f"✅ Session created: {session_id}")

        # Test sending a message
        test_message = "Hello, this is a test from the terminal. Can you respond?"
        message_response = requests.post(
            f"{api_base_url}/v1/chat/sessions/{session_id}/messages",
            json={"content": test_message},
            headers={"Content-Type": "application/json"}
        )

        if message_response.status_code != 200:
            print(f"❌ Failed to send message: {message_response.status_code}")
            print(f"   Response: {message_response.text}")
            return False

        message_data = message_response.json()
        print(f"✅ Message sent successfully")
        print(f"   Response: {message_data.get('response', 'No response text')[:100]}...")

        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {api_base_url}")
        return False
    except Exception as e:
        print(f"❌ Error testing chat functionality: {e}")
        return False

def interactive_chat():
    """Interactive chat through terminal."""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    print("\n💬 Interactive Chat via API")
    print("Type your messages below (type 'quit' or 'exit' to stop):")
    print("-" * 50)

    # Create a session
    try:
        session_response = requests.post(
            f"{api_base_url}/v1/chat/sessions",
            json={"title": "Interactive Terminal Session"},
            headers={"Content-Type": "application/json"}
        )

        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.status_code}")
            return

        session_data = session_response.json()
        session_id = session_data.get("session_id")
        print(f"✅ Session created: {session_id}")

        while True:
            user_input = input("\n>You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q', '']:
                print("Goodbye! 👋")
                break

            try:
                response = requests.post(
                    f"{api_base_url}/v1/chat/sessions/{session_id}/messages",
                    json={"content": user_input},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    continue

                data = response.json()
                agent_response = data.get('response', 'No response')
                print(f"\n🤖 Agent: {agent_response}")

                # Show sources if available
                sources = data.get('sources', [])
                if sources:
                    print(f"   📚 Sources: {len(sources)} context chunks used")

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error initializing chat: {e}")

def main():
    """Main function to run API tests."""
    print("🚀 AI Textbook Backend API Test Suite")
    print("=" * 50)

    # Test basic connection
    if not test_api_connection():
        print("\n❌ Cannot proceed - API is not accessible")
        return

    # Test chat functionality
    test_chat_functionality()

    # Ask if user wants to try interactive chat
    print("\n" + "=" * 50)
    choice = input("Would you like to try interactive chat? (y/n): ").strip().lower()

    if choice in ['y', 'yes']:
        interactive_chat()

if __name__ == "__main__":
    main()