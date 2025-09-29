"""
Core module initialization
"""

from .interfaces import BackgroundRemover, AdvancedBackgroundRemover, BackgroundRemovalError
from .removers import InspyrenetRemover, LayerDiffuseRemover
from .factory import RemoverFactory, RemoverManager, RemoverType
from .processor import ProcessingEngine, ProcessingStats

__all__ = [
    'BackgroundRemover',
    'AdvancedBackgroundRemover',
    'BackgroundRemovalError',
    'InspyrenetRemover',
    'LayerDiffuseRemover',
    'RemoverFactory',
    'RemoverManager',
    'RemoverType',
    'ProcessingEngine',
    'ProcessingStats',
]