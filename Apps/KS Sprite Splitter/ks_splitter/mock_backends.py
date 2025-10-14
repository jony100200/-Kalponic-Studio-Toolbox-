"""
Mock backends for testing and demonstration.

Provides simple implementations of the core protocols for development
and testing without requiring full ML models.
"""

import numpy as np
import cv2
from typing import List, Dict, Any
from ks_splitter.segment import Segmenter
from ks_splitter.matte import Matter
from ks_splitter.parts import PartSplitter


class MockSegmenter(Segmenter):
    """
    Mock segmenter using simple color thresholding.

    Creates mock instances based on color clusters in the image.
    """

    def infer(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Create mock instances using color-based segmentation."""
        # Convert to HSV for better color segmentation
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Simple color-based instance detection
        # This is a placeholder - real implementation would use SAM2/YOLO/etc
        height, width = image.shape[:2]

        # Create a few mock instances
        instances = []

        # Mock instance 1: "main object" covering most of the image
        mask1 = np.ones((height, width), dtype=bool)
        # Add some variation to make it more realistic
        mask1[height//4:3*height//4, width//4:3*width//4] = True

        instances.append({
            'id': 1,
            'class': 'object',
            'mask': mask1,
            'bbox': [width//4, height//4, 3*width//4, 3*height//4],
            'score': 0.95
        })

        return instances


class MockMatter(Matter):
    """
    Mock matting using Gaussian blur for soft edges.

    Creates soft alpha mattes by blurring the hard mask edges.
    """

    def refine(self, image: np.ndarray, mask: np.ndarray, band_px: int = 5) -> np.ndarray:
        """Create soft alpha using Gaussian blur."""
        # Convert mask to float
        alpha = mask.astype(np.float32)

        # Apply Gaussian blur to create soft edges
        kernel_size = max(3, band_px * 2 + 1)  # Ensure odd kernel size
        alpha = cv2.GaussianBlur(alpha, (kernel_size, kernel_size), band_px/2)

        return alpha


class MockPartSplitter(PartSplitter):
    """
    Mock part splitter using simple heuristics.

    Creates basic parts based on image regions and template.
    """

    def split(self, image: np.ndarray, instance: Dict[str, Any], template: Dict) -> Dict[str, np.ndarray]:
        """Split instance into parts using simple region-based approach."""
        mask = instance['mask']
        height, width = mask.shape

        parts = {}
        part_names = template.get('parts', ['Part1', 'Part2', 'Part3'])

        # Simple region-based splitting
        regions = len(part_names)

        for i, part_name in enumerate(part_names):
            # Create a simple mask for this part
            part_mask = np.zeros_like(mask, dtype=bool)

            if regions == 1:
                part_mask = mask.copy()
            elif regions == 2:
                # Split vertically
                split_point = width // 2
                if i == 0:
                    part_mask[:, :split_point] = mask[:, :split_point]
                else:
                    part_mask[:, split_point:] = mask[:, split_point:]
            elif regions == 3:
                # Split into thirds
                third = width // 3
                if i == 0:
                    part_mask[:, :third] = mask[:, :third]
                elif i == 1:
                    part_mask[:, third:2*third] = mask[:, third:2*third]
                else:
                    part_mask[:, 2*third:] = mask[:, 2*third:]

            parts[part_name] = part_mask

        return parts


# Register mock backends
from ks_splitter.segment import register_segmenter_backend
from ks_splitter.matte import register_matte_backend
from ks_splitter.parts import register_part_backend

register_segmenter_backend('mock', MockSegmenter)
register_matte_backend('mock', MockMatter)
register_part_backend('mock', MockPartSplitter)