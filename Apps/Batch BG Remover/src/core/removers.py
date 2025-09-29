"""
InSPyReNet Background Remover Implementation
SOLID: Single Responsibility, Open/Closed principle
KISS: Clean implementation without unnecessary complexity
"""

from typing import Dict, Any, Optional
from transparent_background import Remover
import logging

from .interfaces import BackgroundRemover, AdvancedBackgroundRemover, BackgroundRemovalError, load_image_from_bytes, image_to_bytes


class InspyrenetRemover(BackgroundRemover):
    """
    InSPyReNet implementation using transparent-background library.
    
    SOLID: Single Responsibility - only handles InSPyReNet processing
    KISS: Simple configuration and processing
    """
    
    def __init__(self, use_jit: bool = False, threshold: float = 0.5):
        self.use_jit = use_jit
        self.threshold = threshold
        self._remover: Optional[Remover] = None
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def _get_remover(self) -> Remover:
        """
        Lazy initialization of remover to avoid loading model until needed.
        
        Returns:
            Initialized Remover instance
        """
        if self._remover is None:
            try:
                self._logger.info("Initializing InSPyReNet remover...")
                self._remover = Remover(jit=self.use_jit)
                self._logger.info("InSPyReNet remover initialized successfully")
            except Exception as e:
                raise BackgroundRemovalError("Failed to initialize InSPyReNet", "InSPyReNet", e)
        
        return self._remover
    
    def remove_background(self, image_data: bytes) -> bytes:
        """
        Remove background using InSPyReNet algorithm.
        
        Args:
            image_data: Input image as bytes
            
        Returns:
            PNG image with transparent background
            
        Raises:
            BackgroundRemovalError: If processing fails
        """
        try:
            # Load input image
            img = load_image_from_bytes(image_data)
            
            # Process with InSPyReNet
            remover = self._get_remover()
            result = remover.process(img, type='rgba', threshold=self.threshold)
            
            # Convert to bytes
            return image_to_bytes(result, format='PNG')
            
        except BackgroundRemovalError:
            raise  # Re-raise our custom errors
        except Exception as e:
            raise BackgroundRemovalError("InSPyReNet processing failed", "InSPyReNet", e)
    
    def configure(self, **kwargs) -> bool:
        """
        Configure the InSPyReNet remover.
        
        Supported kwargs:
            - threshold: float (0.0 to 1.0)
            - use_jit: bool
            
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            True if configuration successful
        """
        try:
            if 'threshold' in kwargs:
                threshold = float(kwargs['threshold'])
                if 0.0 <= threshold <= 1.0:
                    self.threshold = threshold
                    self._logger.info(f"Updated threshold to {threshold}")
                else:
                    self._logger.warning(f"Invalid threshold {threshold}, keeping {self.threshold}")
                    return False
            
            if 'use_jit' in kwargs:
                new_jit = bool(kwargs['use_jit'])
                if new_jit != self.use_jit:
                    self.use_jit = new_jit
                    # Reset remover to apply new JIT setting
                    self._remover = None
                    self._logger.info(f"Updated JIT setting to {new_jit}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Configuration failed: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the InSPyReNet remover.
        
        Returns:
            Dictionary with remover information
        """
        return {
            "name": "InSPyReNet",
            "version": "1.3.4",  # transparent-background version
            "description": "Superior AI background removal using InSPyReNet algorithm",
            "type": "neural_network",
            "settings": {
                "threshold": self.threshold,
                "use_jit": self.use_jit,
            },
            "capabilities": [
                "high_quality_removal",
                "fine_details",
                "fur_and_hair",
                "configurable_threshold"
            ],
            "supported_formats": ["PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF"],
            "output_format": "PNG",
            "has_transparency": True
        }
    
    def is_available(self) -> bool:
        """
        Check if InSPyReNet is available.
        
        Returns:
            True if ready to use
        """
        try:
            # Try to get the remover (lazy init)
            self._get_remover()
            return True
        except Exception as e:
            self._logger.error(f"InSPyReNet not available: {e}")
            return False
    
    def cleanup(self):
        """Clean up InSPyReNet resources."""
        if self._remover is not None:
            try:
                # InSPyReNet doesn't need explicit cleanup, but we clear the reference
                self._remover = None
                self._logger.info("InSPyReNet resources cleaned up")
            except Exception as e:
                self._logger.warning(f"Cleanup warning: {e}")


class LayerDiffuseRemover(AdvancedBackgroundRemover):
    """
    LayerDiffuse-inspired background remover with real implementation.
    
    SOLID: Open/Closed - new removal method without modifying existing code
    KISS: Same interface as other removers, but with advanced capabilities
    """
    
    def __init__(self):
        from .layerdiffuse_remover import LayerDiffuseRemover as LayerDiffuseImpl
        self._impl = LayerDiffuseImpl()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("LayerDiffuse remover initialized with advanced capabilities")
    
    def remove_background(self, image_data: bytes) -> bytes:
        """LayerDiffuse background removal with enhancements."""
        return self._impl.remove_background(image_data)
    
    def remove_with_material_type(self, image_data: bytes, material_hint: str = "general") -> bytes:
        """Remove background with material-specific processing."""
        return self._impl.remove_with_material_type(image_data, material_hint)
    
    def get_supported_materials(self) -> list[str]:
        """Get list of supported material types."""
        return self._impl.get_supported_materials()
    
    def configure(self, **kwargs) -> bool:
        """Configure LayerDiffuse remover."""
        return self._impl.configure(**kwargs)
    
    def get_info(self) -> Dict[str, Any]:
        """Get LayerDiffuse information."""
        return self._impl.get_info()
    
    def is_available(self) -> bool:
        """LayerDiffuse is now available."""
        return self._impl.is_available()
    
    def cleanup(self):
        """Clean up LayerDiffuse resources."""
        self._impl.cleanup()