"""
Background Removal Interfaces
SOLID: Interface Segregation and Dependency Inversion
KISS: Simple, consistent interface for all removal methods
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from PIL import Image
import io


class BackgroundRemover(ABC):
    """
    Abstract base class for background removal algorithms.
    
    SOLID: Interface Segregation - minimal, focused interface
    KISS: Simple method signatures, consistent behavior
    """
    
    @abstractmethod
    def remove_background(self, image_data: bytes) -> bytes:
        """
        Remove background from image data and return processed PNG bytes.
        
        Args:
            image_data: Input image as bytes
            
        Returns:
            PNG image data with transparent background
            
        Raises:
            BackgroundRemovalError: If processing fails
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> bool:
        """
        Configure the remover with new settings.
        
        Args:
            **kwargs: Algorithm-specific settings
            
        Returns:
            True if configuration successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the remover.
        
        Returns:
            Dictionary with remover info (name, version, settings, etc.)
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the remover is available and functional.
        
        Returns:
            True if ready to use, False otherwise
        """
        return True
    
    def cleanup(self):
        """Clean up resources if needed."""
        pass


class AdvancedBackgroundRemover(BackgroundRemover):
    """
    Extended interface for advanced removal methods (like LayerDiffuse).
    
    SOLID: Interface Segregation - advanced features separate from basic
    """
    
    @abstractmethod
    def remove_with_material_type(self, image_data: bytes, material_hint: str = "general") -> bytes:
        """
        Remove background with material-specific processing.
        
        Args:
            image_data: Input image as bytes
            material_hint: Type of material ("glass", "transparent", "solid", "general")
            
        Returns:
            PNG image data with advanced transparency handling
        """
        pass
    
    @abstractmethod
    def get_supported_materials(self) -> list[str]:
        """Get list of supported material types."""
        pass


class BackgroundRemovalError(Exception):
    """Custom exception for background removal errors."""
    
    def __init__(self, message: str, remover_type: str = "unknown", original_error: Optional[Exception] = None):
        super().__init__(message)
        self.remover_type = remover_type
        self.original_error = original_error
    
    def __str__(self):
        base_msg = f"[{self.remover_type}] {super().__str__()}"
        if self.original_error:
            base_msg += f" (caused by: {self.original_error})"
        return base_msg


def load_image_from_bytes(image_data: bytes) -> Image.Image:
    """
    Utility function to load PIL Image from bytes.
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        PIL Image object
        
    Raises:
        BackgroundRemovalError: If image loading fails
    """
    try:
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise BackgroundRemovalError("Failed to load image from bytes", "utility", e)


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Utility function to convert PIL Image to bytes.
    
    Args:
        image: PIL Image object
        format: Output format (PNG, JPEG, etc.)
        
    Returns:
        Image data as bytes
        
    Raises:
        BackgroundRemovalError: If conversion fails
    """
    try:
        output = io.BytesIO()
        image.save(output, format=format)
        return output.getvalue()
    except Exception as e:
        raise BackgroundRemovalError(f"Failed to convert image to {format}", "utility", e)