"""
KS PDF Studio - Core Engine Test
Test script to validate the PDF creation engine components.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from core.pdf_engine import KSPDFEngine, convert_markdown_to_pdf
    from core.markdown_parser import KSMarkdownParser, parse_markdown_file
    from core.image_handler import KSImageHandler, process_image_for_pdf
    from core.code_formatter import KSCodeFormatter, format_code_block
    from templates.base_template import KSPDFTemplate, get_template
    from utils.file_utils import KSFileHandler, validate_file, read_text_file

    print("✅ All imports successful")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_pdf_engine():
    """Test the PDF engine with sample content."""
    print("\n🧪 Testing PDF Engine...")

    # Sample markdown content
    test_markdown = """
# KS PDF Studio Test Document

## Introduction

This is a comprehensive test of the KS PDF Studio PDF generation engine.

## Features

- **Markdown Processing**: Full markdown support with extensions
- **Code Highlighting**: Syntax highlighting for multiple languages
- **Image Support**: Automatic image optimization and embedding
- **Professional Styling**: Custom templates and branding

### Sample Code

```python
def pdf_generation_demo():
    \"\"\"Demonstrate PDF creation capabilities.\"\"\"
    engine = KSPDFEngine()
    success = engine.convert_markdown_to_pdf(
        markdown_content, "output.pdf",
        title="Demo Document",
        author="KS PDF Studio"
    )
    return success
```

## Tables

| Component | Status | Notes |
|-----------|--------|-------|
| PDF Engine | ✅ Complete | ReportLab integration |
| Markdown Parser | ✅ Complete | Custom extensions |
| Image Handler | ✅ Complete | PIL optimization |
| Code Formatter | ✅ Complete | Pygments highlighting |
| Template System | ✅ Complete | Professional styling |

## Conclusion

The KS PDF Studio engine successfully converts markdown to professional PDFs with advanced features.
"""

    # Test PDF generation
    engine = KSPDFEngine()
    output_file = "test_ks_pdf_studio.pdf"

    success = engine.convert_markdown_to_pdf(
        test_markdown,
        output_file,
        title="KS PDF Studio Test Document",
        author="Kalponic Studio"
    )

    if success and os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"✅ PDF Engine: Generated {output_file} ({file_size} bytes)")
        return True
    else:
        print("❌ PDF Engine: Failed to generate PDF")
        return False

def test_markdown_parser():
    """Test the markdown parser."""
    print("\n🧪 Testing Markdown Parser...")

    test_content = """
---
title: Test Document
author: Test Author
---

# Main Title

## Subsection

This is a paragraph with **bold** and *italic* text.

### Code Block

```python
print("Hello, World!")
```

### List

- Item 1
- Item 2
- Item 3

### Table

| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
"""

    parser = KSMarkdownParser()
    result = parser.parse(test_content)

    # Check results
    checks = [
        ('html' in result, "HTML conversion"),
        ('metadata' in result, "Metadata extraction"),
        ('toc' in result, "Table of contents"),
        (len(result.get('code_blocks', [])) > 0, "Code block extraction"),
        (result.get('structure', {}).get('sections', 0) > 0, "Structure analysis")
    ]

    passed = 0
    for check, description in checks:
        if check:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")

    success_rate = passed / len(checks)
    print(f"Markdown Parser: {passed}/{len(checks)} tests passed ({success_rate:.1%})")

    return success_rate >= 0.8

def test_code_formatter():
    """Test the code formatter."""
    print("\n🧪 Testing Code Formatter...")

    test_code = '''
def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
'''

    formatter = KSCodeFormatter()
    result = formatter.format_code_block(test_code, 'python')

    checks = [
        ('html' in result, "HTML formatting"),
        ('latex' in result, "LaTeX formatting"),
        ('pdf' in result, "PDF formatting"),
        (result.get('language') == 'python', "Language detection"),
        (isinstance(result.get('lines'), int), "Line counting")
    ]

    passed = 0
    for check, description in checks:
        if check:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")

    success_rate = passed / len(checks)
    print(f"Code Formatter: {passed}/{len(checks)} tests passed ({success_rate:.1%})")

    return success_rate >= 0.8

def test_template_system():
    """Test the template system."""
    print("\n🧪 Testing Template System...")

    # Test template creation
    template = get_template('professional')

    checks = [
        (hasattr(template, 'styles'), "Style system"),
        (hasattr(template, 'page_size'), "Page configuration"),
        (hasattr(template, 'color_scheme'), "Color scheme"),
        (template.get_style('TutorialBody') is not None, "Body text style"),
        (template.get_style('DocumentTitle') is not None, "Title style")
    ]

    passed = 0
    for check, description in checks:
        if check:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")

    success_rate = passed / len(checks)
    print(f"Template System: {passed}/{len(checks)} tests passed ({success_rate:.1%})")

    return success_rate >= 0.8

def test_file_utils():
    """Test the file utilities."""
    print("\n🧪 Testing File Utilities...")

    handler = KSFileHandler()

    # Test with this script file
    validation = handler.validate_file(__file__)

    checks = [
        (validation['exists'], "File existence check"),
        (validation['readable'], "File readability"),
        (validation['type'] == 'text', "File type detection"),
        (validation['size'] > 0, "File size detection"),
        (validation['extension'] == '.py', "Extension detection")
    ]

    passed = 0
    for check, description in checks:
        if check:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")

    # Test text reading
    content = handler.read_text_file(__file__)
    if content and len(content) > 100:
        print("✅ Text file reading")
        passed += 1
    else:
        print("❌ Text file reading")

    success_rate = passed / (len(checks) + 1)
    print(f"File Utilities: {passed}/{len(checks) + 1} tests passed ({success_rate:.1%})")

    return success_rate >= 0.8

def run_full_integration_test():
    """Run a full integration test."""
    print("\n🔗 Running Full Integration Test...")

    # Create comprehensive test content
    integration_markdown = """
# KS PDF Studio Integration Test

## Complete Workflow Test

This document tests the complete KS PDF Studio workflow from markdown to PDF.

## Code Examples

### Python
```python
from ks_pdf_studio import KSPDFStudio

# Create studio instance
studio = KSPDFStudio()

# Convert markdown to PDF
success = studio.convert_markdown_to_pdf(
    "tutorial.md",
    "tutorial.pdf",
    template="tutorial",
    ai_enhancement=True
)
```

### JavaScript
```javascript
// Example React component for PDF preview
function PDFPreview({ markdown }) {
    const [pdfUrl, setPdfUrl] = useState(null);

    useEffect(() => {
        convertMarkdown(markdown).then(setPdfUrl);
    }, [markdown]);

    return <iframe src={pdfUrl} />;
}
```

## Advanced Features

### Tables with Complex Data

| Feature | Implementation | Status | Notes |
|---------|----------------|--------|-------|
| AI Enhancement | DistilBART + CLIP | ✅ Complete | Optional models |
| Image Processing | PIL + Optimization | ✅ Complete | Auto-resizing |
| Code Highlighting | Pygments | ✅ Complete | 100+ languages |
| Template System | Custom Styling | ✅ Complete | Professional themes |
| Batch Processing | Multi-file | 📋 Planned | Next phase |

### Mathematical Content

The PDF engine supports complex layouts and can handle:

- Multi-column layouts
- Headers and footers
- Table of contents
- Image galleries
- Code with line numbers

## Performance Metrics

Based on testing with 50-page tutorial documents:

- **Generation Time**: < 5 seconds
- **Memory Usage**: < 100MB
- **File Size**: 2-5MB per document
- **Image Quality**: Optimized for print

## Conclusion

The KS PDF Studio successfully demonstrates professional PDF generation capabilities with advanced features for tutorial content creation.
"""

    # Test full pipeline
    try:
        # Parse markdown
        parser = KSMarkdownParser()
        parsed = parser.parse(integration_markdown)

        # Get template
        template = get_template('tutorial')

        # Create PDF engine with template
        engine = KSPDFEngine()

        # Generate PDF
        success = engine.convert_markdown_to_pdf(
            integration_markdown,
            "integration_test.pdf",
            title="KS PDF Studio Integration Test",
            author="Kalponic Studio"
        )

        if success and os.path.exists("integration_test.pdf"):
            file_size = os.path.getsize("integration_test.pdf")
            print(f"✅ Integration Test: Generated PDF ({file_size} bytes)")
            print(f"   - Parsed sections: {parsed['structure']['sections']}")
            print(f"   - Code blocks: {len(parsed['code_blocks'])}")
            print(f"   - Template: {template.template_name}")
            return True
        else:
            print("❌ Integration Test: Failed to generate PDF")
            return False

    except Exception as e:
        print(f"❌ Integration Test: Exception occurred - {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 KS PDF Studio Core Engine Test Suite")
    print("=" * 50)

    # Run individual component tests
    results = {
        'PDF Engine': test_pdf_engine(),
        'Markdown Parser': test_markdown_parser(),
        'Code Formatter': test_code_formatter(),
        'Template System': test_template_system(),
        'File Utilities': test_file_utils(),
        'Integration': run_full_integration_test()
    }

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    success_rate = passed / total
    print(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1%})")

    if success_rate >= 0.8:
        print("🎉 Core engine is ready for development!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())