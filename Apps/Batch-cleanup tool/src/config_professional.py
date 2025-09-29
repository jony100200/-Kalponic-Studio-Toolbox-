"""
Enhanced configuration system for professional image processing.
Supports advanced features and material-specific settings.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

class MattePreset(Enum):
    """Matte removal presets."""
    WHITE_MATTE = "White Matte"
    BLACK_MATTE = "Black Matte"
    AUTO = "Auto"
    NONE = "None"

class ProcessorType(Enum):
    """Available processor types."""
    BASIC = "Basic"
    PROFESSIONAL = "Professional" 
    OPENCV = "OpenCV Enhanced"

class MaterialType(Enum):
    """Material type presets for specialized processing."""
    AUTO = "Auto Detect"
    STANDARD = "Standard"
    HAIR_FUR = "Hair/Fur"
    GLASS = "Glass/Transparent"
    COMPLEX = "Complex Edges"

@dataclass 
class ProfessionalConfig:
    """Advanced configuration for professional processing."""
    
    # Processor selection
    processor_type: ProcessorType = ProcessorType.PROFESSIONAL
    
    # Material-specific settings
    material_type: MaterialType = MaterialType.AUTO
    enable_material_detection: bool = True
    
    # Advanced edge processing
    edge_detection_method: str = "multi_scale"  # gradient, laplacian, multi_scale
    surgical_processing: bool = True  # Only process problematic areas
    preserve_fine_details: bool = True
    
    # Alpha pyramid settings
    use_alpha_pyramid: bool = True
    pyramid_levels: int = 4
    pyramid_blend_ratio: float = 0.7
    
    # Color analysis
    use_color_unmixing: bool = True
    contamination_threshold: float = 0.3
    color_variance_threshold: int = 80
    
    # Professional refinement
    use_bilateral_filtering: bool = True
    edge_preserving_smooth: bool = True
    legacy_contrast_mode: bool = True  # Mimics PS "Use Legacy Contrast"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'processor_type': self.processor_type.value,
            'material_type': self.material_type.value,
            'enable_material_detection': self.enable_material_detection,
            'edge_detection_method': self.edge_detection_method,
            'surgical_processing': self.surgical_processing,
            'preserve_fine_details': self.preserve_fine_details,
            'use_alpha_pyramid': self.use_alpha_pyramid,
            'pyramid_levels': self.pyramid_levels,
            'pyramid_blend_ratio': self.pyramid_blend_ratio,
            'use_color_unmixing': self.use_color_unmixing,
            'contamination_threshold': self.contamination_threshold,
            'color_variance_threshold': self.color_variance_threshold,
            'use_bilateral_filtering': self.use_bilateral_filtering,
            'edge_preserving_smooth': self.edge_preserving_smooth,
            'legacy_contrast_mode': self.legacy_contrast_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfessionalConfig':
        """Create from dictionary."""
        config = cls()
        
        if 'processor_type' in data:
            config.processor_type = ProcessorType(data['processor_type'])
        if 'material_type' in data:
            config.material_type = MaterialType(data['material_type'])
        
        # Update other fields
        for key, value in data.items():
            if hasattr(config, key) and key not in ['processor_type', 'material_type']:
                setattr(config, key, value)
                
        return config

@dataclass
class ProcessingConfig:
    """Enhanced configuration for image processing parameters."""
    
    # Matte removal
    matte_preset: MattePreset = MattePreset.WHITE_MATTE
    
    # Alpha refinement
    smooth: int = 2  # 0-5 (expanded range)
    feather: int = 1  # 0-5 (expanded range)
    contrast: float = 3.0  # 0.5-5.0 (expanded range)
    shift_edge: int = -1  # -5 to +5 pixels (expanded range)
    
    # Fringe fix
    fringe_fix_enabled: bool = True
    fringe_band: int = 2  # 1-5 (expanded range)
    fringe_strength: int = 2  # 1-5 (expanded range)
    
    # Professional settings
    professional: ProfessionalConfig = None
    
    # Output
    output_format: str = "PNG"
    add_suffix: str = "_professional"
    skip_existing: bool = True
    
    def __post_init__(self):
        """Initialize professional config if not provided."""
        if self.professional is None:
            self.professional = ProfessionalConfig()
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        return (
            0 <= self.smooth <= 5 and
            0 <= self.feather <= 5 and
            0.5 <= self.contrast <= 5.0 and
            -5 <= self.shift_edge <= 5 and
            1 <= self.fringe_band <= 5 and
            1 <= self.fringe_strength <= 5
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'matte_preset': self.matte_preset.value,
            'smooth': self.smooth,
            'feather': self.feather,
            'contrast': self.contrast,
            'shift_edge': self.shift_edge,
            'fringe_fix_enabled': self.fringe_fix_enabled,
            'fringe_band': self.fringe_band,
            'fringe_strength': self.fringe_strength,
            'professional': self.professional.to_dict() if self.professional else {},
            'output_format': self.output_format,
            'add_suffix': self.add_suffix,
            'skip_existing': self.skip_existing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create from dictionary."""
        # Handle matte preset
        matte_preset = MattePreset.WHITE_MATTE
        if 'matte_preset' in data:
            try:
                matte_preset = MattePreset(data['matte_preset'])
            except ValueError:
                matte_preset = MattePreset.WHITE_MATTE
        
        # Handle professional config
        professional = None
        if 'professional' in data and data['professional']:
            professional = ProfessionalConfig.from_dict(data['professional'])
        
        return cls(
            matte_preset=matte_preset,
            smooth=data.get('smooth', 2),
            feather=data.get('feather', 1),
            contrast=data.get('contrast', 3.0),
            shift_edge=data.get('shift_edge', -1),
            fringe_fix_enabled=data.get('fringe_fix_enabled', True),
            fringe_band=data.get('fringe_band', 2),
            fringe_strength=data.get('fringe_strength', 2),
            professional=professional,
            output_format=data.get('output_format', 'PNG'),
            add_suffix=data.get('add_suffix', '_professional'),
            skip_existing=data.get('skip_existing', True)
        )

@dataclass
class AppState:
    """Application state management."""
    
    input_folder: str = ""
    output_folder: str = ""
    processed_count: int = 0
    total_count: int = 0
    current_file: str = ""
    is_processing: bool = False
    last_error: str = ""
    
    def reset_progress(self):
        """Reset processing progress."""
        self.processed_count = 0
        self.total_count = 0
        self.current_file = ""
        self.is_processing = False
        self.last_error = ""

# Preset configurations for different use cases
class PresetConfigs:
    """Pre-defined configurations for common scenarios."""
    
    @staticmethod
    def photoshop_like() -> ProcessingConfig:
        """Configuration that closely mimics Photoshop's behavior."""
        config = ProcessingConfig(
            matte_preset=MattePreset.WHITE_MATTE,
            smooth=1,
            feather=1,
            contrast=3.5,
            shift_edge=-1,
            fringe_fix_enabled=True,
            fringe_band=2,
            fringe_strength=3,
            add_suffix="_ps_clean"
        )
        
        config.professional.surgical_processing = True
        config.professional.legacy_contrast_mode = True
        config.professional.use_color_unmixing = True
        
        return config
    
    @staticmethod
    def hair_fur_specialist() -> ProcessingConfig:
        """Optimized for hair and fur materials."""
        config = ProcessingConfig(
            matte_preset=MattePreset.AUTO,
            smooth=1,
            feather=0,
            contrast=2.5,
            shift_edge=0,
            fringe_fix_enabled=True,
            fringe_band=1,
            fringe_strength=2,
            add_suffix="_hair_clean"
        )
        
        config.professional.material_type = MaterialType.HAIR_FUR
        config.professional.preserve_fine_details = True
        config.professional.surgical_processing = True
        
        return config
    
    @staticmethod
    def glass_transparent() -> ProcessingConfig:
        """Optimized for glass and transparent materials."""
        config = ProcessingConfig(
            matte_preset=MattePreset.WHITE_MATTE,
            smooth=3,
            feather=2,
            contrast=2.0,
            shift_edge=0,
            fringe_fix_enabled=True,
            fringe_band=3,
            fringe_strength=1,
            add_suffix="_glass_clean"
        )
        
        config.professional.material_type = MaterialType.GLASS
        config.professional.use_alpha_pyramid = True
        config.professional.edge_preserving_smooth = True
        
        return config
    
    @staticmethod
    def maximum_quality() -> ProcessingConfig:
        """Maximum quality processing with all features enabled."""
        config = ProcessingConfig(
            matte_preset=MattePreset.AUTO,
            smooth=2,
            feather=2,
            contrast=3.0,
            shift_edge=-1,
            fringe_fix_enabled=True,
            fringe_band=3,
            fringe_strength=3,
            add_suffix="_pro_clean"
        )
        
        # Enable all professional features
        config.professional.enable_material_detection = True
        config.professional.surgical_processing = True
        config.professional.preserve_fine_details = True
        config.professional.use_alpha_pyramid = True
        config.professional.use_color_unmixing = True
        config.professional.use_bilateral_filtering = True
        config.professional.edge_preserving_smooth = True
        config.professional.legacy_contrast_mode = True
        
        return config