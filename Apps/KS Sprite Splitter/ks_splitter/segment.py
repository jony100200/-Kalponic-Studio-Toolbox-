"""
Core protocols and contracts for KS Sprite Splitter.

Defines the interfaces that all segmentation, matting, and part splitting
backends must implement for pluggable architecture.
"""

from typing import Protocol, List, Dict, Any, Optional
import numpy as np


class Segmenter(Protocol):
    """
    Protocol for object/instance segmentation backends.

    Responsible for detecting and masking individual objects/instances
    in sprite images.
    """

    def infer(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Perform instance segmentation on the input image.

        Args:
            image: Input image as numpy array (H, W, 3) in RGB format

        Returns:
            List of instance dictionaries, each containing:
            - 'id': Unique instance identifier
            - 'class': Class name/label (optional)
            - 'mask': Boolean mask array (H, W)
            - 'bbox': Bounding box [x1, y1, x2, y2]
            - 'score': Confidence score (optional)
        """
        ...


class Matter(Protocol):
    """
    Protocol for alpha matting/refinement backends.

    Responsible for converting hard masks to soft alpha mattes.
    """

    def refine(self, image: np.ndarray, mask: np.ndarray, band_px: int = 5) -> np.ndarray:
        """
        Refine a hard mask into a soft alpha matte.

        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            mask: Hard mask as boolean array (H, W)
            band_px: Width of the unknown band around mask edges in pixels

        Returns:
            Soft alpha matte as float32 array (H, W) with values in [0, 1]
        """
        ...


class PartSplitter(Protocol):
    """
    Protocol for semantic part splitting backends.

    Responsible for dividing detected objects into semantic parts
    based on category-specific heuristics and templates.
    """

    def split(self, image: np.ndarray, instance: Dict[str, Any], template: Dict) -> Dict[str, np.ndarray]:
        """
        Split an object instance into semantic parts.

        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            instance: Instance dictionary from Segmenter.infer()
            template: Template configuration dictionary

        Returns:
            Dictionary mapping part names to boolean mask arrays:
            {'Leaves': mask_array, 'Trunk': mask_array, ...}
        """
        ...