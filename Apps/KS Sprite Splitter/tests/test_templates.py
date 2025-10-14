"""
Tests for template loading and validation.
"""

import pytest
import yaml
from pathlib import Path
from ks_splitter.parts import load_template


class TestTemplateLoading:
    """Test template loading functionality."""

    def test_load_tree_template(self):
        """Test loading the tree template."""
        template = load_template('tree')

        assert template['name'] == 'tree'
        assert 'parts' in template
        assert 'Leaves' in template['parts']
        assert 'Trunk' in template['parts']
        assert 'heuristics' in template
        assert 'matting' in template

    def test_load_flag_template(self):
        """Test loading the flag template."""
        template = load_template('flag')

        assert template['name'] == 'flag'
        assert 'Pole' in template['parts']
        assert 'Flag' in template['parts']

    def test_load_char_template(self):
        """Test loading the character template."""
        template = load_template('char')

        assert template['name'] == 'char'
        assert 'Body' in template['parts']
        assert 'Head' in template['parts']
        assert 'Arms' in template['parts']
        assert 'Legs' in template['parts']

    def test_load_arch_template(self):
        """Test loading the architecture template."""
        template = load_template('arch')

        assert template['name'] == 'arch'
        assert 'Walls' in template['parts']
        assert 'Doors' in template['parts']

    def test_load_vfx_template(self):
        """Test loading the VFX template."""
        template = load_template('vfx')

        assert template['name'] == 'vfx'
        assert 'Core' in template['parts']
        assert 'Glow' in template['parts']

    def test_template_structure(self):
        """Test that all templates have required structure."""
        categories = ['tree', 'flag', 'char', 'arch', 'vfx']

        for category in categories:
            template = load_template(category)

            # Check required keys
            required_keys = ['name', 'parts', 'heuristics', 'matting']
            for key in required_keys:
                assert key in template, f"Template {category} missing {key}"

            # Check parts is a list
            assert isinstance(template['parts'], list)
            assert len(template['parts']) > 0

            # Check heuristics has expected structure
            assert 'kmeans_k' in template['heuristics']
            assert 'freq_window' in template['heuristics']

            # Check matting has band_px
            assert 'band_px' in template['matting']

    def test_invalid_template_error(self):
        """Test that invalid template raises error."""
        with pytest.raises(FileNotFoundError):
            load_template('nonexistent_template')