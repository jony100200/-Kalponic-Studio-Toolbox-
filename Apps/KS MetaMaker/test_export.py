#!/usr/bin/env python3
"""
Test script for KS MetaMaker export functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ks_metamaker.utils.config import Config
from ks_metamaker.export import DatasetExporter

def test_export():
    """Test the export functionality"""
    config = Config()
    exporter = DatasetExporter(config)

    # Create a dummy image path
    test_image = Path("test_image.jpg")

    # Test tags
    tags = ["kalponic studio background", "cinematic lighting", "4k render", "texture", "stone"]

    print(f"Testing export with tags: {tags}")

    # Test export
    try:
        exporter.export(test_image, tags)
        print("Export completed successfully")

        # Check if txt file was created
        txt_file = test_image.with_suffix('.txt')
        if txt_file.exists():
            with open(txt_file, 'r') as f:
                content = f.read()
            print(f"Created txt file: {txt_file}")
            print(f"Content: {content}")
        else:
            print(f"No txt file created at: {txt_file}")

    except Exception as e:
        print(f"Export failed: {e}")

if __name__ == "__main__":
    test_export()