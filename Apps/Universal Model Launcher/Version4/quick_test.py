#!/usr/bin/env python3
"""
Fast test for Universal Model Launcher task processing
"""

import requests
import json
import time
from pathlib import Path

# Server configuration
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test-key-12345"

def quick_test():
    """Quick test of task processing"""

    # Test files
    testing_dir = Path(__file__).parent.parent / "Testing"

    test_case = {
        "task_type": "code_analysis",
        "input_path": str(testing_dir / "PlayerMovement.cs"),
        "output_path": str(Path(__file__).parent / "output" / "quick_test.txt")
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print("⚡ Quick Task Processing Test")

    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/process_task",
            json=test_case,
            headers=headers,
            timeout=5
        )
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"✅ Success: {result['data']['result']['analysis'][:100]}...")
        else:
            print(f"❌ Failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()