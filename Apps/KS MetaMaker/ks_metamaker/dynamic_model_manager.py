"""
🎯 Dynamic Model Manager for KS MetaMaker
=========================================
Manages AI model loading/unloading for optimal memory usage across different hardware profiles
"""

import gc
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    import torch
    import numpy as np
    from PIL import Image
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime not available, using CPU-only mode")


class ModelType(Enum):
    """Types of AI models"""
    TAGGING = "tagging"
    DETECTION = "detection"
    CAPTIONING = "captioning"


class MemoryProfile(Enum):
    """Memory management profiles"""
    LOW_VRAM = "low_vram"      # < 4GB - Load/unload per image
    MEDIUM_VRAM = "medium_vram"  # 4-8GB - Keep 2 models loaded
    HIGH_VRAM = "high_vram"    # >8GB - Keep all models loaded


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_type: ModelType
    model_path: Path
    session: Optional[Any] = None
    loaded_at: Optional[float] = None
    last_used: Optional[float] = None
    memory_usage_mb: int = 0
    input_shape: Tuple[int, ...] = None


@dataclass
class HardwareLimits:
    """Hardware memory limits"""
    total_vram_gb: float
    available_ram_gb: float
    max_models_loaded: int
    memory_profile: MemoryProfile


class DynamicModelManager:
    """
    Dynamic AI model manager with intelligent loading/unloading for memory optimization.

    Features:
    - Load models on-demand based on hardware capabilities
    - Automatic unloading of unused models
    - Memory usage tracking and optimization
    - Support for different hardware profiles
    """

    def __init__(self, models_dir: Path, hardware_detector=None):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Hardware detection
        self.hardware_limits = self._detect_hardware_limits(hardware_detector)

        # Model registry
        self.available_models: Dict[ModelType, List[Path]] = {}
        self.loaded_models: Dict[ModelType, ModelInfo] = {}

        # Memory management
        self.memory_lock = threading.Lock()
        self.max_memory_usage_mb = int(self.hardware_limits.total_vram_gb * 1024 * 0.8)  # 80% of VRAM

        # Model priorities (higher = more important to keep loaded)
        self.model_priorities = {
            ModelType.TAGGING: 3,      # Most frequently used
            ModelType.DETECTION: 2,    # Moderately used
            ModelType.CAPTIONING: 1    # Least frequently used
        }

        # Scan for available models
        self._scan_available_models()

        logger.info(f"DynamicModelManager initialized for {self.hardware_limits.memory_profile.value} profile")

    def _detect_hardware_limits(self, hardware_detector) -> HardwareLimits:
        """Detect hardware limits and determine memory profile"""
        if hardware_detector:
            summary = hardware_detector.get_hardware_summary()
            total_vram = 0
            if summary['gpus']:
                total_vram = summary['gpus'][0]['memory_gb']

            available_ram = summary['system']['available_ram_gb']
        else:
            # Fallback detection
            total_vram = 8.0  # Assume 8GB
            available_ram = 16.0  # Assume 16GB

        # Determine memory profile
        if total_vram <= 4:
            profile = MemoryProfile.LOW_VRAM
            max_models = 1
        elif total_vram <= 8:
            profile = MemoryProfile.MEDIUM_VRAM
            max_models = 2
        else:
            profile = MemoryProfile.HIGH_VRAM
            max_models = 3

        return HardwareLimits(
            total_vram_gb=total_vram,
            available_ram_gb=available_ram,
            max_models_loaded=max_models,
            memory_profile=profile
        )

    def _scan_available_models(self):
        """Scan models directory for available model files"""
        if not self.models_dir.exists():
            return

        # Model file patterns
        model_patterns = {
            ModelType.TAGGING: ["*clip*", "*siglip*", "*eva*", "*openclip*"],
            ModelType.DETECTION: ["*yolo*", "*yolov*"],
            ModelType.CAPTIONING: ["*blip*", "*florence*"]
        }

        for model_type, patterns in model_patterns.items():
            self.available_models[model_type] = []
            for pattern in patterns:
                matches = list(self.models_dir.glob(f"**/{pattern}"))
                matches.extend(list(self.models_dir.glob(f"**/{pattern}.onnx")))
                matches.extend(list(self.models_dir.glob(f"**/{pattern}.pt")))
                self.available_models[model_type].extend(matches)

            # Remove duplicates
            self.available_models[model_type] = list(set(self.available_models[model_type]))

        logger.info(f"Found models: Tagging={len(self.available_models[ModelType.TAGGING])}, "
                   f"Detection={len(self.available_models[ModelType.DETECTION])}, "
                   f"Captioning={len(self.available_models[ModelType.CAPTIONING])}")

    def get_model(self, model_type: ModelType) -> Optional[Any]:
        """
        Get a model session, loading it if necessary.
        Automatically manages memory by unloading less important models if needed.
        """
        with self.memory_lock:
            # Check if model is already loaded
            if model_type in self.loaded_models:
                model_info = self.loaded_models[model_type]
                model_info.last_used = time.time()
                return model_info.session

            # Model not loaded, try to load it
            return self._load_model(model_type)

    def _load_model(self, model_type: ModelType) -> Optional[Any]:
        """Load a model, managing memory constraints"""
        if not ONNX_AVAILABLE:
            logger.warning("ONNX Runtime not available, cannot load models")
            return None

        # Check if we have the model file
        if not self.available_models.get(model_type):
            logger.warning(f"No {model_type.value} model files found")
            return None

        model_path = self.available_models[model_type][0]  # Use first available

        # Check memory constraints
        if not self._can_load_model():
            # Try to free memory by unloading less important models
            if not self._free_memory_for_model(model_type):
                logger.warning(f"Cannot load {model_type.value} model: insufficient memory")
                return None

        try:
            # Load the model
            logger.info(f"Loading {model_type.value} model: {model_path.name}")

            if model_path.suffix.lower() == '.onnx':
                # ONNX model
                session = ort.InferenceSession(str(model_path))
            else:
                # PyTorch model (placeholder - would need torch loading)
                logger.warning(f"PyTorch models not yet supported: {model_path}")
                return None

            # Create model info
            model_info = ModelInfo(
                model_type=model_type,
                model_path=model_path,
                session=session,
                loaded_at=time.time(),
                last_used=time.time(),
                memory_usage_mb=self._estimate_model_memory(session)
            )

            self.loaded_models[model_type] = model_info

            logger.info(f"Successfully loaded {model_type.value} model "
                       f"({model_info.memory_usage_mb}MB)")

            return session

        except Exception as e:
            logger.error(f"Failed to load {model_type.value} model: {e}")
            return None

    def _can_load_model(self) -> bool:
        """Check if we can load another model within memory limits"""
        current_memory = sum(info.memory_usage_mb for info in self.loaded_models.values())

        # Check against max models limit
        if len(self.loaded_models) >= self.hardware_limits.max_models_loaded:
            return False

        # Check against memory limit (leave 20% buffer)
        return current_memory < (self.max_memory_usage_mb * 0.8)

    def _free_memory_for_model(self, needed_model_type: ModelType) -> bool:
        """Free memory by unloading less important models"""
        if not self.loaded_models:
            return True

        # Sort loaded models by priority (lower priority first) and last used time
        sorted_models = sorted(
            self.loaded_models.items(),
            key=lambda x: (self.model_priorities[x[0]], x[1].last_used or 0)
        )

        # Try to unload the least important model that's not the one we need
        for model_type, model_info in sorted_models:
            if model_type != needed_model_type:
                self._unload_model(model_type)
                logger.info(f"Unloaded {model_type.value} model to free memory")
                return True

        return False

    def _unload_model(self, model_type: ModelType):
        """Unload a model and free its memory"""
        if model_type in self.loaded_models:
            model_info = self.loaded_models[model_type]

            # Clear the session
            if model_info.session:
                del model_info.session

            # Remove from loaded models
            del self.loaded_models[model_type]

            # Force garbage collection
            gc.collect()

            logger.info(f"Unloaded {model_type.value} model")

    def _estimate_model_memory(self, session) -> int:
        """Estimate memory usage of a model session"""
        try:
            # Rough estimation based on session info
            # This is approximate and could be improved with actual profiling
            if hasattr(session, '_sess_options'):
                # ONNX Runtime session
                return 500  # Rough estimate: 500MB per model
            else:
                return 256  # Conservative estimate
        except:
            return 256  # Fallback estimate

    def preload_models(self, model_types: List[ModelType]):
        """Preload specific models (useful for high VRAM systems)"""
        for model_type in model_types:
            self.get_model(model_type)

    def unload_all_models(self):
        """Unload all models (useful for cleanup)"""
        with self.memory_lock:
            for model_type in list(self.loaded_models.keys()):
                self._unload_model(model_type)

    def get_memory_status(self) -> Dict:
        """Get current memory usage status"""
        with self.memory_lock:
            loaded_types = list(self.loaded_models.keys())
            total_memory = sum(info.memory_usage_mb for info in self.loaded_models.values())

            return {
                "loaded_models": [mt.value for mt in loaded_types],
                "memory_usage_mb": total_memory,
                "max_memory_mb": self.max_memory_usage_mb,
                "memory_profile": self.hardware_limits.memory_profile.value,
                "max_models_allowed": self.hardware_limits.max_models_loaded
            }

    def __del__(self):
        """Cleanup on destruction"""
        self.unload_all_models()