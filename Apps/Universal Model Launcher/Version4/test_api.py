import requests
import json
import time
import subprocess
import sys
import os

def start_server():
    """Start the server in a separate process"""
    script_dir = r'E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\Universal Model Launcher\Version4'
    cmd = [sys.executable, os.path.join(script_dir, 'api', 'unified_server.py')]
    
    print("Starting server...")
    process = subprocess.Popen(cmd, cwd=script_dir)
    time.sleep(5)  # Wait for server to start
    return process

def test_api():
    print("Testing Universal Model Launcher API...")

    # Start server
    server_process = start_server()

    try:
        # Test health endpoint
        try:
            response = requests.get('http://127.0.0.1:8000/health', timeout=5)
            print(f"✅ Health endpoint: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}")
            return

        # Test models endpoint
        try:
            response = requests.get('http://127.0.0.1:8000/models', timeout=5)
            print(f"✅ Models endpoint: {response.status_code}")
            models_data = response.json()
            print(f"   Available models: {len(models_data.get('data', []))}")
            for model in models_data.get('data', [])[:3]:  # Show first 3
                print(f"     - {model.get('id', 'unknown')}")
        except Exception as e:
            print(f"❌ Models endpoint failed: {e}")

        # Test model loading with a simple test
        print("\n🧪 Testing model loading...")
        
        # First, let's check if we can access the Testing directory models
        testing_dir = r'E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\Universal Model Launcher\Testing'
        print(f"Testing directory: {testing_dir}")
        
        if os.path.exists(testing_dir):
            files = os.listdir(testing_dir)
            print(f"Files in Testing directory: {files}")
            
            # Try to load a simple file as a "model" for testing
            if files:
                test_file = os.path.join(testing_dir, files[0])
                print(f"Attempting to 'load' test file: {test_file}")
                
                load_request = {
                    'model_name': 'test_model',
                    'model_path': test_file,
                    'backend': 'llama.cpp',
                    'context_length': 1024,
                    'gpu_layers': 0,
                    'quantization': 'auto'
                }

                try:
                    headers = {'Authorization': 'Bearer test_key_1234567890abcdef'}
                    response = requests.post('http://127.0.0.1:8000/load_model', json=load_request, headers=headers, timeout=30)
                    print(f"✅ Load response: {response.status_code}")
                    result = response.json()
                    print(f"   Result: {result}")
                except Exception as e:
                    print(f"❌ Model loading failed: {e}")
        else:
            print(f"❌ Testing directory not found: {testing_dir}")

    finally:
        # Stop server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_api()