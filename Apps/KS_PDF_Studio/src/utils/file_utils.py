"""
KS PDF Studio - File Utilities
File handling, validation, and I/O operations for PDF generation.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import hashlib
import shutil
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import mimetypes

from PIL import Image as PILImage


class KSFileHandler:
    """
    Comprehensive file handling for KS PDF Studio.

    Features:
    - File validation and type detection
    - Safe file operations
    - Directory management
    - File hashing and integrity checks
    - Batch file processing
    """

    # Supported file types
    SUPPORTED_TEXT_TYPES = {
        '.md', '.markdown', '.txt', '.rst', '.adoc'
    }

    SUPPORTED_IMAGE_TYPES = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg'
    }

    SUPPORTED_ARCHIVE_TYPES = {
        '.zip', '.tar', '.gz', '.bz2', '.7z'
    }

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the file handler.

        Args:
            base_dir: Base directory for operations
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir.mkdir(exist_ok=True)

    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Comprehensive file validation.

        Args:
            file_path: Path to the file to validate

        Returns:
            Dict with validation results
        """
        file_path = Path(file_path)

        result = {
            'exists': False,
            'readable': False,
            'writable': False,
            'size': 0,
            'type': 'unknown',
            'mime_type': None,
            'extension': file_path.suffix.lower(),
            'is_supported': False,
            'errors': [],
            'warnings': []
        }

        # Check if file exists
        if not file_path.exists():
            result['errors'].append('File does not exist')
            return result

        result['exists'] = True

        # Check permissions
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try to read one byte
            result['readable'] = True
        except:
            result['errors'].append('File is not readable')

        # Check if writable
        try:
            # Try to open in append mode to check write permission
            with open(file_path, 'ab') as f:
                pass
            result['writable'] = True
        except:
            result['warnings'].append('File is not writable')

        # Get file size
        try:
            result['size'] = file_path.stat().st_size
        except:
            result['warnings'].append('Could not determine file size')

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        result['mime_type'] = mime_type

        # Determine file type and support
        if result['extension'] in self.SUPPORTED_TEXT_TYPES:
            result['type'] = 'text'
            result['is_supported'] = True
        elif result['extension'] in self.SUPPORTED_IMAGE_TYPES:
            result['type'] = 'image'
            result['is_supported'] = True
        elif result['extension'] in self.SUPPORTED_ARCHIVE_TYPES:
            result['type'] = 'archive'
            result['is_supported'] = True
        elif result['extension'] == '.pdf':
            result['type'] = 'pdf'
            result['is_supported'] = True
        else:
            result['type'] = 'unknown'
            if result['readable']:
                result['warnings'].append(f'Unsupported file type: {result["extension"]}')

        # Additional checks for large files
        if result['size'] > 100 * 1024 * 1024:  # 100MB
            result['warnings'].append('Very large file - may impact performance')

        return result

    def read_text_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """
        Safely read a text file.

        Args:
            file_path: Path to the text file
            encoding: Text encoding

        Returns:
            File content as string, or None if failed
        """
        validation = self.validate_file(file_path)

        if not validation['exists'] or not validation['readable']:
            return None

        if validation['type'] not in ['text', 'unknown']:
            # Try to read anyway, but warn
            pass

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                return None
        except Exception:
            return None

    def write_text_file(
        self,
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        backup: bool = True
    ) -> bool:
        """
        Safely write a text file.

        Args:
            file_path: Path to write the file
            content: Content to write
            encoding: Text encoding
            backup: Whether to create backup of existing file

        Returns:
            bool: True if successful
        """
        file_path = Path(file_path)

        # Create backup if requested and file exists
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            try:
                shutil.copy2(file_path, backup_path)
            except:
                pass  # Continue even if backup fails

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)

            return True

        except Exception:
            return False

    def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> bool:
        """
        Safely copy a file.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing destination

        Returns:
            bool: True if successful
        """
        source = Path(source)
        destination = Path(destination)

        if not source.exists():
            return False

        if destination.exists() and not overwrite:
            return False

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            return True
        except:
            return False

    def get_file_hash(self, file_path: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file hash for integrity checking.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')

        Returns:
            Hexadecimal hash string, or None if failed
        """
        validation = self.validate_file(file_path)

        if not validation['exists'] or not validation['readable']:
            return None

        hash_func = getattr(hashlib, algorithm, None)
        if not hash_func:
            return None

        try:
            with open(file_path, 'rb') as f:
                hasher = hash_func()
                while chunk := f.read(8192):
                    hasher.update(chunk)
                return hasher.hexdigest()
        except:
            return None

    def find_files(
        self,
        directory: Union[str, Path],
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
        max_depth: Optional[int] = None
    ) -> List[Path]:
        """
        Find files in a directory with optional filtering.

        Args:
            directory: Directory to search
            extensions: List of file extensions to include (with dots)
            recursive: Whether to search subdirectories
            max_depth: Maximum directory depth

        Returns:
            List of matching file paths
        """
        directory = Path(directory)

        if not directory.exists() or not directory.is_dir():
            return []

        files = []
        pattern = '**/*' if recursive else '*'

        try:
            for path in directory.glob(pattern):
                if path.is_file():
                    # Check extension filter
                    if extensions:
                        if path.suffix.lower() in [ext.lower() for ext in extensions]:
                            files.append(path)
                    else:
                        files.append(path)
        except:
            pass

        return files

    def create_directory_structure(self, structure: Dict[str, Any], base_path: Union[str, Path]) -> bool:
        """
        Create a directory structure from a dictionary.

        Args:
            structure: Dictionary defining the structure
            base_path: Base path for creation

        Returns:
            bool: True if successful
        """
        base_path = Path(base_path)

        try:
            for name, content in structure.items():
                current_path = base_path / name

                if isinstance(content, dict):
                    # It's a directory
                    current_path.mkdir(parents=True, exist_ok=True)
                    self.create_directory_structure(content, current_path)
                else:
                    # It's a file
                    current_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, str):
                        with open(current_path, 'w', encoding='utf-8') as f:
                            f.write(content)

            return True

        except Exception:
            return False

    def get_directory_info(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a directory.

        Args:
            directory: Directory path

        Returns:
            Dict with directory information
        """
        directory = Path(directory)

        info = {
            'exists': directory.exists(),
            'is_directory': directory.is_dir(),
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'subdirectories': 0
        }

        if not info['exists'] or not info['is_directory']:
            return info

        try:
            for path in directory.rglob('*'):
                if path.is_file():
                    info['total_files'] += 1
                    info['total_size'] += path.stat().st_size

                    ext = path.suffix.lower() or 'no_extension'
                    info['file_types'][ext] = info['file_types'].get(ext, 0) + 1

                elif path.is_dir():
                    info['subdirectories'] += 1

        except:
            pass

        return info

    def validate_image_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate an image file specifically.

        Args:
            file_path: Path to the image file

        Returns:
            Dict with image validation results
        """
        validation = self.validate_file(file_path)

        if validation['type'] != 'image':
            validation['image_info'] = None
            return validation

        image_info = {
            'dimensions': None,
            'mode': None,
            'format': None,
            'has_transparency': False,
            'estimated_pdf_size': None
        }

        try:
            with PILImage.open(file_path) as img:
                image_info['dimensions'] = img.size
                image_info['mode'] = img.mode
                image_info['format'] = img.format

                # Check for transparency
                if img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'P':
                        # Check if palette has transparency
                        if 'transparency' in img.info:
                            image_info['has_transparency'] = True
                    else:
                        image_info['has_transparency'] = True

                # Estimate PDF size (rough calculation)
                width, height = img.size
                # Assume 150 DPI for PDF
                pdf_width = (width / 150) * 72  # 72 points per inch
                pdf_height = (height / 150) * 72
                image_info['estimated_pdf_size'] = (pdf_width, pdf_height)

        except Exception as e:
            validation['errors'].append(f'Image validation failed: {e}')

        validation['image_info'] = image_info
        return validation


class BatchFileProcessor:
    """Utility for batch file processing operations."""

    def __init__(self, file_handler: KSFileHandler):
        """
        Initialize batch processor.

        Args:
            file_handler: KSFileHandler instance
        """
        self.file_handler = file_handler

    def process_markdown_files(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        processor_func: callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process multiple markdown files.

        Args:
            input_dir: Input directory
            output_dir: Output directory
            processor_func: Function to process each file
            **kwargs: Additional arguments for processor

        Returns:
            Dict with processing results
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }

        # Find markdown files
        md_files = self.file_handler.find_files(input_dir, ['.md', '.markdown'])

        for md_file in md_files:
            try:
                # Read content
                content = self.file_handler.read_text_file(md_file)
                if not content:
                    results['skipped'] += 1
                    continue

                # Process file
                result = processor_func(content, **kwargs)

                # Determine output path
                relative_path = md_file.relative_to(input_dir)
                output_file = output_dir / relative_path.with_suffix('.pdf')

                # Save result (assuming processor returns saveable data)
                if hasattr(result, 'save'):
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    result.save(str(output_file))

                results['processed'] += 1
                results['results'].append({
                    'input': str(md_file),
                    'output': str(output_file),
                    'success': True
                })

            except Exception as e:
                results['failed'] += 1
                results['results'].append({
                    'input': str(md_file),
                    'error': str(e),
                    'success': False
                })

        return results


# Convenience functions
def validate_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Quick file validation."""
    handler = KSFileHandler()
    return handler.validate_file(file_path)


def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Quick text file reading."""
    handler = KSFileHandler()
    return handler.read_text_file(file_path, encoding)


def write_text_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    backup: bool = True
) -> bool:
    """Quick text file writing."""
    handler = KSFileHandler()
    return handler.write_text_file(file_path, content, encoding, backup)


if __name__ == "__main__":
    # Test the file utilities
    print("Testing File Utilities...")

    handler = KSFileHandler()

    # Test file validation
    test_file = "README.md"  # Assuming this exists
    if os.path.exists(test_file):
        validation = handler.validate_file(test_file)
        print(f"✅ File validation: {validation['exists'] and validation['readable']}")

        # Test reading
        content = handler.read_text_file(test_file)
        print(f"✅ File reading: {len(content) if content else 0} characters")

    # Test directory operations
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # Test writing
    success = handler.write_text_file(test_dir / "test.txt", "Hello, KS PDF Studio!")
    print(f"✅ File writing: {success}")

    # Test directory info
    info = handler.get_directory_info(".")
    print(f"✅ Directory scan: {info['total_files']} files found")

    print("File utilities test complete!")