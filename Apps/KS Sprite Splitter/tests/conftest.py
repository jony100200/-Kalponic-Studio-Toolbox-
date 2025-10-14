"""
Pytest configuration and shared fixtures for KS Sprite Splitter tests.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple colored rectangle image
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    # Red rectangle in top-left
    image[:32, :32, 0] = 255
    # Green rectangle in bottom-right
    image[32:, 32:, 1] = 255
    # Blue background
    image[:, :, 2] = 128

    return image.astype(np.float32) / 255.0


@pytest.fixture
def test_config():
    """Create a test configuration dictionary."""
    return {
        'objects_backend': 'mock',
        'matte_backend': 'mock',
        'parts_backend': 'mock',
        'export': {
            'write_previews': True,
            'write_aux_maps': False,
            'preview_format': 'png'
        },
        'templates_dir': 'templates'
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_instance():
    """Create a mock instance dictionary."""
    return {
        'id': 1,
        'class': 'object',
        'mask': np.ones((32, 32), dtype=bool),
        'bbox': [0, 0, 32, 32],
        'score': 0.95
    }