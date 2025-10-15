"""
Circle detection and masking functionality for KS SnapStudio.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CircleMask:
    """Handles circle detection, masking, and composition."""

    def __init__(self):
        self._hough_params = {
            'dp': 1.2,
            'minDist': 100,
            'param1': 50,
            'param2': 30,
            'minRadius': 50,
            'maxRadius': 500
        }

    def detect_circle(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Detect the most prominent circle in the image using Hough transform.

        Returns:
            Dict with 'center', 'radius', 'confidence' or None if no circle found
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)

            # Detect circles using Hough transform
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=self._hough_params['dp'],
                minDist=self._hough_params['minDist'],
                param1=self._hough_params['param1'],
                param2=self._hough_params['param2'],
                minRadius=self._hough_params['minRadius'],
                maxRadius=self._hough_params['maxRadius']
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype(int)

                # Return the largest circle found
                largest_circle = max(circles, key=lambda c: c[2])
                center = (largest_circle[0], largest_circle[1])
                radius = largest_circle[2]

                # Calculate confidence based on circle properties
                confidence = self._calculate_circle_confidence(gray, center, radius)

                return {
                    'center': center,
                    'radius': radius,
                    'confidence': confidence
                }

            return None

        except Exception as e:
            logger.error(f"Circle detection failed: {e}")
            return None

    def _calculate_circle_confidence(self, gray_image: np.ndarray,
                                   center: Tuple[int, int],
                                   radius: int) -> float:
        """Calculate confidence score for detected circle."""
        try:
            # Create circle mask
            mask = np.zeros_like(gray_image)
            cv2.circle(mask, center, radius, 255, -1)

            # Calculate mean intensity inside and outside circle
            inside_mask = mask > 0
            outside_mask = mask == 0

            if np.sum(inside_mask) == 0 or np.sum(outside_mask) == 0:
                return 0.0

            inside_mean = np.mean(gray_image[inside_mask])
            outside_mean = np.mean(gray_image[outside_mask])

            # Higher confidence if there's good contrast between inside and outside
            contrast = abs(inside_mean - outside_mean) / 255.0

            # Penalize if circle is too close to image edges
            height, width = gray_image.shape
            cx, cy = center
            edge_distance = min(cx, width - cx, cy, height - cy)
            edge_penalty = min(1.0, edge_distance / radius)

            confidence = contrast * edge_penalty

            return min(1.0, confidence)

        except Exception:
            return 0.0

    def create_circular_mask(self, image: np.ndarray,
                           center: Tuple[int, int],
                           radius: int,
                           feather: int = 10) -> np.ndarray:
        """
        Create a circular mask with soft feathering.

        Args:
            image: Input image
            center: (x, y) center coordinates
            radius: Circle radius
            feather: Feather amount in pixels

        Returns:
            Alpha mask (0-255)
        """
        height, width = image.shape[:2]

        # Create base mask
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)

        if feather > 0:
            # Create feather mask
            feather_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.circle(feather_mask, center, radius + feather, 255, -1)
            cv2.circle(feather_mask, center, max(0, radius - feather), 0, -1)

            # Apply Gaussian blur to feather mask
            feather_mask = cv2.GaussianBlur(feather_mask, (feather*2+1, feather*2+1), 0)

            # Combine masks
            mask = cv2.bitwise_or(mask, feather_mask)

        return mask

    def apply_mask(self, image: np.ndarray, mask: np.ndarray,
                  background_color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
        """
        Apply circular mask to image with specified background.

        Args:
            image: Input image (RGB)
            mask: Alpha mask (0-255)
            background_color: RGB background color

        Returns:
            Masked image with alpha channel
        """
        # Ensure image is RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = image[:, :, :3]

        # Create background
        background = np.full_like(image, background_color)

        # Normalize mask to 0-1
        mask_norm = mask.astype(np.float32) / 255.0

        # Blend image and background
        result = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)

        for c in range(3):  # RGB channels
            result[:, :, c] = (image[:, :, c] * mask_norm + background[:, :, c] * (1 - mask_norm))

        result[:, :, 3] = mask  # Alpha channel

        return result

    def auto_crop_circle(self, image: np.ndarray,
                        circle_info: Optional[Dict[str, Any]] = None,
                        padding: int = 20) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Automatically detect and crop to circle with padding.

        Returns:
            Tuple of (cropped_image, circle_info)
        """
        if circle_info is None:
            circle_info = self.detect_circle(image)

        if circle_info is None:
            # Fallback: crop to square in center
            height, width = image.shape[:2]
            size = min(width, height)
            x = (width - size) // 2
            y = (height - size) // 2

            cropped = image[y:y+size, x:x+size]
            return cropped, {'center': (size//2, size//2), 'radius': size//2, 'confidence': 0.0}

        center = circle_info['center']
        radius = circle_info['radius']

        # Calculate crop bounds with padding
        x1 = max(0, center[0] - radius - padding)
        y1 = max(0, center[1] - radius - padding)
        x2 = min(image.shape[1], center[0] + radius + padding)
        y2 = min(image.shape[0], center[1] + radius + padding)

        cropped = image[y1:y2, x1:x2]

        # Adjust circle coordinates for cropped image
        adjusted_circle = {
            'center': (center[0] - x1, center[1] - y1),
            'radius': radius,
            'confidence': circle_info.get('confidence', 0.0)
        }

        return cropped, adjusted_circle

    def update_hough_params(self, **params):
        """Update Hough circle detection parameters."""
        self._hough_params.update(params)
        logger.info(f"Updated Hough parameters: {self._hough_params}")</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\core\mask.py