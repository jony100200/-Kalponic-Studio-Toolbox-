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

        # Convert to uint8 if needed (OpenCV GrabCut requires uint8)
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                # Assume normalized float image
                image_uint8 = (image * 255).astype(np.uint8)
            else:
                # Assume already in 0-255 range
                image_uint8 = image.astype(np.uint8)
        else:
            image_uint8 = image

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
        cv2.grabCut(image_uint8, mask, rect, bgd_model, fgd_model, self.iterations, cv2.GC_INIT_WITH_RECT)

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


class SimpleMatter(Matter):
    """
    Simple matting using morphological operations and Gaussian blur.

    Creates soft edges around hard masks using basic image processing.
    """

    def __init__(self):
        self.blur_kernel = 5
        self.morph_kernel = 3

    def refine(self, image: np.ndarray, mask: np.ndarray, band_px: int = 5) -> np.ndarray:
        """
        Refine hard mask using morphological operations and blurring.

        Args:
            image: RGB image (H, W, 3)
            mask: Hard mask (H, W) boolean
            band_px: Transition band width in pixels

        Returns:
            Soft alpha matte (H, W) float32 [0, 1]
        """
        # Convert mask to uint8
        mask_uint8 = mask.astype(np.uint8) * 255

        # Apply morphological operations to create transition band
        kernel = np.ones((self.morph_kernel, self.morph_kernel), np.uint8)

        # Erode to create inner mask
        eroded = cv2.erode(mask_uint8, kernel, iterations=band_px//2)

        # Dilate to create outer mask
        dilated = cv2.dilate(mask_uint8, kernel, iterations=band_px//2)

        # Create transition band
        transition = dilated - eroded

        # Apply Gaussian blur to transition band
        blurred = cv2.GaussianBlur(transition.astype(np.float32), (self.blur_kernel, self.blur_kernel), 0)

        # Normalize to [0, 1]
        matte = blurred / 255.0

        # Combine with original mask
        final_matte = np.where(mask, 1.0, matte)

        return np.clip(final_matte, 0.0, 1.0)


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
register_matte_backend('guided', SimpleMatter)
register_part_backend('heuristic', HeuristicPartSplitter)