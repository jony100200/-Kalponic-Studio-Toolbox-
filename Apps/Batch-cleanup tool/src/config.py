"""
Configuration classes for batch image processing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class MattePreset(Enum):
    """Matte removal presets."""
    WHITE_MATTE = "White Matte"
    BLACK_MATTE = "Black Matte"
    AUTO = "Auto"

@dataclass
class ProcessingConfig:
    """Configuration for image processing parameters."""
    
    # Matte removal
    matte_preset: MattePreset = MattePreset.WHITE_MATTE
    
    # Alpha refinement
    smooth: int = 2  # 0-3
    feather: int = 1  # 0-3
    contrast: float = 3.0  # 1.0-4.0
    shift_edge: int = -1  # -2 to +2 pixels
    
    # Fringe fix
    fringe_fix_enabled: bool = True
    fringe_band: int = 2  # 1-3
    fringe_strength: int = 2  # 1-3
    
    # Output
    output_format: str = "PNG"
    add_suffix: str = "_clean"
    skip_existing: bool = True
    
    # Number of processing iterations
    process_iterations: int = 1  # Default to 1 iteration
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        return (
            0 <= self.smooth <= 3 and
            0 <= self.feather <= 3 and
            1.0 <= self.contrast <= 4.0 and
            -2 <= self.shift_edge <= 2 and
            1 <= self.fringe_band <= 3 and
            1 <= self.fringe_strength <= 3 and
            1 <= self.process_iterations <= 10  # Ensure iterations are within range
        )

@dataclass
class AppState:
    """Application state container."""
    input_folder: Optional[str] = None
    output_folder: Optional[str] = None
    processing_config: ProcessingConfig = None
    is_processing: bool = False
    processed_count: int = 0
    total_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        if self.processing_config is None:
            self.processing_config = ProcessingConfig()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processed_count = 0
        self.total_count = 0
        self.error_count = 0
