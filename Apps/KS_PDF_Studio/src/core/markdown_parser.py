"""
KS PDF Studio - Markdown Parser
Enhanced markdown processing with custom extensions for PDF generation.

Author: Kalponic Studio
Version: 2.0.0
"""

import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import InlineProcessor
from markdown.blockprocessors import BlockProcessor

import xml.etree.ElementTree as ET


class KSMarkdownParser:
    """
    Enhanced markdown parser for KS PDF Studio.

    Features:
    - Extended markdown syntax for tutorials
    - Metadata extraction
    - Image processing hints
    - Code block language detection
    - Table formatting
    """

    def __init__(self):
        """Initialize the markdown parser with custom extensions."""
        self.extensions = self._setup_extensions()
        self.markdown = Markdown(extensions=self.extensions)

    def _setup_extensions(self) -> List[Extension]:
        """Set up markdown extensions for tutorial content."""
        return [
            'fenced_code',              # ``` code blocks
            'tables',                   # | table | syntax
            'toc',                      # [TOC] support
            'meta',                     # YAML frontmatter
            'nl2br',                    # Line breaks
            TutorialExtensions(),       # Custom tutorial extensions
            ImageProcessorExtension(),  # Enhanced image processing
            CalloutExtension(),         # Info/note boxes
        ]

    def parse(self, markdown_content: str) -> Dict[str, Any]:
        """
        Parse markdown content and extract structured data.

        Args:
            markdown_content: Raw markdown string

        Returns:
            Dict containing:
            - 'html': Converted HTML
            - 'metadata': Extracted metadata
            - 'toc': Table of contents
            - 'images': List of image references
            - 'code_blocks': List of code blocks with languages
        """
        # Reset markdown instance for clean parsing
        self.markdown.reset()

        # Convert to HTML
        html_content = self.markdown.convert(markdown_content)

        # Extract additional data
        metadata = getattr(self.markdown, 'Meta', {})
        toc = getattr(self.markdown, 'toc', None)

        # Parse for additional elements
        images = self._extract_images(html_content)
        code_blocks = self._extract_code_blocks(markdown_content)

        return {
            'html': html_content,
            'metadata': metadata,
            'toc': toc,
            'images': images,
            'code_blocks': code_blocks,
            'structure': self._analyze_structure(html_content)
        }

    def _extract_images(self, html_content: str) -> List[Dict[str, str]]:
        """Extract image references from HTML content."""
        images = []
        root = ET.fromstring(f"<div>{html_content}</div>")

        for img in root.findall('.//img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')

            if src:
                images.append({
                    'src': src,
                    'alt': alt,
                    'title': title,
                    'path': Path(src) if not src.startswith(('http://', 'https://')) else None
                })

        return images

    def _extract_code_blocks(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract code blocks with language information."""
        code_blocks = []

        # Regex to find fenced code blocks
        fenced_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(fenced_pattern, markdown_content, re.DOTALL)

        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip(),
                'lines': len(code.strip().split('\n'))
            })

        return code_blocks

    def _analyze_structure(self, html_content: str) -> Dict[str, Any]:
        """Analyze document structure for PDF layout hints."""
        root = ET.fromstring(f"<div>{html_content}</div>")

        structure = {
            'headings': [],
            'sections': 0,
            'subsections': 0,
            'paragraphs': 0,
            'code_blocks': 0,
            'tables': 0,
            'images': 0
        }

        # Count elements
        structure['sections'] = len(root.findall('.//h1') + root.findall('.//h2'))
        structure['subsections'] = len(root.findall('.//h3') + root.findall('.//h4'))
        structure['paragraphs'] = len(root.findall('.//p'))
        structure['code_blocks'] = len(root.findall('.//pre'))
        structure['tables'] = len(root.findall('.//table'))
        structure['images'] = len(root.findall('.//img'))

        # Extract heading hierarchy
        for h1 in root.findall('.//h1'):
            structure['headings'].append({
                'level': 1,
                'text': h1.text or "",
                'id': h1.get('id', '')
            })

        for h2 in root.findall('.//h2'):
            structure['headings'].append({
                'level': 2,
                'text': h2.text or "",
                'id': h2.get('id', '')
            })

        return structure

    def validate_content(self, markdown_content: str) -> Dict[str, List[str]]:
        """
        Validate markdown content for PDF generation.

        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        # Check for basic structure
        if not markdown_content.strip():
            errors.append("Document is empty")

        # Check for title
        if not re.search(r'^#\s+', markdown_content, re.MULTILINE):
            warnings.append("No main title (# heading) found")

        # Check for broken links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, markdown_content):
            link_text, link_url = match.groups()
            if not link_url.startswith(('http://', 'https://', '#')):
                # Check if local file exists
                if not Path(link_url).exists():
                    warnings.append(f"Local link may be broken: {link_url}")

        # Check image references
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for match in re.finditer(img_pattern, markdown_content):
            alt_text, img_src = match.groups()
            if not img_src.startswith(('http://', 'https://')):
                if not Path(img_src).exists():
                    warnings.append(f"Image file not found: {img_src}")

        return {
            'errors': errors,
            'warnings': warnings
        }


class TutorialExtensions(Extension):
    """Custom extensions for tutorial content."""

    def extendMarkdown(self, md):
        # Add tutorial-specific processors
        md.preprocessors.register(TutorialPreprocessor(md), 'tutorial_prep', 0)
        md.inlinePatterns.register(IconPattern(r':icon\{([^}]+)\}'), 'icon', 175)
        md.parser.blockprocessors.register(InfoBoxProcessor(md.parser), 'info_box', 175)


class TutorialPreprocessor(Preprocessor):
    """Preprocessor for tutorial-specific syntax."""

    def run(self, lines: List[str]) -> List[str]:
        """Process tutorial-specific markdown extensions."""
        new_lines = []

        for line in lines:
            # Convert tutorial-specific shortcuts
            line = re.sub(r'^>>>>\s*(.+)$', r'<div class="highlight">\1</div>', line)  # Highlight box
            line = re.sub(r'^<<<<\s*(.+)$', r'<div class="warning">\1</div>', line)   # Warning box
            line = re.sub(r'^====\s*(.+)$', r'<div class="info">\1</div>', line)      # Info box

            new_lines.append(line)

        return new_lines


class IconPattern(InlineProcessor):
    """Process icon shortcuts like :icon{name}."""

    def handleMatch(self, m, data):
        """Handle icon pattern matches."""
        icon_name = m.group(1)
        # Return a span with icon class for PDF processing
        el = ET.Element('span')
        el.set('class', f'icon icon-{icon_name}')
        el.text = f'[{icon_name}]'  # Placeholder text for PDF
        return el, m.start(0), m.end(0)


class InfoBoxProcessor(BlockProcessor):
    """Process info/note boxes."""

    def test(self, parent, block):
        """Test if block is an info box."""
        return re.match(r'^:::(info|note|warning|tip)\s*$', block)

    def run(self, parent, blocks):
        """Process info box blocks."""
        block = blocks.pop(0)
        m = re.match(r'^:::(info|note|warning|tip)\s*$', block)

        if m:
            box_type = m.group(1)
            content = []

            # Collect content until closing :::
            while blocks:
                block = blocks[0]
                if re.match(r'^:::$', block):
                    blocks.pop(0)
                    break
                else:
                    content.append(blocks.pop(0))

            # Create div with appropriate class
            div = ET.SubElement(parent, 'div')
            div.set('class', f'callout callout-{box_type}')
            div.text = '\n'.join(content)

        return False


class ImageProcessorExtension(Extension):
    """Enhanced image processing extension."""

    def extendMarkdown(self, md):
        md.treeprocessors.register(ImageProcessor(md), 'image_processor', 0)


class ImageProcessor(Treeprocessor):
    """Process images with size and alignment hints."""

    def run(self, root):
        """Process image elements."""
        for img in root.iter('img'):
            src = img.get('src', '')

            # Parse size hints from src (e.g., image.jpg|300x200)
            if '|' in src:
                src, size_hint = src.split('|', 1)
                img.set('src', src)

                # Parse size (widthxheight)
                if 'x' in size_hint:
                    try:
                        width, height = size_hint.split('x')
                        img.set('width', width)
                        img.set('height', height)
                    except ValueError:
                        pass

        return root


class CalloutExtension(Extension):
    """Extension for callout boxes (info, warning, etc.)."""

    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(CalloutProcessor(md.parser), 'callout', 25)


class CalloutProcessor(BlockProcessor):
    """Process callout blocks."""

    RE = re.compile(r'^:::(\w+)\s*(.*)$')

    def test(self, parent, block):
        return self.RE.match(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.match(block)

        if m:
            callout_type, title = m.groups()
            content = []

            # Collect content until closing :::
            while blocks:
                block = blocks[0]
                if block.strip() == ':::':
                    blocks.pop(0)
                    break
                else:
                    content.append(blocks.pop(0))

            # Create callout div
            div = ET.SubElement(parent, 'div')
            div.set('class', f'callout callout-{callout_type}')

            if title:
                title_el = ET.SubElement(div, 'strong')
                title_el.text = title
                title_el.tail = '\n'

            content_text = '\n'.join(content)
            if content_text:
                content_el = ET.SubElement(div, 'p')
                content_el.text = content_text

        return False


# Convenience functions
def parse_markdown_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Parse a markdown file and return structured data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = KSMarkdownParser()
    return parser.parse(content)


def validate_markdown_file(file_path: Union[str, Path]) -> Dict[str, List[str]]:
    """Validate a markdown file for PDF generation."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = KSMarkdownParser()
    return parser.validate_content(content)


if __name__ == "__main__":
    # Test the parser
    test_content = """
---
title: Test Tutorial
author: Kalponic Studio
date: 2025-10-14
---

# Test Tutorial

## Introduction

This is a test tutorial document.

:::info Important Note
This is an important information box.
:::

## Code Example

```python
def test_function():
    print("Hello, World!")
    return True
```

## Features

- Feature 1
- Feature 2
- Feature 3

| Feature | Status |
|---------|--------|
| Parser | ✅ Working |
| Extensions | ✅ Working |
| Validation | 🚧 In Progress |
"""

    parser = KSMarkdownParser()
    result = parser.parse(test_content)

    print("Parsed successfully!")
    print(f"Metadata: {result['metadata']}")
    print(f"Code blocks: {len(result['code_blocks'])}")
    print(f"Images: {len(result['images'])}")
    print(f"Structure: {result['structure']['sections']} sections")

    # Validate
    validation = parser.validate_content(test_content)
    print(f"Errors: {validation['errors']}")
    print(f"Warnings: {validation['warnings']}")