"""
Input/Output operations for file handling.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

logger = logging.getLogger(__name__)

class IOHandler:
    """Handles file input/output operations."""
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    
    def __init__(self):
        pass
    
    def get_image_files(self, folder_path: str) -> List[Path]:
        """
        Get all supported image files from a folder.
        
        Args:
            folder_path: Path to the folder containing images
            
        Returns:
            List of Path objects for supported image files
        """
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            return []
        
        folder = Path(folder_path)
        image_files = []
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                image_files.append(file_path)
        
        logger.info(f"Found {len(image_files)} image files in {folder_path}")
        return sorted(image_files)
    
    def load_image(self, file_path: Path) -> Optional[Image.Image]:
        """
        Load an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            PIL Image object or None if loading failed
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGBA for consistent processing
                return img.convert('RGBA')
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            return None
    
    def save_image(self, image: Image.Image, output_path: Path) -> bool:
        """
        Save an image to file.
        
        Args:
            image: PIL Image to save
            output_path: Path where to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with PNG format to preserve transparency
            image.save(output_path, 'PNG', optimize=True)
            logger.debug(f"Saved image to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save image to {output_path}: {e}")
            return False
    
    def generate_output_path(self, input_path: Path, output_folder: str, suffix: str = "_clean") -> Path:
        """
        Generate output path for processed image.
        
        Args:
            input_path: Original image path
            output_folder: Output folder path
            suffix: Suffix to add to filename
            
        Returns:
            Path object for the output file
        """
        # Get filename without extension
        base_name = input_path.stem
        
        # Add suffix and force PNG extension for transparency support
        output_name = f"{base_name}{suffix}.png"
        
        return Path(output_folder) / output_name
    
    def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists."""
        return file_path.exists()
    
    def get_file_info(self, file_path: Path) -> Tuple[str, int]:
        """
        Get basic file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (file_size_str, file_size_bytes)
        """
        if not file_path.exists():
            return "N/A", 0
        
        size_bytes = file_path.stat().st_size
        
        # Convert to human readable format
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        return size_str, size_bytes
    
    def create_backup(self, file_path: Path) -> bool:
        """
        Create a backup of the original file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            True if backup was created, False otherwise
        """
        try:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if not backup_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False
