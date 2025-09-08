#!/usr/bin/env python3
"""
Quick test script to verify the Batch Image Cleanup Tool components.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import customtkinter as ctk
        print("✓ CustomTkinter imported successfully")
    except ImportError as e:
        print(f"✗ CustomTkinter import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✓ OpenCV imported successfully (version: {cv2.__version__})")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy imported successfully (version: {np.__version__})")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print(f"✓ Pillow imported successfully (version: {Image.__version__})")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    return True

def test_components():
    """Test that all application components can be imported."""
    print("\nTesting application components...")
    
    try:
        from src.config import ProcessingConfig
        print("✓ ProcessingConfig imported")
    except ImportError as e:
        print(f"✗ ProcessingConfig import failed: {e}")
        return False
    
    try:
        from src.processor import ImageProcessor
        print("✓ ImageProcessor imported")
    except ImportError as e:
        print(f"✗ ImageProcessor import failed: {e}")
        return False
    
    try:
        from src.io_handler import IOHandler
        print("✓ IOHandler imported")
    except ImportError as e:
        print(f"✗ IOHandler import failed: {e}")
        return False
    
    try:
        from src.batch_runner import BatchRunner
        print("✓ BatchRunner imported")
    except ImportError as e:
        print(f"✗ BatchRunner import failed: {e}")
        return False
    
    try:
        from src.controller import Controller
        print("✓ Controller imported")
    except ImportError as e:
        print(f"✗ Controller import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration creation and defaults."""
    print("\nTesting configuration...")
    
    try:
        from src.config import ProcessingConfig, MattePreset
        config = ProcessingConfig()
        
        assert config.matte_preset == MattePreset.WHITE_MATTE
        assert config.smooth == 2
        assert config.feather == 1
        assert config.contrast == 3.0
        assert config.shift_edge == -1
        assert config.fringe_fix_enabled == True
        assert config.fringe_band == 2
        assert config.fringe_strength == 2
        
        print("✓ Configuration defaults are correct")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Batch Image Cleanup Tool - Component Test ===\n")
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_components():
        tests_passed += 1
    
    if test_config():
        tests_passed += 1
    
    print(f"\n=== Test Results: {tests_passed}/{total_tests} passed ===")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nTo run the application: python main.py")
        return True
    else:
        print("❌ Some tests failed. Please check the installation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
