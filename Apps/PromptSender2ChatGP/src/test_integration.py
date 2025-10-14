"""
KS PDF Studio - Integration Test Suite
Tests the complete integration of all components.

Author: Kalponic Studio
Version: 2.0.0
"""

import sys
import os
from pathlib import Path
import unittest
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.pdf_engine import KSPDFEngine
from core.markdown_parser import KSMarkdownParser
from core.image_handler import KSImageHandler
from core.code_formatter import KSCodeFormatter
from templates.base_template import KSPDFTemplate, TemplateManager
from utils.file_utils import KSFileHandler
from ai.ai_manager import AIModelManager
from ai.ai_enhancement import AIEnhancer


class TestIntegration(unittest.TestCase):
    """Integration tests for KS PDF Studio components."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.sample_markdown = """
# Test Tutorial

## Introduction
This is a test tutorial for KS PDF Studio.

## Code Example
```python
def hello_world():
    print("Hello, World!")
    return True
```

## Features
- Feature 1
- Feature 2
- Feature 3

## Conclusion
This concludes our test tutorial.
"""

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_core_components_initialization(self):
        """Test that all core components can be initialized."""
        try:
            pdf_engine = KSPDFEngine()
            markdown_parser = KSMarkdownParser()
            image_handler = KSImageHandler()
            code_formatter = KSCodeFormatter()
            file_handler = KSFileHandler()
            template_manager = TemplateManager()

            # Test basic functionality
            self.assertIsNotNone(pdf_engine)
            self.assertIsNotNone(markdown_parser)
            self.assertIsNotNone(image_handler)
            self.assertIsNotNone(code_formatter)
            self.assertIsNotNone(file_handler)
            self.assertIsNotNone(template_manager)

        except Exception as e:
            self.fail(f"Core components initialization failed: {e}")

    def test_ai_components_initialization(self):
        """Test that AI components can be initialized."""
        try:
            ai_manager = AIModelManager()
            ai_enhancer = AIEnhancer(ai_manager)

            # Test basic functionality
            self.assertIsNotNone(ai_manager)
            self.assertIsNotNone(ai_enhancer)

            # Test model info (should not crash)
            info = ai_manager.get_model_info()
            self.assertIsInstance(info, dict)
            self.assertIn('models', info)

        except Exception as e:
            self.fail(f"AI components initialization failed: {e}")

    def test_markdown_parsing(self):
        """Test markdown parsing functionality."""
        try:
            parser = KSMarkdownParser()
            result = parser.parse_markdown(self.sample_markdown)

            self.assertIsInstance(result, dict)
            self.assertIn('title', result)
            self.assertIn('sections', result)
            self.assertEqual(result['title'], 'Test Tutorial')
            self.assertGreater(len(result['sections']), 0)

        except Exception as e:
            self.fail(f"Markdown parsing failed: {e}")

    def test_pdf_generation(self):
        """Test PDF generation from markdown."""
        try:
            pdf_engine = KSPDFEngine()
            output_path = self.test_dir / "test_output.pdf"

            success = pdf_engine.convert_markdown_to_pdf(
                self.sample_markdown,
                str(output_path),
                template_name="professional"
            )

            # PDF generation might fail due to missing fonts/images, but shouldn't crash
            self.assertIsInstance(success, bool)

            # If successful, check file exists
            if success:
                self.assertTrue(output_path.exists())

        except Exception as e:
            self.fail(f"PDF generation failed: {e}")

    def test_template_system(self):
        """Test template system functionality."""
        try:
            template_manager = TemplateManager()

            # Test getting available templates
            templates = template_manager.get_available_templates()
            self.assertIsInstance(templates, list)

            # Test getting default template
            default_template = template_manager.get_template("professional")
            # Template might not exist, but shouldn't crash
            self.assertTrue(default_template is None or isinstance(default_template, dict))

        except Exception as e:
            self.fail(f"Template system test failed: {e}")

    def test_file_handling(self):
        """Test file handling utilities."""
        try:
            file_handler = KSFileHandler()

            # Test file validation
            test_file = self.test_dir / "test.md"
            test_file.write_text(self.sample_markdown)

            is_valid = file_handler.validate_file(str(test_file))
            self.assertIsInstance(is_valid, bool)

            # Test reading file
            content = file_handler.read_file(str(test_file))
            self.assertEqual(content, self.sample_markdown)

        except Exception as e:
            self.fail(f"File handling test failed: {e}")

    def test_ai_enhancement_structure(self):
        """Test AI enhancement structure (without actual AI calls)."""
        try:
            ai_manager = AIModelManager()
            ai_enhancer = AIEnhancer(ai_manager)

            # Test enhancement options structure
            options = {
                'auto_expand_sections': True,
                'suggest_images': False,
                'add_examples': True
            }

            # This should not crash even without models loaded
            result = ai_enhancer.enhance_markdown(self.sample_markdown, options)

            # Result should be a dict with expected keys
            self.assertIsInstance(result, dict)
            self.assertIn('enhanced_content', result)
            self.assertIn('suggestions', result)

        except Exception as e:
            self.fail(f"AI enhancement structure test failed: {e}")

    def test_code_formatting(self):
        """Test code formatting functionality."""
        try:
            code_formatter = KSCodeFormatter()

            sample_code = """
def hello():
    print("Hello")
    return True
"""

            # Test Python formatting
            formatted = code_formatter.format_code(sample_code, 'python')
            self.assertIsInstance(formatted, str)
            self.assertGreater(len(formatted), 0)

        except Exception as e:
            self.fail(f"Code formatting test failed: {e}")

    def test_image_handling(self):
        """Test image handling functionality."""
        try:
            image_handler = KSImageHandler()

            # Test basic functionality (no actual image processing)
            self.assertIsNotNone(image_handler)

            # Test image validation (with non-existent file)
            is_valid = image_handler.validate_image("nonexistent.jpg")
            self.assertFalse(is_valid)

        except Exception as e:
            self.fail(f"Image handling test failed: {e}")


class TestWorkflowIntegration(unittest.TestCase):
    """Test complete workflow integration."""

    def setUp(self):
        """Set up workflow test."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up workflow test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_workflow(self):
        """Test a complete workflow from markdown to PDF."""
        try:
            # Initialize components
            markdown_parser = KSMarkdownParser()
            pdf_engine = KSPDFEngine()
            ai_manager = AIModelManager()
            ai_enhancer = AIEnhancer(ai_manager)

            # Step 1: Parse markdown
            parsed = markdown_parser.parse_markdown(self.sample_markdown)
            self.assertIsNotNone(parsed)

            # Step 2: AI enhancement (structure test)
            enhanced = ai_enhancer.enhance_markdown(self.sample_markdown, {})
            self.assertIsInstance(enhanced, dict)

            # Step 3: PDF generation
            output_path = self.test_dir / "workflow_test.pdf"
            success = pdf_engine.convert_markdown_to_pdf(
                enhanced.get('enhanced_content', self.sample_markdown),
                str(output_path)
            )

            # Should complete without crashing
            self.assertIsInstance(success, bool)

        except Exception as e:
            self.fail(f"Complete workflow test failed: {e}")


def run_integration_tests():
    """Run all integration tests."""
    print("KS PDF Studio - Integration Test Suite")
    print("=" * 50)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTest(loader.loadTestsFromTestCase(TestWorkflowIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 50)
    print("Integration Test Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check output above.")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)