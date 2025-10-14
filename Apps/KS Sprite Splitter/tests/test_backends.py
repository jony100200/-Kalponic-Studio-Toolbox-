"""
Tests for backend registry functionality.
"""

import pytest
import numpy as np
from ks_splitter import segment, matte, parts, mock_backends, real_backends


class TestBackendRegistry:
    """Test backend registration and retrieval."""

    def test_segmenter_registry(self):
        """Test segmenter backend registration and retrieval."""
        # Mock backends should be registered
        backend = segment.get_segmenter_backend('mock')
        assert backend is not None
        assert hasattr(backend, 'infer')

        # Test inference
        test_image = np.random.rand(64, 64, 3).astype(np.float32)
        instances = backend.infer(test_image)
        assert isinstance(instances, list)
        assert len(instances) > 0

        # Check instance structure
        instance = instances[0]
        required_keys = ['id', 'mask', 'bbox', 'score']
        for key in required_keys:
            assert key in instance

    def test_matte_registry(self):
        """Test matte backend registration and retrieval."""
        backend = matte.get_matte_backend('mock')
        assert backend is not None
        assert hasattr(backend, 'refine')

        # Test refinement
        test_image = np.random.rand(32, 32, 3).astype(np.float32)
        test_mask = np.random.rand(32, 32).astype(bool)
        matte_result = backend.refine(test_image, test_mask)
        assert matte_result.shape == (32, 32)
        assert matte_result.dtype == np.float32
        assert np.all((matte_result >= 0) & (matte_result <= 1))

    def test_part_splitter_registry(self):
        """Test part splitter backend registration and retrieval."""
        backend = parts.get_part_backend('mock')
        assert backend is not None
        assert hasattr(backend, 'split')

        # Test splitting
        test_image = np.random.rand(32, 32, 3).astype(np.float32)
        test_instance = {
            'id': 1,
            'mask': np.ones((32, 32), dtype=bool),
            'bbox': [0, 0, 32, 32],
            'score': 0.9
        }
        test_template = {'parts': ['Part1', 'Part2']}

        parts_result = backend.split(test_image, test_instance, test_template)
        assert isinstance(parts_result, dict)
        assert len(parts_result) > 0

        # Check that parts are boolean masks
        for part_name, part_mask in parts_result.items():
            assert isinstance(part_mask, np.ndarray)
            assert part_mask.dtype == bool
            assert part_mask.shape == (32, 32)

    def test_real_segmenter_backend(self):
        """Test OpenCV segmenter backend."""
        backend = segment.get_segmenter_backend('opencv')
        assert backend is not None
        assert hasattr(backend, 'infer')

        # Test inference
        test_image = np.random.rand(64, 64, 3).astype(np.float32)
        instances = backend.infer(test_image)
        assert isinstance(instances, list)
        assert len(instances) > 0

        # Check instance structure
        instance = instances[0]
        required_keys = ['id', 'mask', 'bbox', 'score']
        for key in required_keys:
            assert key in instance

    def test_real_matte_backend(self):
        """Test simple matte backend."""
        backend = matte.get_matte_backend('guided')
        assert backend is not None
        assert hasattr(backend, 'refine')

        # Test refinement
        test_image = np.random.rand(32, 32, 3).astype(np.float32)
        test_mask = np.random.rand(32, 32) > 0.5  # Random boolean mask
        matte_result = backend.refine(test_image, test_mask)
        assert matte_result.shape == (32, 32)
        assert matte_result.dtype == np.float32
        assert np.all((matte_result >= 0) & (matte_result <= 1))

    def test_real_part_splitter_backend(self):
        """Test heuristic part splitter backend."""
        backend = parts.get_part_backend('heuristic')
        assert backend is not None
        assert hasattr(backend, 'split')

        # Test splitting
        test_image = np.random.rand(32, 32, 3).astype(np.float32)
        test_instance = {
            'id': 1,
            'mask': np.ones((32, 32), dtype=bool),
            'bbox': [0, 0, 32, 32],
            'score': 0.9
        }
        test_template = {'parts': ['Part1', 'Part2', 'Part3']}

        parts_result = backend.split(test_image, test_instance, test_template)
        assert isinstance(parts_result, dict)
        assert len(parts_result) == 3  # Should have all parts from template

        # Check that parts are boolean masks
        for part_name, part_mask in parts_result.items():
            assert isinstance(part_mask, np.ndarray)
            assert part_mask.dtype == bool
            assert part_mask.shape == (32, 32)