#!/usr/bin/env python3
"""
Simple terminal script to test the backend API endpoints directly.
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
            print("SUCCESS: API Connection")
            print(f"Health check response: {response.json()}")
            return True
        else:
            print(f"FAILED: API Connection - Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"FAILED: Cannot connect to {api_base_url}")
        print("Make sure the backend server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_chat_functionality():
    """Test the chat functionality directly."""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    print("\nTesting chat functionality...")

    # Create a session
    try:
        session_response = requests.post(
            f"{api_base_url}/v1/chat/sessions",
            json={"title": "Terminal Test Session"},
            headers={"Content-Type": "application/json"}
        )

        if session_response.status_code != 200:
            print(f"FAILED: Create session - {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return False

        session_data = session_response.json()
        session_id = session_data.get("session_id")
        print(f"SUCCESS: Session created: {session_id}")

        # Test sending a message
        test_message = "Hello, this is a test from the terminal. Can you respond?"
        message_response = requests.post(
            f"{api_base_url}/v1/chat/sessions/{session_id}/messages",
            json={"content": test_message},
            headers={"Content-Type": "application/json"}
        )

        if message_response.status_code != 200:
            print(f"FAILED: Send message - {message_response.status_code}")
            print(f"Response: {message_response.text}")
            return False

        message_data = message_response.json()
        print(f"SUCCESS: Message sent")
        print(f"Response: {message_data.get('response', 'No response text')[:100]}...")

        return True

    except requests.exceptions.ConnectionError:
        print(f"FAILED: Cannot connect to API at {api_base_url}")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    """Main function to run API tests."""
    print("AI Textbook Backend API Test")
    print("=" * 40)

    # Test basic connection
    if not test_api_connection():
        print("\nCannot proceed - API is not accessible")
        return

    # Test chat functionality
    test_chat_functionality()

if __name__ == "__main__":
    main()