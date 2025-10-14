"""
KS PDF Extractor - Test Suite
=============================

Unit tests for the PDF extractor functionality.
Following KS testing principles: comprehensive, clear, fast.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.pdf_processor import PDFExtractor
    from config.config_manager import ConfigManager
    from utils.file_utils import FileUtils, TextUtils, MarkdownUtils
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class TestFileUtils(unittest.TestCase):
    """Test file utility functions"""
    
    def test_safe_filename(self):
        """Test safe filename generation"""
        # Test invalid characters
        unsafe = "test<>:\"/\\|?*.pdf"
        safe = FileUtils.get_safe_filename(unsafe)
        self.assertNotIn('<', safe)
        self.assertNotIn('>', safe)
        self.assertNotIn(':', safe)
        
        # Test length limiting
        long_name = "a" * 300
        safe = FileUtils.get_safe_filename(long_name)
        self.assertLessEqual(len(safe), 255)
        
        # Test empty name
        safe = FileUtils.get_safe_filename("")
        self.assertEqual(safe, "extracted_content")
    
    def test_format_file_size(self):
        """Test file size formatting"""
        self.assertEqual(FileUtils.format_file_size(0), "0 B")
        self.assertEqual(FileUtils.format_file_size(1024), "1.0 KB")
        self.assertEqual(FileUtils.format_file_size(1024 * 1024), "1.0 MB")

class TestTextUtils(unittest.TestCase):
    """Test text utility functions"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "Hello\\x00\\x08   world\\n\\n\\n\\nTest"
        clean = TextUtils.clean_text(dirty_text)
        
        # Should remove null characters
        self.assertNotIn('\\x00', clean)
        
        # Should normalize whitespace
        self.assertNotIn('   ', clean)
    
    def test_count_words(self):
        """Test word counting"""
        text = "Hello world! This is a test."
        count = TextUtils.count_words(text)
        self.assertEqual(count, 6)
        
        # Test empty text
        self.assertEqual(TextUtils.count_words(""), 0)
        self.assertEqual(TextUtils.count_words(None), 0)
    
    def test_get_text_stats(self):
        """Test text statistics"""
        text = "Hello world!\\n\\nThis is a test.\\nAnother line."
        stats = TextUtils.get_text_stats(text)
        
        self.assertIsInstance(stats['characters'], int)
        self.assertIsInstance(stats['words'], int)
        self.assertIsInstance(stats['lines'], int)
        self.assertIsInstance(stats['paragraphs'], int)
        
        self.assertGreater(stats['characters'], 0)
        self.assertGreater(stats['words'], 0)
    
    def test_extract_title(self):
        """Test title extraction"""
        text = "Chapter 1: Introduction\\n\\nThis is the content of the chapter."
        title = TextUtils.extract_title(text)
        
        self.assertIsNotNone(title)
        self.assertIn("Chapter", title)
        
        # Test with no clear title
        text = "123\\n\\n\\nSome random content."
        title = TextUtils.extract_title(text)
        # Should skip page numbers
        self.assertNotEqual(title, "123")
    
    def test_split_into_chunks(self):
        """Test text chunking"""
        text = "This is a long text. " * 100
        chunks = TextUtils.split_into_chunks(text, chunk_size=100, overlap=20)
        
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should be roughly the right size
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 120)  # Allowing some flexibility

class TestMarkdownUtils(unittest.TestCase):
    """Test markdown utility functions"""
    
    def test_escape_markdown(self):
        """Test markdown escaping"""
        text = "This has *bold* and _italic_ and #header"
        escaped = MarkdownUtils.escape_markdown(text)
        
        self.assertIn('\\*', escaped)
        self.assertIn('\\_', escaped)
        self.assertIn('\\#', escaped)
    
    def test_create_toc(self):
        """Test table of contents generation"""
        markdown = "# Chapter 1\\n\\nContent\\n\\n## Section 1.1\\n\\nMore content\\n\\n# Chapter 2"
        toc = MarkdownUtils.create_toc(markdown)
        
        self.assertIn("Table of Contents", toc)
        self.assertIn("Chapter 1", toc)
        self.assertIn("Section 1.1", toc)
        self.assertIn("Chapter 2", toc)
    
    def test_format_metadata_table(self):
        """Test metadata table formatting"""
        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "pages": 5
        }
        
        table = MarkdownUtils.format_metadata_table(metadata)
        
        self.assertIn("| Property | Value |", table)
        self.assertIn("Test Document", table)
        self.assertIn("Test Author", table)

class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """Test default configuration loading"""
        config = ConfigManager(str(self.config_path))
        
        # Check that defaults are loaded
        self.assertEqual(config.get('extraction.method'), 'pdfplumber')
        self.assertEqual(config.get('output.default_format'), 'md')
        self.assertTrue(config.get('extraction.clean_text'))
    
    def test_config_save_load(self):
        """Test saving and loading configuration"""
        config = ConfigManager(str(self.config_path))
        
        # Modify a setting
        config.set('extraction.method', 'pypdf2')
        config.save_config()
        
        # Create new instance and check if setting persisted
        config2 = ConfigManager(str(self.config_path))
        self.assertEqual(config2.get('extraction.method'), 'pypdf2')
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = ConfigManager(str(self.config_path))
        
        # Test valid config
        errors = config.validate_config()
        self.assertEqual(len(errors), 0)
        
        # Test invalid config
        config.set('extraction.method', 'invalid_method')
        errors = config.validate_config()
        self.assertGreater(len(errors), 0)
    
    def test_config_merge(self):
        """Test configuration merging"""
        config = ConfigManager(str(self.config_path))
        
        # Test that new defaults are merged with existing config
        original_keys = set(config.config.keys())
        
        # Simulate adding new default section
        new_defaults = config.DEFAULT_CONFIG.copy()
        new_defaults['new_section'] = {'new_setting': 'value'}
        
        merged = config._merge_configs(new_defaults, config.config)
        
        # Should have all original keys plus new section
        self.assertTrue('new_section' in merged)
        self.assertTrue(all(key in merged for key in original_keys))

class TestPDFExtractor(unittest.TestCase):
    """Test PDF extraction functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = PDFExtractor()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        self.assertIsNotNone(self.extractor)
        self.assertIsNotNone(self.extractor.config)
        self.assertIsNotNone(self.extractor.logger)
    
    def test_config_validation(self):
        """Test extractor configuration"""
        # Test with custom config
        custom_config = {
            'extraction_method': 'pypdf2',
            'clean_text': False
        }
        
        extractor = PDFExtractor(custom_config)
        self.assertEqual(extractor.config['extraction_method'], 'pypdf2')
        self.assertFalse(extractor.config['clean_text'])
    
    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        dirty_text = "Hello   world\\n\\n\\n\\nTest"
        clean = self.extractor._clean_text(dirty_text)
        
        # Should normalize excessive whitespace
        self.assertNotIn('   ', clean)
        self.assertLessEqual(clean.count('\\n\\n'), 1)
    
    def test_markdown_formatting(self):
        """Test markdown formatting"""
        # Mock extraction result
        result = {
            'success': True,
            'text': 'This is test content.',
            'metadata': {'title': 'Test Document'},
            'page_count': 1
        }
        
        markdown = self.extractor.format_as_markdown(result, "Test Title")
        
        self.assertIn('# Test Title', markdown)
        self.assertIn('This is test content.', markdown)
        self.assertIn('## Document Information', markdown)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_simulation(self):
        """Test complete workflow without actual PDF files"""
        # This test simulates the workflow without requiring actual PDF files
        # In a real environment, you would test with sample PDF files
        
        config_path = Path(self.temp_dir) / "config.json"
        config = ConfigManager(str(config_path))
        
        # Test configuration
        self.assertTrue(config.save_config())
        self.assertTrue(config_path.exists())
        
        # Test extractor creation
        extractor = PDFExtractor(config.get_extraction_config())
        self.assertIsNotNone(extractor)
        
        print("✅ Integration test completed successfully")

def run_tests():
    """Run all tests"""
    print("🧪 Running KS PDF Extractor Tests")
    print("=" * 50)
    
    # Create test suite
    test_classes = [
        TestFileUtils,
        TestTextUtils,
        TestMarkdownUtils,
        TestConfigManager,
        TestPDFExtractor,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\\n🎉 All tests passed!")
    else:
        print("\\n❌ Some tests failed!")
    
    return success

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)