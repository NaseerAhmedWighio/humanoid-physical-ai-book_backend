#!/usr/bin/env python
"""
Test script to verify the chat endpoint is working correctly
"""
import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint to make sure it's accessible"""
    print("Testing Chat Endpoint...")

    base_url = "http://localhost:8000"

    # Test health endpoint first
    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            print("+ Health endpoint is accessible")
        else:
            print(f"- Health endpoint returned status: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"- Health endpoint not accessible: {e}")
        return False

    # Test the chat endpoint
    session_id = "session_test_12345"
    test_url = f"{base_url}/v1/chat/sessions/{session_id}/messages"

    payload = {
        "content": "Hello, this is a test message",
        "context_window": 5
    }

    print(f"Testing POST request to: {test_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            test_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("+ Chat endpoint is working correctly")
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"Response text: {response.text[:200]}...")
        elif response.status_code == 422:  # Validation error
            print("- Chat endpoint is accessible but validation failed (expected for test data)")
            try:
                result = response.json()
                print(f"Validation error: {result}")
            except:
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"- Chat endpoint returned status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")

        return True

    except requests.exceptions.ConnectionError:
        print(f"- Cannot connect to chat endpoint at {test_url}")
        print("   Make sure the backend server is running on port 8000")
        return False
    except Exception as e:
        print(f"- Error testing chat endpoint: {e}")
        return False

def test_ask_from_selection_endpoint():
    """Test the ask-from-selection endpoint"""
    print("\nTesting Ask from Selection Endpoint...")

    base_url = "http://localhost:8000"
    test_url = f"{base_url}/v1/chat/ask-from-selection"

    payload = {
        "content": "What is ROS 2?",
        "context_window": 5
    }

    print(f"Testing POST request to: {test_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            test_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("+ Ask-from-selection endpoint is working correctly")
            try:
                result = response.json()
                print(f"Response preview: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"Response text: {response.text[:200]}...")
        elif response.status_code == 422:  # Validation error
            print("- Ask-from-selection endpoint is accessible but validation failed (expected for test data)")
            try:
                result = response.json()
                print(f"Validation error: {result}")
            except:
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"- Ask-from-selection endpoint returned status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")

        return True

    except requests.exceptions.ConnectionError:
        print(f"- Cannot connect to ask-from-selection endpoint at {test_url}")
        print("   Make sure the backend server is running on port 8000")
        return False
    except Exception as e:
        print(f"- Error testing ask-from-selection endpoint: {e}")
        return False

def main():
    print("Testing Backend Chat Endpoints")
    print("=" * 50)

    print("This script tests whether the backend chat endpoints are accessible.")
    print("Make sure your backend server is running on http://localhost:8000")
    print()

    test1 = test_chat_endpoint()
    test2 = test_ask_from_selection_endpoint()

    print(f"\nTest Results:")
    print(f"  - Chat endpoint: {'PASS' if test1 else 'FAIL'}")
    print(f"  - Ask-from-selection endpoint: {'PASS' if test2 else 'FAIL'}")

    if test1 and test2:
        print(f"\nBoth endpoints are accessible!")
        print(f"   The frontend should now be able to communicate with the backend.")
        return True
    else:
        print(f"\nSome endpoints are not accessible.")
        print(f"   Please make sure the backend server is running and accessible.")
        return False

if __name__ == "__main__":
    main()