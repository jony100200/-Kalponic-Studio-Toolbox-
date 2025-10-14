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
    checker = ImageChecker(threshold=0.3)

    # Test with a simple pattern (should be seamless)
    img = cv2.imread('test_seamless.png')  # You'll need to create this
    if img is not None:
        result = checker.is_seamless(img)
        print(f"Seamless image result: {result}")
    else:
        print("No test image found")

    # Test with a non-seamless image
    img2 = cv2.imread('test_non_seamless.png')  # You'll need to create this
    if img2 is not None:
        result2 = checker.is_seamless(img2)
        print(f"Non-seamless image result: {result2}")
    else:
        print("No non-seamless test image found")

if __name__ == '__main__':
    test_detection()