"""KS AutoModel - Independent ML Model Finder and Recommender

An independent, drop-in "model finder" that analyzes any app, detects what ML tasks
it needs, profiles the host machine, searches trusted hubs, then recommends and
(optionally) downloads the best + most optimized models for that hardware.

Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Kalponic Studio"
__email__ = "info@kalponic.com"

# Core functionality exports
from .core import HardwareProfiler, AppProfiler, TaskMapper, ScoringEngine
from .providers import ModelProvider, HuggingFaceProvider
from .data import ModelRegistry, PipelineConfig

__all__ = [
    "HardwareProfiler",
    "AppProfiler",
    "TaskMapper",
    "ScoringEngine",
    "ModelProvider",
    "HuggingFaceProvider",
    "ModelRegistry",
    "PipelineConfig",
    "__version__",
]