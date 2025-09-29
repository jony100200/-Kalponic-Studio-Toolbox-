"""
Remover Factory and Management
SOLID: Dependency Inversion, Single Responsibility
KISS: Simple factory pattern for remover creation
"""

from typing import Dict, Type, Optional, List
from enum import Enum
import logging

from .interfaces import BackgroundRemover
from .removers import InspyrenetRemover, LayerDiffuseRemover


class RemoverType(Enum):
    """Available background remover types."""
    INSPYRENET = "inspyrenet"
    LAYERDIFFUSE = "layerdiffuse"


class RemoverFactory:
    """
    Factory for creating background removal instances.
    
    SOLID: Single Responsibility - only creates removers
    KISS: Simple registration and creation pattern
    """
    
    _removers: Dict[RemoverType, Type[BackgroundRemover]] = {
        RemoverType.INSPYRENET: InspyrenetRemover,
        RemoverType.LAYERDIFFUSE: LayerDiffuseRemover,
    }
    
    @classmethod
    def create_remover(cls, remover_type: RemoverType, **kwargs) -> BackgroundRemover:
        """
        Create a background remover instance.
        
        Args:
            remover_type: Type of remover to create
            **kwargs: Arguments to pass to remover constructor
            
        Returns:
            Initialized remover instance
            
        Raises:
            ValueError: If remover type is not supported
        """
        if remover_type not in cls._removers:
            raise ValueError(f"Unsupported remover type: {remover_type}")
        
        remover_class = cls._removers[remover_type]
        return remover_class(**kwargs)
    
    @classmethod
    def get_available_types(cls) -> List[RemoverType]:
        """Get list of available remover types."""
        return list(cls._removers.keys())
    
    @classmethod
    def register_remover(cls, remover_type: RemoverType, remover_class: Type[BackgroundRemover]):
        """
        Register a new remover type.
        
        Args:
            remover_type: Enum value for the remover
            remover_class: Remover class to register
        """
        cls._removers[remover_type] = remover_class
        logging.info(f"Registered new remover type: {remover_type.value}")


class RemoverManager:
    """
    Manages multiple background removers with fallback support.
    
    SOLID: Single Responsibility - manages remover lifecycle
    KISS: Simple primary/fallback pattern
    """
    
    def __init__(self, primary_type: RemoverType = RemoverType.INSPYRENET):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.primary_type = primary_type
        self.fallback_type = RemoverType.INSPYRENET  # Always fallback to InSPyReNet
        
        self._primary_remover: Optional[BackgroundRemover] = None
        self._fallback_remover: Optional[BackgroundRemover] = None
        
        self._initialize_removers()
    
    def _initialize_removers(self):
        """Initialize the remover instances."""
        try:
            # Initialize primary remover
            self._primary_remover = RemoverFactory.create_remover(self.primary_type)
            self._logger.info(f"Primary remover initialized: {self.primary_type.value}")
            
            # Initialize fallback if different from primary
            if self.fallback_type != self.primary_type:
                self._fallback_remover = RemoverFactory.create_remover(self.fallback_type)
                self._logger.info(f"Fallback remover initialized: {self.fallback_type.value}")
                
        except Exception as e:
            self._logger.error(f"Failed to initialize removers: {e}")
            # Try to at least get the fallback working
            if self.primary_type != self.fallback_type:
                try:
                    self._fallback_remover = RemoverFactory.create_remover(self.fallback_type)
                    self._logger.info("Fallback remover ready")
                except Exception as e2:
                    self._logger.error(f"Even fallback failed: {e2}")
    
    def remove_background(self, image_data: bytes, prefer_primary: bool = True) -> bytes:
        """
        Remove background with automatic fallback.
        
        Args:
            image_data: Input image as bytes
            prefer_primary: Whether to try primary remover first
            
        Returns:
            Processed image with transparent background
            
        Raises:
            RuntimeError: If no removers are available
        """
        if prefer_primary and self._primary_remover and self._primary_remover.is_available():
            try:
                self._logger.debug(f"Using primary remover: {self.primary_type.value}")
                return self._primary_remover.remove_background(image_data)
            except Exception as e:
                self._logger.warning(f"Primary remover failed: {e}")
                # Fall through to fallback
        
        # Try fallback remover
        if self._fallback_remover and self._fallback_remover.is_available():
            try:
                self._logger.debug(f"Using fallback remover: {self.fallback_type.value}")
                return self._fallback_remover.remove_background(image_data)
            except Exception as e:
                self._logger.error(f"Fallback remover also failed: {e}")
                raise RuntimeError("All background removers failed") from e
        
        raise RuntimeError("No available background removers")
    
    def get_active_remover_info(self) -> Dict:
        """Get information about the currently active remover."""
        if self._primary_remover and self._primary_remover.is_available():
            info = self._primary_remover.get_info()
            info["status"] = "primary_active"
            return info
        elif self._fallback_remover and self._fallback_remover.is_available():
            info = self._fallback_remover.get_info()
            info["status"] = "fallback_active"
            return info
        else:
            return {
                "name": "None",
                "status": "no_removers_available",
                "error": "No background removers are currently available"
            }
    
    def switch_primary(self, new_primary: RemoverType, **kwargs):
        """
        Switch to a different primary remover.
        
        Args:
            new_primary: New primary remover type
            **kwargs: Arguments for the new remover
        """
        try:
            new_remover = RemoverFactory.create_remover(new_primary, **kwargs)
            
            # Clean up old primary
            if self._primary_remover:
                self._primary_remover.cleanup()
            
            self._primary_remover = new_remover
            self.primary_type = new_primary
            
            self._logger.info(f"Switched to primary remover: {new_primary.value}")
            
        except Exception as e:
            self._logger.error(f"Failed to switch primary remover: {e}")
            raise
    
    def configure_remover(self, remover_type: RemoverType, **kwargs) -> bool:
        """
        Configure a specific remover.
        
        Args:
            remover_type: Which remover to configure
            **kwargs: Configuration parameters
            
        Returns:
            True if configuration successful
        """
        target_remover = None
        
        if remover_type == self.primary_type and self._primary_remover:
            target_remover = self._primary_remover
        elif remover_type == self.fallback_type and self._fallback_remover:
            target_remover = self._fallback_remover
        
        if target_remover:
            return target_remover.configure(**kwargs)
        else:
            self._logger.warning(f"Cannot configure {remover_type.value}: not initialized")
            return False
    
    def cleanup(self):
        """Clean up all removers."""
        if self._primary_remover:
            try:
                self._primary_remover.cleanup()
            except Exception as e:
                self._logger.warning(f"Primary remover cleanup warning: {e}")
        
        if self._fallback_remover:
            try:
                self._fallback_remover.cleanup()
            except Exception as e:
                self._logger.warning(f"Fallback remover cleanup warning: {e}")
        
        self._logger.info("RemoverManager cleanup complete")