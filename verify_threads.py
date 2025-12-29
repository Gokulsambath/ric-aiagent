import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_threads():
    # 1. Start a new session and thread
    print("Testing new session/thread creation...")
    payload1 = {
        "email": "test@example.com",
        "message": "Hello, I want to start a session",
        "provider": "ollama",
        "is_new_chat": True
    }
    
    headers = {"X-API-Key": "test_secret_key_123"}
    response1 = requests.post(f"{BASE_URL}/chat/", json=payload1, headers=headers, stream=True)
    print(f"Response Status: {response1.status_code}")
    session_id = None
    thread_id1 = None
    
    for line in response1.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            # print(f"DEBUG Line: {decoded_line}")
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                session_id = data.get("session_id")
                thread_id1 = data.get("thread_id")
    
    if not session_id:
        print("Detailed Session ID Failure. Response content (first 500 chars):")
        try:
             # Consume stream to print error
            print(response1.text[:500])
        except:
            print("Could not read response text")
    
    print(f"Created Session: {session_id}, Thread 1: {thread_id1}")
    
    # 2. Start another thread in the same session
    print("\nTesting multiple threads in same session...")
    payload2 = {
        "email": "test@example.com",
        "message": "This is a second thread",
        "session_id": session_id,
        "is_new_chat": True
    }
    
    response2 = requests.post(f"{BASE_URL}/chat/", json=payload2, headers=headers, stream=True)
    thread_id2 = None
    for line in response2.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                thread_id2 = data.get("thread_id")
    
    print(f"Thread 2: {thread_id2}")
    
    # 3. List threads for the session
    print("\nListing threads for session...")
    if session_id:
        response_threads = requests.get(f"{BASE_URL}/chat/sessions/{session_id}/threads", headers=headers)
        if response_threads.status_code == 200:
            threads = response_threads.json().get("threads", [])
            print(f"Found {len(threads)} threads.")
            for t in threads:
                print(f" - Thread ID: {t['id']}, Title: {t['title']}")
        else:
            print(f"Failed to list threads: {response_threads.status_code} {response_threads.text}")
    else:
        print("Skipping list threads due to missing session_id")
        
    # 4. Verify messages in Thread 1
    if thread_id1:
        print(f"\nVerifying messages in Thread 1 ({thread_id1})...")
        response_msgs = requests.get(f"{BASE_URL}/chat/threads/{thread_id1}/messages", headers=headers)
        if response_msgs.status_code == 200:
            msgs = response_msgs.json()
            print(f"Messages in Thread 1: {len(msgs)}")
        else:
             print(f"Failed to get messages: {response_msgs.status_code}")
    else:
        print("Skipping verify messages due to missing thread_id1")

if __name__ == "__main__":
    try:
        test_threads()
    except Exception as e:
        print(f"Test failed: {e}. Is the server running?")
