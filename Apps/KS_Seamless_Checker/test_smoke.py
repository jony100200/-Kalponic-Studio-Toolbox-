#!/usr/bin/env python3
"""
Smoke Test for KS Seamless Checker
Tests that the application starts without import errors.
"""

import sys
import os
import subprocess
import json

def test_config():
    """Test that config.json is valid."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        required_keys = ['seam_threshold', 'preview_mode', 'accent_color']
        for key in required_keys:
            assert key in config, f"Missing config key: {key}"
        print("✓ Config is valid")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_app_imports():
    """Test that the app can be imported without errors."""
    try:
        # This will test if all imports work
        from src import gui, batch_processor, image_checker
        print("✓ All modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_app_starts():
    """Test that the app starts without immediate errors."""
    try:
        result = subprocess.run([sys.executable, 'main.py'],
                              cwd=os.path.dirname(__file__),
                              capture_output=True,
                              timeout=3)  # Should start within 3 seconds
        if result.returncode == 0 or 'KeyboardInterrupt' in result.stderr.decode():
            print("✓ App starts successfully")
            return True
        else:
            print(f"✗ App failed to start: {result.stderr.decode()}")
            return False
    except subprocess.TimeoutExpired:
        print("✓ App starts successfully (timed out as expected)")
        return True
    except Exception as e:
        print(f"✗ Failed to start app: {e}")
        return False

if __name__ == '__main__':
    print("Running KS Seamless Checker Smoke Test...")
    tests = [test_config, test_app_imports, test_app_starts]
    results = [test() for test in tests]
    if all(results):
        print("✓ All smoke tests passed!")
        sys.exit(0)
    else:
        print("✗ Some smoke tests failed!")
        sys.exit(1)