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
from .core import (
    HardwareProfiler,
    AppProfiler,
    TaskMapper,
    ScoringEngine,
    ModelFinder,
    SearchFilters,
    PipelineComposer,
    ModelDownloader,
    ConfigManager,
)
from .providers import ModelProvider, HuggingFaceProvider
from .data import ModelRegistry, PipelineConfig, HardwareInfo, AppProfile, ModelCandidate

__all__ = [
    "HardwareProfiler",
    "AppProfiler",
    "TaskMapper",
    "ScoringEngine",
    "ModelFinder",
    "SearchFilters",
    "PipelineComposer",
    "ModelDownloader",
    "ConfigManager",
    "ModelProvider",
    "HuggingFaceProvider",
    "ModelRegistry",
    "HardwareInfo",
    "AppProfile",
    "ModelCandidate",
    "PipelineConfig",
    "__version__",
]
