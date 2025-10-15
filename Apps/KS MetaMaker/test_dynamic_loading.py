#!/usr/bin/env python3
"""
Test script for dynamic model loading in KS MetaMaker
"""

import sys
from pathlib import Path

# Add the ks_metamaker module to path
sys.path.insert(0, str(Path(__file__).parent))

from ks_metamaker.tagger import ImageTagger
from ks_metamaker.utils.config import Config
from ks_metamaker.hardware_detector import HardwareDetector

def test_dynamic_loading():
    """Test dynamic model loading functionality"""
    print("Testing dynamic model loading...")

    # Initialize components
    config = Config()
    hardware_detector = HardwareDetector()

    # Create tagger with dynamic loading
    tagger = ImageTagger(config, hardware_detector=hardware_detector)

    # Check memory status
    memory_status = tagger.model_manager.get_memory_status()
    print(f"Memory profile: {memory_status['memory_profile']}")
    print(f"Max models allowed: {memory_status['max_models_allowed']}")
    print(f"Currently loaded models: {memory_status['loaded_models']}")

    # Test model loading (will load on demand)
    print("\nTesting model loading...")

    # This should trigger loading of the tagging model
    # Since we don't have actual models, it will return empty lists but test the loading logic
    test_image_path = Path("test_image.jpg")  # Doesn't need to exist for this test

    try:
        tags = tagger.tag(test_image_path)
        print(f"Tagging completed. Tags: {tags}")

        # Check memory status after potential loading
        memory_status_after = tagger.model_manager.get_memory_status()
        print(f"Models loaded after tagging: {memory_status_after['loaded_models']}")
        print(f"Memory usage: {memory_status_after['memory_usage_mb']}MB")

    except Exception as e:
        print(f"Error during tagging: {e}")

    print("Dynamic loading test completed!")

if __name__ == "__main__":
    test_dynamic_loading()