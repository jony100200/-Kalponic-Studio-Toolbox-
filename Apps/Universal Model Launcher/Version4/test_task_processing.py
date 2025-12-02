#!/usr/bin/env python3
"""
Test script for Universal Model Launcher task processing
Tests the new /process_task endpoint with files from the Testing directory
"""

import requests
import json
import time
import os
from pathlib import Path

# Server configuration
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test-key-12345"  # Same key used in test_api.py

def test_task_processing():
    """Test the task processing functionality"""

    # Test files in Testing directory
    testing_dir = Path(__file__).parent.parent / "Testing"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    test_cases = [
        {
            "task_type": "audio_transcription",
            "input_path": str(testing_dir / "6.Local AI Model Launcher.mp3"),
            "output_path": str(output_dir / "audio_transcription.txt")
        },
        {
            "task_type": "image_analysis",
            "input_path": str(testing_dir / "image test.png"),
            "output_path": str(output_dir / "image_analysis.txt")
        },
        {
            "task_type": "code_analysis",
            "input_path": str(testing_dir / "PlayerMovement.cs"),
            "output_path": str(output_dir / "code_analysis.txt")
        }
    ]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print("🧪 Testing Task Processing System")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['task_type']}")
        print(f"Input: {test_case['input_path']}")
        print(f"Output: {test_case['output_path']}")

        # Check if input file exists
        if not Path(test_case['input_path']).exists():
            print(f"❌ Input file not found: {test_case['input_path']}")
            continue

        try:
            # Send task request
            response = requests.post(
                f"{BASE_URL}/process_task",
                json=test_case,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Task completed successfully")
                print(f"Model used: {result['data']['model_used']}")
                print(f"Result keys: {list(result['data']['result'].keys())}")

                # Check if output file was created
                if Path(test_case['output_path']).exists():
                    print("✅ Output file created")
                else:
                    print("❌ Output file not created")
            else:
                print(f"❌ Task failed with status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 50)
    print("🎯 Task Processing Tests Complete")

def test_health_and_models():
    """Test basic health and models endpoints"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print("\n🔍 Testing Basic Endpoints")

    # Test health
    try:
        response = requests.get(f"{BASE_URL}/health", headers=headers)
        if response.status_code == 200:
            health = response.json()
            print("✅ Health check passed")
            print(f"Memory usage: {health.get('details', {}).get('memory_percent', 'N/A')}%")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test models
    try:
        response = requests.get(f"{BASE_URL}/models", headers=headers)
        if response.status_code == 200:
            models = response.json()
            print("✅ Models endpoint working")
            print(f"Available models: {len(models.get('data', []))}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")

if __name__ == "__main__":
    # First test basic endpoints
    test_health_and_models()
    # Then test task processing
    test_task_processing()