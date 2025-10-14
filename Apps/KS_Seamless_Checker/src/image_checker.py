import cv2
import numpy as np
from PIL import Image

class ImageChecker:
    def __init__(self, threshold=10):
        self.threshold = threshold

    def is_seamless(self, img):
        """Check if image is seamless by comparing edge pixels."""
        h, w = img.shape[:2]
        # Vertical seam
        diff_v = np.mean((img[:, -1] - img[:, 0]) ** 2)
        # Horizontal seam
        diff_h = np.mean((img[-1, :] - img[0, :]) ** 2)
        return diff_v < self.threshold and diff_h < self.threshold

    def create_tiled_preview(self, img):
        """Create a 2x2 tiled preview."""
        h, w = img.shape[:2]
        tiled = np.zeros((2 * h, 2 * w, 3), dtype=np.uint8)
        tiled[0:h, 0:w] = img
        tiled[0:h, w:2*w] = img
        tiled[h:2*h, 0:w] = img
        tiled[h:2*h, w:2*w] = img
        return Image.fromarray(cv2.cvtColor(tiled, cv2.COLOR_BGR2RGB))