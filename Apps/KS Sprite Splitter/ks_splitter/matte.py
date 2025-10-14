"""
Alpha matting and refinement backends.

Provides protocols and implementations for converting hard masks
to soft alpha mattes using various techniques.
"""

from typing import Protocol
import numpy as np


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


# Registry for available matting backends
MATTE_BACKENDS = {}


def register_matte_backend(name: str, backend_class):
    """Register a matting backend implementation."""
    MATTE_BACKENDS[name] = backend_class


def get_matte_backend(name: str) -> Matter:
    """Get a matting backend instance by name."""
    if name not in MATTE_BACKENDS:
        raise ValueError(f"Unknown matte backend: {name}")
    return MATTE_BACKENDS[name]()