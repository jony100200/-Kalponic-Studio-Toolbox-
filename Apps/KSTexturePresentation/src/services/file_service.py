"""
File Operations Service - Single Responsibility Principle  
Handles all file system operations
"""

import os
from pathlib import Path

class FileService:
    """Handles file system operations"""
    
    def __init__(self, supported_formats):
        """
        Initialize file service
        
        Args:
            supported_formats (list): List of supported file extensions
        """
        self.supported_formats = [fmt.lower() for fmt in supported_formats]
    
    def is_valid_image_file(self, file_path):
        """
        Check if file is a valid image format
        
        Args:
            file_path (str): Path to file
            
        Returns:
            bool: True if valid image file
        """
        if not os.path.exists(file_path):
            return False
            
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_formats
    
    def get_valid_images_in_directory(self, directory_path):
        """
        Get all valid image files in directory
        
        Args:
            directory_path (str): Directory to search
            
        Returns:
            list: List of valid image file paths
        """
        if not os.path.exists(directory_path):
            return []
            
        valid_images = []
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)
            if self.is_valid_image_file(file_path):
                valid_images.append(file_path)
                
        return sorted(valid_images)
    
    def ensure_output_directory(self, output_path):
        """
        Ensure output directory exists
        
        Args:
            output_path (str): Output file path
            
        Returns:
            bool: True if directory exists or was created
        """
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    def get_safe_output_path(self, output_path):
        """
        Get safe output path that doesn't overwrite existing files
        
        Args:
            output_path (str): Desired output path
            
        Returns:
            str: Safe output path
        """
        if not os.path.exists(output_path):
            return output_path
            
        # Add counter to filename
        path_obj = Path(output_path)
        counter = 1
        
        while True:
            new_path = path_obj.parent / f"{path_obj.stem}_{counter}{path_obj.suffix}"
            if not os.path.exists(new_path):
                return str(new_path)
            counter += 1
