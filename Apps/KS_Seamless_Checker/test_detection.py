#!/usr/bin/env python3
"""
Test script to check seamless detection on sample images.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from image_checker import ImageChecker
import cv2

def test_detection():
    """Test detection on some sample images."""
    checker = ImageChecker(threshold=20.0)

    test_files = [
        'test_fully_seamless.png',
        'test_horizontal_only.png',
        'test_vertical_only.png',
        'test_non_seamless.png'
    ]

    for filename in test_files:
        img = cv2.imread(filename)
        if img is not None:
            info = checker.get_detailed_seamless_info(img, filename)
            print(f'{filename}:')
            print(f'  Type: {info["seamless_type"]}')
            print(f'  Horizontal: {info["horizontal_seamless"]} (score: {info["horizontal_score"]:.2f})')
            print(f'  Vertical: {info["vertical_seamless"]} (score: {info["vertical_score"]:.2f})')
            print(f'  Overall: {info["is_seamless"]}')
            print()
        else:
            print(f"Could not load {filename}")

if __name__ == '__main__':
    test_detection()