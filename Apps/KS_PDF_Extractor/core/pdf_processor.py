"""
KS PDF Extractor - Core Processing Module
========================================

Core functionality for extracting text from PDF files and converting 
to various output formats (text, markdown).

Following KS principles:
- Modular design
- Error handling
- Performance optimization
- Clear interfaces
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# PDF processing library
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF_LIBS = True
except ImportError:
    HAS_PDF_LIBS = False
    print("⚠️  PDF processing libraries not found. Install with: pip install PyPDF2 pdfplumber")

class PDFExtractor:
    """
    Core PDF text extraction engine
    
    Supports multiple extraction methods and output formats
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration"""
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration settings"""
        return {
            'method': 'pdfplumber',  # 'pypdf2' or 'pdfplumber'
            'preserve_formatting': True,
            'clean_text': True,
            'extract_metadata': True,
            'page_separator': '\n\n---\n\n',
            'chunk_size': 1000000,  # Max chars per chunk
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the extractor"""
        logger = logging.getLogger('ks_pdf_extractor')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted text, metadata, and status
        """
        if not HAS_PDF_LIBS:
            raise ImportError("PDF processing libraries not available. Install PyPDF2 and pdfplumber.")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        self.logger.info(f"🔍 Extracting text from: {pdf_path.name}")
        
        try:
            method = self.config.get('method') or self.config.get('extraction_method') or 'pdfplumber'
            if method == 'pdfplumber':
                return self._extract_with_pdfplumber(pdf_path)
            else:
                return self._extract_with_pypdf2(pdf_path)
                
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {},
                'page_count': 0
            }
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using pdfplumber (more accurate)"""
        result = {
            'success': True,
            'text': '',
            'metadata': {},
            'page_count': 0,
            'pages': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            result['page_count'] = len(pdf.pages)
            result['metadata'] = pdf.metadata or {}
            
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text() or ''
                    if self.config['clean_text']:
                        page_text = self._clean_text(page_text)
                    
                    result['pages'].append({
                        'page_num': i + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Page {i+1} extraction failed: {e}")
                    result['pages'].append({
                        'page_num': i + 1,
                        'text': f'[Page {i+1} extraction failed: {e}]',
                        'char_count': 0
                    })
        
        # Combine all pages
        if self.config['page_separator']:
            result['text'] = self.config['page_separator'].join([p['text'] for p in result['pages'] if p['text']])
        else:
            result['text'] = '\n'.join([p['text'] for p in result['pages'] if p['text']])
        
        self.logger.info(f"✅ Extracted {len(result['text'])} characters from {result['page_count']} pages")
        return result
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text using PyPDF2 (fallback method)"""
        result = {
            'success': True,
            'text': '',
            'metadata': {},
            'page_count': 0,
            'pages': []
        }
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            result['page_count'] = len(reader.pages)
            result['metadata'] = reader.metadata or {}
            
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ''
                    if self.config['clean_text']:
                        page_text = self._clean_text(page_text)
                    
                    result['pages'].append({
                        'page_num': i + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Page {i+1} extraction failed: {e}")
                    result['pages'].append({
                        'page_num': i + 1,
                        'text': f'[Page {i+1} extraction failed: {e}]',
                        'char_count': 0
                    })
        
        # Combine all pages
        if self.config['page_separator']:
            result['text'] = self.config['page_separator'].join([p['text'] for p in result['pages'] if p['text']])
        else:
            result['text'] = '\n'.join([p['text'] for p in result['pages'] if p['text']])
        
        self.logger.info(f"✅ Extracted {len(result['text'])} characters from {result['page_count']} pages")
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return text
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = text.strip()
        
        return text
    
    def format_as_markdown(self, extraction_result: Dict[str, Any], title: Optional[str] = None) -> str:
        """
        Format extracted text as Markdown
        
        Args:
            extraction_result: Result from extract_text()
            title: Optional title for the document
            
        Returns:
            Formatted markdown string
        """
        if not extraction_result['success']:
            return f"# PDF Extraction Failed\n\n**Error:** {extraction_result.get('error', 'Unknown error')}\n"
        
        md_content = []
        
        # Title
        if title:
            md_content.append(f"# {title}\n")
        else:
            md_content.append("# Extracted PDF Content\n")
        
        # Metadata section
        if self.config['extract_metadata'] and extraction_result.get('metadata'):
            md_content.append("## Document Information\n")
            metadata = extraction_result['metadata']
            
            if metadata.get('title'):
                md_content.append(f"**Title:** {metadata['title']}  ")
            if metadata.get('author'):
                md_content.append(f"**Author:** {metadata['author']}  ")
            if metadata.get('subject'):
                md_content.append(f"**Subject:** {metadata['subject']}  ")
            if metadata.get('creator'):
                md_content.append(f"**Creator:** {metadata['creator']}  ")
            
            md_content.append(f"**Pages:** {extraction_result['page_count']}  ")
            md_content.append(f"**Characters:** {len(extraction_result['text'])}  ")
            md_content.append("")
        
        # Content section
        md_content.append("## Content\n")
        md_content.append(extraction_result['text'])
        
        return '\n'.join(md_content)
    
    def batch_extract(self, input_dir: str, output_dir: str, format_type: str = 'txt') -> List[Dict[str, Any]]:
        """
        Extract text from all PDFs in a directory
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted files
            format_type: Output format ('txt' or 'md')
            
        Returns:
            List of processing results
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_path}")
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(input_path.glob('*.pdf')) + list(input_path.glob('*.PDF'))
        
        if not pdf_files:
            self.logger.warning(f"⚠️  No PDF files found in: {input_path}")
            return []
        
        results = []
        self.logger.info(f"🔄 Processing {len(pdf_files)} PDF files...")
        
        for pdf_file in pdf_files:
            try:
                # Extract text
                extraction_result = self.extract_text(pdf_file)
                
                # Prepare output filename
                base_name = pdf_file.stem
                if format_type.lower() == 'md':
                    output_file = output_path / f"{base_name}.md"
                    content = self.format_as_markdown(extraction_result, base_name)
                else:
                    output_file = output_path / f"{base_name}.txt"
                    content = extraction_result['text']
                
                # Save to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                result = {
                    'pdf_file': str(pdf_file),
                    'output_file': str(output_file),
                    'success': True,
                    'char_count': len(extraction_result['text']),
                    'page_count': extraction_result['page_count']
                }
                
                self.logger.info(f"✅ {pdf_file.name} → {output_file.name}")
                
            except Exception as e:
                result = {
                    'pdf_file': str(pdf_file),
                    'output_file': None,
                    'success': False,
                    'error': str(e)
                }
                self.logger.error(f"❌ Failed to process {pdf_file.name}: {e}")
            
            results.append(result)
        
        successful = sum(1 for r in results if r['success'])
        self.logger.info(f"🎉 Batch processing complete: {successful}/{len(results)} files processed successfully")
        
        return results