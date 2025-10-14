"""
Semantic part splitting backends and template system.

Provides protocols and implementations for dividing detected objects
into semantic parts based on category-specific heuristics.
"""

from typing import Protocol, Dict, Any
import numpy as np


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


# Registry for available part splitting backends
PART_BACKENDS = {}


def register_part_backend(name: str, backend_class):
    """Register a part splitting backend implementation."""
    PART_BACKENDS[name] = backend_class()


def get_part_backend(name: str) -> PartSplitter:
    """Get a part splitting backend instance by name."""
    if name not in PART_BACKENDS:
        raise ValueError(f"Unknown part backend: {name}")
    return PART_BACKENDS[name]


def load_template(category: str, templates_dir: str = "templates") -> Dict:
    """
    Load a template configuration for a given category.

    Args:
        category: Template category name (e.g., 'tree', 'flag')
        templates_dir: Directory containing template YAML files

    Returns:
        Template configuration dictionary
    """
    import os
    import yaml

    template_path = os.path.join(templates_dir, f"{category}.yml")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r') as f:
        return yaml.safe_load(f)