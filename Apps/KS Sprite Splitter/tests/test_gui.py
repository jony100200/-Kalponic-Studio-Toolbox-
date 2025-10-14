"""
Tests for the KS Sprite Splitter GUI application.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Skip GUI tests if PySide6 is not available
pyside6_available = True
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
except ImportError:
    pyside6_available = False

if pyside6_available:
    from app.main_gui import SpriteSplitterGUI


@pytest.mark.skipif(not pyside6_available, reason="PySide6 not available")
class TestSpriteSplitterGUI:
    """Test the GUI application."""

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication instance for tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    def test_gui_initialization(self, qapp):
        """Test that the GUI can be initialized without errors."""
        with patch('app.main_gui.SpriteSplitterGUI.load_config'), \
             patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()
            assert gui.windowTitle() == "KS Sprite Splitter v1.0"
            assert gui.minimumSize().width() == 1000
            assert gui.minimumSize().height() == 700

    def test_config_loading(self, qapp):
        """Test configuration loading."""
        with patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()
            # Should load default config if file doesn't exist
            config = gui.config
            assert isinstance(config, dict)
            # Check for individual backend keys
            assert 'objects_backend' in config
            assert 'matte_backend' in config
            assert 'parts_backend' in config

    def test_template_selection(self, qapp):
        """Test template selection functionality."""
        with patch('app.main_gui.SpriteSplitterGUI.load_config'), \
             patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()
            # Check that template combo box has expected items
            templates = [gui.template_combo.itemText(i) for i in range(gui.template_combo.count())]
            expected_templates = ['tree', 'flag', 'char', 'arch', 'vfx']
            assert templates == expected_templates

    @patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
    def test_input_file_selection(self, mock_dialog, qapp):
        """Test input file selection dialog."""
        with patch('app.main_gui.SpriteSplitterGUI.load_config'), \
             patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()
            mock_dialog.return_value = ('/path/to/test.png', 'PNG Files (*.png)')

            gui.select_input_file()

            assert gui.input_path_label.text() == 'test.png'  # Shows just filename
            assert gui.input_path == '/path/to/test.png'  # Stores full path

    @patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory')
    def test_output_directory_selection(self, mock_dialog, qapp):
        """Test output directory selection dialog."""
        with patch('app.main_gui.SpriteSplitterGUI.load_config'), \
             patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()
            mock_dialog.return_value = '/path/to/output'

            gui.select_output_directory()

            assert gui.output_dir_label.text() == 'output'  # Shows just directory name
            assert gui.output_dir == '/path/to/output'  # Stores full path

    def test_template_info_update(self, qapp):
        """Test template information display update."""
        with patch('app.main_gui.SpriteSplitterGUI.load_config'), \
             patch('app.main_gui.SpriteSplitterGUI.load_stylesheet'):
            gui = SpriteSplitterGUI()

            # Test tree template
            gui.on_template_changed('tree')
            info_text = gui.template_info.toPlainText()
            assert 'tree' in info_text.lower()

            # Test character template
            gui.on_template_changed('char')
            info_text = gui.template_info.toPlainText()
            assert 'character' in info_text.lower() or 'char' in info_text.lower()


if __name__ == "__main__":
    pytest.main([__file__])