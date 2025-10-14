"""
KS PDF Studio - PDF Extraction Module
Extract text content from existing PDF files for repurposing.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging

# PDF processing libraries
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF_LIBS = True
except ImportError:
    HAS_PDF_LIBS = False

class KSPDFExtractor:
    """
    PDF text extraction engine for KS PDF Studio.

    Supports multiple extraction methods and output formats.
    Used for repurposing existing PDF content into tutorials.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF extractor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger('ks_pdf_studio.extractor')

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'method': 'pdfplumber',  # 'pdfplumber' or 'pypdf2'
            'preserve_formatting': True,
            'clean_text': True,
            'extract_metadata': True,
            'page_separator': '\n\n--- Page {page} ---\n\n',
            'chunk_size': 1000000,
            'include_page_numbers': True,
        }

    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary containing extracted text and metadata
        """
        if not HAS_PDF_LIBS:
            raise ImportError("PDF extraction requires PyPDF2 and pdfplumber. Install with: pip install PyPDF2 pdfplumber")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

        self.logger.info(f"Extracting text from: {pdf_path.name}")

        try:
            method = self.config.get('method', 'pdfplumber')
            if method == 'pdfplumber':
                return self._extract_with_pdfplumber(pdf_path)
            else:
                return self._extract_with_pypdf2(pdf_path)

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {},
                'page_count': 0,
                'pages': []
            }

    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using pdfplumber (more accurate)."""
        result = {
            'success': True,
            'text': '',
            'metadata': {},
            'page_count': 0,
            'pages': [],
            'file_path': str(pdf_path)
        }

        with pdfplumber.open(pdf_path) as pdf:
            result['page_count'] = len(pdf.pages)
            result['metadata'] = pdf.metadata or {}

            page_texts = []
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text() or ''
                    if self.config['clean_text']:
                        page_text = self._clean_text(page_text)

                    page_data = {
                        'page_num': i + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    }
                    result['pages'].append(page_data)

                    # Format page text with separator
                    if page_text.strip():
                        if self.config['include_page_numbers']:
                            separator = self.config['page_separator'].format(page=i+1)
                            page_texts.append(f"{separator}{page_text}")
                        else:
                            page_texts.append(page_text)

                except Exception as e:
                    self.logger.warning(f"Page {i+1} extraction failed: {e}")
                    page_data = {
                        'page_num': i + 1,
                        'text': f'[Page {i+1} extraction failed: {e}]',
                        'char_count': 0
                    }
                    result['pages'].append(page_data)

        # Combine all pages
        result['text'] = '\n\n'.join(page_texts)
        result['total_chars'] = len(result['text'])

        self.logger.info(f"Extracted {result['total_chars']} characters from {result['page_count']} pages")
        return result

    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using PyPDF2 (fallback method)."""
        result = {
            'success': True,
            'text': '',
            'metadata': {},
            'page_count': 0,
            'pages': [],
            'file_path': str(pdf_path)
        }

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            result['page_count'] = len(pdf_reader.pages)

            # Extract metadata if available
            if pdf_reader.metadata:
                result['metadata'] = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                }

            page_texts = []
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if self.config['clean_text']:
                        page_text = self._clean_text(page_text)

                    page_data = {
                        'page_num': i + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    }
                    result['pages'].append(page_data)

                    # Format page text with separator
                    if page_text.strip():
                        if self.config['include_page_numbers']:
                            separator = self.config['page_separator'].format(page=i+1)
                            page_texts.append(f"{separator}{page_text}")
                        else:
                            page_texts.append(page_text)

                except Exception as e:
                    self.logger.warning(f"Page {i+1} extraction failed: {e}")
                    page_data = {
                        'page_num': i + 1,
                        'text': f'[Page {i+1} extraction failed: {e}]',
                        'char_count': 0
                    }
                    result['pages'].append(page_data)

        # Combine all pages
        result['text'] = '\n\n'.join(page_texts)
        result['total_chars'] = len(result['text'])

        return result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""

        # Remove excessive whitespace
        import re
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n +', '\n', text)  # Spaces after newlines

        # Fix common OCR issues
        text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)  # Broken words
        text = re.sub(r'([A-Z])\n([a-z])', r'\1\2', text)  # Title case words

        return text.strip()

    def extract_to_markdown(self, pdf_path: str) -> str:
        """
        Extract PDF content and convert to markdown format.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Markdown formatted text
        """
        result = self.extract_text(pdf_path)
        if not result['success']:
            return f"# PDF Extraction Failed\n\nError: {result['error']}"

        # Convert to markdown
        markdown_lines = []

        # Add header with metadata
        markdown_lines.append("# Extracted PDF Content\n")
        markdown_lines.append(f"**Source:** {Path(pdf_path).name}")
        markdown_lines.append(f"**Pages:** {result['page_count']}")
        markdown_lines.append(f"**Characters:** {result.get('total_chars', 0)}\n")

        # Add metadata if available
        if result['metadata']:
            markdown_lines.append("## Document Metadata\n")
            for key, value in result['metadata'].items():
                if value:
                    markdown_lines.append(f"- **{key}:** {value}")
            markdown_lines.append("")

        # Add content
        markdown_lines.append("## Content\n")

        for page in result['pages']:
            if page['text'].strip():
                if self.config['include_page_numbers']:
                    markdown_lines.append(f"### Page {page['page_num']}\n")
                markdown_lines.append(page['text'])
                markdown_lines.append("")

        return '\n'.join(markdown_lines)

    def batch_extract(self, pdf_paths: List[str], output_dir: str,
                     format_type: str = 'txt') -> List[Dict[str, Any]]:
        """
        Extract text from multiple PDF files.

        Args:
            pdf_paths: List of PDF file paths
            output_dir: Directory to save extracted files
            format_type: Output format ('txt' or 'md')

        Returns:
            List of extraction results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for pdf_path in pdf_paths:
            try:
                pdf_path = Path(pdf_path)
                if format_type == 'md':
                    content = self.extract_to_markdown(str(pdf_path))
                    output_path = output_dir / f"{pdf_path.stem}_extracted.md"
                else:
                    result = self.extract_text(str(pdf_path))
                    content = result['text']
                    output_path = output_dir / f"{pdf_path.stem}_extracted.txt"

                # Save to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                result = {
                    'success': True,
                    'input_file': str(pdf_path),
                    'output_file': str(output_path),
                    'format': format_type,
                    'char_count': len(content)
                }

            except Exception as e:
                result = {
                    'success': False,
                    'input_file': str(pdf_path),
                    'error': str(e)
                }

            results.append(result)

        return results


class PDFExtractorUtils:
    """Utility functions for PDF extraction."""

    @staticmethod
    def detect_pdf_encoding(pdf_path: str) -> str:
        """Detect the encoding of a PDF file."""
        try:
            with open(pdf_path, 'rb') as f:
                # Read first few bytes to detect encoding hints
                header = f.read(1024)
                if b'charset=utf-8' in header.lower():
                    return 'utf-8'
                elif b'charset=latin-1' in header.lower():
                    return 'latin-1'
                else:
                    return 'utf-8'  # Default
        except:
            return 'utf-8'

    @staticmethod
    def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
        """Get basic information about a PDF file."""
        if not HAS_PDF_LIBS:
            return {'error': 'PDF libraries not available'}

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return {
                    'page_count': len(pdf_reader.pages),
                    'metadata': pdf_reader.metadata,
                    'file_size': Path(pdf_path).stat().st_size
                }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """Validate if a file is a readable PDF."""
        if not HAS_PDF_LIBS:
            return False

        try:
            with open(pdf_path, 'rb') as file:
                PyPDF2.PdfReader(file)
            return True
        except:
            return False