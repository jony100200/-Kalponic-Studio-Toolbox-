"""
KS PDF Studio - Core PDF Engine
Professional PDF generation from markdown content with advanced formatting.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, Preformatted, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as ET

from PIL import Image as PILImage
import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import TerminalFormatter


class KSPDFEngine:
    """
    Core PDF generation engine for KS PDF Studio.

    Features:
    - Markdown to PDF conversion
    - Image embedding and processing
    - Code syntax highlighting
    - Table rendering
    - Professional styling
    - Custom templates support
    """

    def __init__(self, page_size=A4, margins=(1*inch, 1*inch, 1*inch, 1*inch)):
        """
        Initialize the PDF engine.

        Args:
            page_size: ReportLab page size (default: A4)
            margins: Page margins as (left, right, top, bottom) tuple
        """
        self.page_size = page_size
        self.margins = margins
        self.styles = self._setup_styles()
        self.markdown_converter = self._setup_markdown()

    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Set up professional PDF styles."""
        styles = getSampleStyleSheet()

        # Custom styles for tutorial content
        styles.add(ParagraphStyle(
            name='TutorialTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.darkblue
        ))

        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.darkgreen,
            borderColor=colors.lightgrey,
            borderWidth=1,
            borderPadding=5
        ))

        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.darkslategray
        ))

        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Code'],
            fontSize=10,
            fontName='Courier',
            backColor=colors.lightgrey,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=5,
            spaceAfter=15
        ))

        styles.add(ParagraphStyle(
            name='TutorialBody',
            parent=styles['Normal'],
            fontSize=11,
            lineHeight=1.4,
            spaceAfter=12
        ))

        return styles

    def _setup_markdown(self) -> Markdown:
        """Set up markdown converter with extensions."""
        # Configure markdown extensions
        extensions = [
            'fenced_code',      # Code blocks with ```
            'tables',           # Table support
            'toc',             # Table of contents
            'meta',            # Metadata support
            'nl2br',           # Newlines to <br>
            CodeBlockExtension(),  # Custom code highlighting
        ]

        return Markdown(extensions=extensions)

    def convert_markdown_to_pdf(
        self,
        markdown_content: str,
        output_path: Union[str, Path],
        title: Optional[str] = None,
        author: Optional[str] = None,
        template: Optional[str] = None
    ) -> bool:
        """
        Convert markdown content to PDF.

        Args:
            markdown_content: Raw markdown string
            output_path: Path to save the PDF
            title: Document title (extracted from markdown if not provided)
            author: Document author
            template: Template name for styling

        Returns:
            bool: True if conversion successful
        """
        try:
            # Parse markdown to HTML
            html_content = self.markdown_converter.convert(markdown_content)

            # Extract metadata if available
            metadata = getattr(self.markdown_converter, 'Meta', {})

            # Use metadata or provided values
            doc_title = title or metadata.get('title', ['Untitled'])[0]
            doc_author = author or metadata.get('author', ['Kalponic Studio'])[0]

            # Convert HTML to PDF elements
            pdf_elements = self._html_to_pdf_elements(html_content)

            # Generate PDF
            self._generate_pdf(pdf_elements, output_path, doc_title, doc_author)

            return True

        except Exception as e:
            print(f"PDF conversion failed: {e}")
            return False

    def _html_to_pdf_elements(self, html_content: str) -> List[Flowable]:
        """Convert HTML content to ReportLab flowable elements."""
        elements = []

        # Parse HTML
        root = ET.fromstring(f"<div>{html_content}</div>")

        for element in root:
            if element.tag == 'h1':
                elements.append(Paragraph(element.text or "", self.styles['TutorialTitle']))
                elements.append(Spacer(1, 20))

            elif element.tag in ['h2', 'h3']:
                style = self.styles['SectionHeader'] if element.tag == 'h2' else self.styles['SubsectionHeader']
                elements.append(Paragraph(element.text or "", style))
                elements.append(Spacer(1, 10))

            elif element.tag == 'p':
                elements.append(Paragraph(element.text or "", self.styles['TutorialBody']))

            elif element.tag == 'pre':
                # Code block
                code_element = element.find('code')
                code_text = code_element.text if code_element is not None else element.text or ""
                elements.append(Preformatted(code_text, self.styles['CodeBlock']))

            elif element.tag == 'table':
                table_data = self._parse_table(element)
                if table_data:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 15))

            elif element.tag == 'img':
                img_path = element.get('src')
                if img_path and os.path.exists(img_path):
                    try:
                        img = self._process_image(img_path)
                        elements.append(img)
                        elements.append(Spacer(1, 10))
                    except Exception as e:
                        print(f"Failed to process image {img_path}: {e}")

            elif element.tag == 'br':
                elements.append(Spacer(1, 5))

        return elements

    def _parse_table(self, table_element) -> List[List[str]]:
        """Parse HTML table to data structure."""
        rows = []
        for tr in table_element.findall('tr'):
            row = []
            for td in tr.findall(['td', 'th']):
                row.append(td.text or "")
            if row:
                rows.append(row)
        return rows

    def _process_image(self, image_path: str) -> Image:
        """Process and optimize image for PDF."""
        # Open image with PIL
        pil_img = PILImage.open(image_path)

        # Calculate size (max width: 6 inches, maintain aspect ratio)
        max_width = 6 * inch
        width, height = pil_img.size
        aspect_ratio = height / width

        if width > max_width:
            width = max_width
            height = width * aspect_ratio

        # Convert to RGB if necessary
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')

        # Create ReportLab Image
        rl_img = Image(image_path, width=width, height=height)
        return rl_img

    def _generate_pdf(
        self,
        elements: List[Flowable],
        output_path: Union[str, Path],
        title: str,
        author: str
    ) -> None:
        """Generate the final PDF document."""
        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            leftMargin=self.margins[0],
            rightMargin=self.margins[1],
            topMargin=self.margins[2],
            bottomMargin=self.margins[3]
        )

        # Set document info
        doc.title = title
        doc.author = author

        # Build PDF
        doc.build(elements)


class CodeBlockExtension(Extension):
    """Custom markdown extension for code block processing."""

    def extendMarkdown(self, md):
        # Add code block processor
        md.treeprocessors.register(CodeBlockProcessor(md), 'code_block', 0)


class CodeBlockProcessor(Treeprocessor):
    """Process code blocks with syntax highlighting."""

    def run(self, root):
        """Process code blocks in the markdown tree."""
        for element in root.iter('pre'):
            code_element = element.find('code')
            if code_element is not None:
                # Extract language from class
                classes = code_element.get('class', [])
                if isinstance(classes, str):
                    classes = classes.split()

                language = None
                for cls in classes:
                    if cls.startswith('language-'):
                        language = cls[9:]  # Remove 'language-' prefix
                        break

                # Apply syntax highlighting if language detected
                if language:
                    try:
                        lexer = get_lexer_by_name(language)
                        code_text = code_element.text or ""
                        # Note: For PDF, we'll handle highlighting in the PDF generation
                        # This is just for structure
                    except:
                        pass  # Fall back to plain text

        return root


# Convenience function for quick conversion
def convert_markdown_to_pdf(
    markdown_file: Union[str, Path],
    output_file: Union[str, Path],
    **kwargs
) -> bool:
    """
    Quick conversion function for markdown files.

    Args:
        markdown_file: Path to markdown file
        output_file: Path to output PDF
        **kwargs: Additional arguments for KSPDFEngine.convert_markdown_to_pdf

    Returns:
        bool: True if conversion successful
    """
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create engine and convert
    engine = KSPDFEngine()
    return engine.convert_markdown_to_pdf(content, output_file, **kwargs)


if __name__ == "__main__":
    # Test the engine
    test_markdown = """
# KS PDF Studio Test Document

## Introduction

This is a test document for the KS PDF Studio PDF generation engine.

## Features

- Markdown to PDF conversion
- Code syntax highlighting
- Image embedding
- Table support

### Code Example

```python
def hello_world():
    print("Hello, KS PDF Studio!")
    return True
```

### Sample Table

| Feature | Status | Notes |
|---------|--------|-------|
| PDF Generation | ✅ Complete | ReportLab integration |
| Markdown Support | ✅ Complete | Full extension support |
| Image Processing | 🚧 In Progress | PIL integration |
| Code Highlighting | 📋 Planned | Pygments integration |

## Conclusion

This document demonstrates the capabilities of the KS PDF Studio engine.
"""

    # Test conversion
    engine = KSPDFEngine()
    success = engine.convert_markdown_to_pdf(
        test_markdown,
        "test_output.pdf",
        title="KS PDF Studio Test",
        author="Kalponic Studio"
    )

    if success:
        print("✅ PDF generated successfully: test_output.pdf")
    else:
        print("❌ PDF generation failed")