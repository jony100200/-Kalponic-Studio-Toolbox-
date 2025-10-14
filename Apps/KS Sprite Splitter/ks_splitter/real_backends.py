"""
Real ML backends for production use.

Implements actual computer vision models for segmentation, matting, and part splitting.
"""

import numpy as np
import cv2
from typing import List, Dict, Any
from ks_splitter.segment import Segmenter, register_segmenter_backend
from ks_splitter.matte import Matter, register_matte_backend
from ks_splitter.parts import PartSplitter, register_part_backend


class OpenCVSegmenter(Segmenter):
    """
    Real segmenter using OpenCV's GrabCut algorithm.

    Provides basic foreground/background segmentation using interactive segmentation.
    """

    def __init__(self):
        # Initialize GrabCut parameters
        self.iterations = 5

    def infer(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Perform segmentation using GrabCut algorithm.

        Uses a simple rectangular initialization around the center of the image.
        """
        height, width = image.shape[:2]

        # Create initial rectangle (center 60% of image)
        margin_h = int(height * 0.2)
        margin_w = int(width * 0.2)
        rect = (margin_w, margin_h, width - 2*margin_w, height - 2*margin_h)

        # Initialize mask
        mask = np.zeros((height, width), dtype=np.uint8)

        # Create models
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Apply GrabCut
        cv2.grabCut(image, mask, rect, bgd_model, fgd_model, self.iterations, cv2.GC_INIT_WITH_RECT)

        # Convert mask to binary (foreground = 1, background = 0)
        binary_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)

        # Find contours to get bounding box
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Use the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            bbox = [x, y, x + w, y + h]
        else:
            # Fallback to full image
            bbox = [0, 0, width, height]

        return [{
            'id': 1,
            'class': 'foreground',
            'mask': binary_mask.astype(bool),
            'bbox': bbox,
            'score': 0.8  # Confidence score
        }]


class GuidedFilterMatter(Matter):
    """
    Real matting using Guided Filter refinement.

    Refines hard masks into soft alpha mattes using guided filtering.
    """

    def __init__(self):
        self.radius = 8
        self.eps = 0.01

    def refine(self, image: np.ndarray, mask: np.ndarray, band_px: int = 5) -> np.ndarray:
        """
        Refine hard mask using guided filtering.

        Args:
            image: RGB image (H, W, 3)
            mask: Hard mask (H, W) boolean
            band_px: Transition band width (unused in this implementation)

        Returns:
            Soft alpha matte (H, W) float32 [0, 1]
        """
        # Convert mask to float
        mask_float = mask.astype(np.float32)

        # Use grayscale version of image as guidance
        guidance = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0

        # Apply guided filter
        refined = cv2.ximgproc.guidedFilter(
            guide=guidance,
            src=mask_float,
            radius=self.radius,
            eps=self.eps
        )

        # Ensure values are in [0, 1]
        return np.clip(refined, 0.0, 1.0)


class HeuristicPartSplitter(PartSplitter):
    """
    Real part splitter using image analysis heuristics.

    Splits objects into semantic parts based on color clustering and spatial analysis.
    """

    def __init__(self):
        self.k_clusters = 5

    def split(self, image: np.ndarray, instance: Dict[str, Any], template: Dict) -> Dict[str, np.ndarray]:
        """
        Split object into semantic parts using k-means clustering.

        Args:
            image: RGB image
            instance: Detection instance with mask
            template: Template configuration

        Returns:
            Dictionary mapping part names to boolean masks
        """
        mask = instance['mask']
        parts = {}

        if not np.any(mask):
            # Empty mask, return empty parts
            for part_name in template['parts']:
                parts[part_name] = np.zeros_like(mask)
            return parts

        # Apply mask to image
        masked_image = image * mask[:, :, np.newaxis]

        # Reshape for k-means
        pixels = masked_image[mask].reshape(-1, 3).astype(np.float32)

        if len(pixels) < self.k_clusters:
            # Not enough pixels, assign all to first part
            for i, part_name in enumerate(template['parts']):
                if i == 0:
                    parts[part_name] = mask.copy()
                else:
                    parts[part_name] = np.zeros_like(mask)
            return parts

        # Perform k-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, self.k_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        # Create part masks
        for i, part_name in enumerate(template['parts']):
            if i < self.k_clusters:
                # Create mask for this cluster
                part_mask = np.zeros_like(mask, dtype=bool)
                cluster_pixels = labels.flatten() == i
                part_mask[mask] = cluster_pixels
                parts[part_name] = part_mask
            else:
                # No more clusters, create empty mask
                parts[part_name] = np.zeros_like(mask, dtype=bool)

        return parts


# Register real backends
register_segmenter_backend('opencv', OpenCVSegmenter)
register_matte_backend('guided', GuidedFilterMatter)
register_part_backend('heuristic', HeuristicPartSplitter)