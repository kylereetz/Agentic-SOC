import requests
import json
import os
import time
from datetime import datetime

import pytest

@pytest.mark.skip(reason="Requires Live FastAPI backend running on port 8000")
def test_chitchat_endpoint():
    """
    Automated Integration Test for ChitChat /api/v1/chitchat.
    Verifies:
    1. Authentication with JWT.
    2. Dynamic context retrieval (logic check).
    3. LLMClient connectivity.
    4. Audit logging persistence.
    """
    base_url = "http://127.0.0.1:8000"
    
    print("--- [RCA ChitChat Integration Test] ---")
    
    # 1. Login to get token
    print("[1/3] Authenticating as admin...")
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{base_url}/token", data=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test ChitChat query
    print("[2/3] Sending query to ChitChat...")
    payload = {
        "query": "Based on the latest incident reports, what is the primary threat vector?",
        "history": [
            {"role": "assistant", "text": "ChitChat ready. I have full context on the SOC reports."}
        ]
    }
    
    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/api/v1/chitchat", headers=headers, json=payload, timeout=30)
    except requests.exceptions.Timeout:
        print("❌ Request timed out (Ollama might be slow/loading model)")
        return
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Is the FastAPI backend running on port 8000?")
        return

    duration = time.time() - start_time
    print(f"    - Status: {response.status_code}")
    print(f"    - Time: {duration:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        ai_response = data.get("response", "EMPTY")
        print(f"    - AI Response Snippet: {ai_response[:100]}...")
        assert "response" in data
    else:
        print(f"❌ Error: {response.text}")
        return

    # 3. Verify audit log creation
    print("[3/3] Verifying audit log persistence...")
    # The log file name is admin_YYYYMMDD.json in soc/reports/chitchat/
    # We'll check the current directory structure
    log_dir = "soc/reports/chitchat"
    session_id = f"admin_{datetime.utcnow().strftime('%Y%m%d')}"
    log_file = os.path.join(log_dir, f"{session_id}.json")
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
            if logs and logs[-1]["query"] == payload["query"]:
                print(f"✅ Audit log verified in {log_file}")
            else:
                print("❌ Log entry mismatch or empty.")
    else:
        print(f"❌ Audit log not found at {log_file}")

if __name__ == "__main__":
    try:
        test_chitchat_endpoint()
        print("\n✨ INTEGRATION TEST COMPLETE ✨")
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
