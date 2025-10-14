"""
KS PDF Extractor - Utility Functions
====================================

Helper utilities for file handling, text processing, and common operations.
Following KS modular design principles.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import hashlib
import datetime
from dataclasses import dataclass

@dataclass
class FileInfo:
    """Information about a processed file"""
    path: str
    name: str
    size: int
    modified: datetime.datetime
    hash: Optional[str] = None

class FileUtils:
    """
    File handling utilities for the PDF extractor
    """
    
    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """
        Create a safe filename for saving extracted content
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Remove or replace invalid characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove excessive whitespace and dots
        safe_chars = re.sub(r'\s+', '_', safe_chars)
        safe_chars = re.sub(r'\.+', '.', safe_chars)
        
        # Ensure it doesn't start/end with dots or spaces
        safe_chars = safe_chars.strip('. ')
        
        # Truncate if too long
        if len(safe_chars) > max_length:
            name, ext = os.path.splitext(safe_chars)
            safe_chars = name[:max_length - len(ext)] + ext
        
        return safe_chars or 'extracted_content'
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if necessary
        
        Args:
            path: Directory path
            
        Returns:
            Path object
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path], calculate_hash: bool = False) -> FileInfo:
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            calculate_hash: Whether to calculate file hash
            
        Returns:
            FileInfo object
        """
        path = Path(file_path)
        stat = path.stat()
        
        file_hash = None
        if calculate_hash:
            file_hash = FileUtils.calculate_file_hash(path)
        
        return FileInfo(
            path=str(path),
            name=path.name,
            size=stat.st_size,
            modified=datetime.datetime.fromtimestamp(stat.st_mtime),
            hash=file_hash
        )
    
    @staticmethod
    def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
        """
        Calculate hash of a file
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*.pdf", recursive: bool = True) -> List[Path]:
        """
        Find files matching pattern in directory
        
        Args:
            directory: Directory to search
            pattern: File pattern (e.g., "*.pdf")
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return []
        
        if recursive:
            return list(dir_path.rglob(pattern))
        else:
            return list(dir_path.glob(pattern))
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

class TextUtils:
    """
    Text processing utilities
    """
    
    @staticmethod
    def clean_text(text: str, preserve_formatting: bool = True) -> str:
        """
        Clean extracted text
        
        Args:
            text: Text to clean
            preserve_formatting: Whether to preserve basic formatting
            
        Returns:
            Cleaned text
        """
        if not text:
            return text
        
        # Remove null characters and other control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        if preserve_formatting:
            # Remove excessive whitespace but preserve structure
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
            text = re.sub(r' +\n', '\n', text)  # Remove trailing spaces
            text = re.sub(r'\n +', '\n', text)  # Remove leading spaces after newline
        else:
            # More aggressive cleaning
            text = re.sub(r'\s+', ' ', text)  # All whitespace to single space
        
        return text.strip()
    
    @staticmethod
    def extract_title(text: str, max_length: int = 100) -> Optional[str]:
        """
        Try to extract a title from the beginning of text
        
        Args:
            text: Text to extract title from
            max_length: Maximum title length
            
        Returns:
            Extracted title or None
        """
        if not text:
            return None
        
        # Look for title-like patterns at the beginning
        lines = text.strip().split('\n')
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            
            if not line:
                continue
            
            # Skip if it looks like metadata or page numbers
            if re.match(r'^\d+$', line) or 'page' in line.lower():
                continue
            
            # Skip if it's too short or too long
            if len(line) < 10 or len(line) > max_length:
                continue
            
            # Skip if it has too many special characters
            special_ratio = len(re.findall(r'[^\w\s]', line)) / len(line)
            if special_ratio > 0.3:
                continue
            
            return line
        
        return None
    
    @staticmethod
    def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to split
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                # Look for space within last 100 characters
                last_space = text.rfind(' ', start, end)
                if last_space > start + chunk_size - 100:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(end - overlap, start + 1)
            
            if start >= len(text):
                break
        
        return chunks
    
    @staticmethod
    def count_words(text: str) -> int:
        """
        Count words in text
        
        Args:
            text: Text to count
            
        Returns:
            Word count
        """
        if not text:
            return 0
        
        # Split on whitespace and filter empty strings
        words = [word for word in re.split(r'\s+', text.strip()) if word]
        return len(words)
    
    @staticmethod
    def get_text_stats(text: str) -> Dict[str, int]:
        """
        Get statistics about text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with text statistics
        """
        if not text:
            return {
                'characters': 0,
                'words': 0,
                'lines': 0,
                'paragraphs': 0
            }
        
        return {
            'characters': len(text),
            'words': TextUtils.count_words(text),
            'lines': len(text.split('\n')),
            'paragraphs': len([p for p in text.split('\n\n') if p.strip()])
        }

class MarkdownUtils:
    """
    Markdown formatting utilities
    """
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special markdown characters
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        # Characters that need escaping in markdown
        escape_chars = r'\\`*_{}[]()#+-.!'
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def create_toc(text: str) -> str:
        """
        Create table of contents from markdown headers
        
        Args:
            text: Markdown text
            
        Returns:
            Table of contents markdown
        """
        toc_lines = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Match headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level <= 6:  # Valid header levels
                    title = line.lstrip('#').strip()
                    if title:
                        indent = '  ' * (level - 1)
                        link = title.lower().replace(' ', '-')
                        link = re.sub(r'[^\w\-]', '', link)
                        toc_lines.append(f"{indent}- [{title}](#{link})")
        
        if toc_lines:
            return "## Table of Contents\n\n" + '\n'.join(toc_lines) + '\n\n'
        
        return ""
    
    @staticmethod
    def format_metadata_table(metadata: Dict[str, Any]) -> str:
        """
        Format metadata as markdown table
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted markdown table
        """
        if not metadata:
            return ""
        
        table_lines = [
            "| Property | Value |",
            "|----------|-------|"
        ]
        
        for key, value in metadata.items():
            if value is not None:
                key_formatted = key.replace('_', ' ').title()
                value_str = str(value).strip()
                if value_str:
                    # Escape markdown characters in values
                    value_escaped = MarkdownUtils.escape_markdown(value_str)
                    table_lines.append(f"| {key_formatted} | {value_escaped} |")
        
        if len(table_lines) > 2:
            return '\n'.join(table_lines) + '\n\n'
        
        return ""