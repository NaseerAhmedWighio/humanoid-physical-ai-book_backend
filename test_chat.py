import os
import requests
import json

# Set environment variables for testing
os.environ['OPENROUTER_API_KEY'] = 'test-key'
os.environ['QDRANT_URL'] = 'http://localhost:6333'  # This will cause retrieval to fail gracefully

def test_chat_api():
    try:
        # Test the root endpoint
        response = requests.get("http://127.0.0.1:8001/")
        print(f"Root endpoint: {response.status_code}")

        # Test health endpoint
        response = requests.get("http://127.0.0.1:8001/health")
        print(f"Health endpoint: {response.status_code}")

        # Try to create a chat session
        session_data = {"title": "Test Session"}
        response = requests.post("http://127.0.0.1:8001/v1/chat/sessions", json=session_data)
        print(f"Session creation: {response.status_code}")

        # If session was created, try to send a message (this will likely fail due to Qdrant not running, but shouldn't be 500)
        if response.status_code == 200:
            session_response = response.json()
            session_id = session_response.get('session_id', 'test_session')

            message_data = {"content": "Hello", "context_window": 1}
            response = requests.post(f"http://127.0.0.1:8001/v1/chat/sessions/{session_id}/messages", json=message_data)
            print(f"Message sending: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Test error (expected if server not running): {e}")

if __name__ == "__main__":
    test_chat_api()