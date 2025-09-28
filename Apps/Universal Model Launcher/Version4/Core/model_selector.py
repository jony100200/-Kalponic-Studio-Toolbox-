"""
🎯 Model Selector - Smart Model Size Selection
Role: "Model Matchmaker" - Match task + hardware to optimal model size
SOLID Principle: Single Responsibility - Model selection logic only
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .input_router import TaskType
from .hardware_detector import HardwareDetector, GPUInfo, SystemInfo

logger = logging.getLogger(__name__)


class ModelSize(Enum):
    """Model size categories"""
    TINY = "tiny"      # <1B parameters
    SMALL = "small"    # 1-3B parameters  
    MEDIUM = "medium"  # 3-7B parameters
    LARGE = "large"    # 7-13B parameters
    XLARGE = "xlarge"  # 13B+ parameters


class ModelCapability(Enum):
    """Model capability levels"""
    BASIC = "basic"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class ModelTier:
    """Model tier definition with hardware requirements"""
    size: ModelSize
    min_vram_gb: float
    min_ram_gb: float
    parameter_range: str
    typical_speed: str
    capability: ModelCapability
    recommended_tasks: List[TaskType]


@dataclass
class ModelRecommendation:
    """Model selection recommendation"""
    recommended_size: ModelSize
    confidence: float
    reasoning: str
    hardware_utilization: Dict[str, float]
    fallback_options: List[ModelSize]
    performance_estimate: Dict[str, str]


class ModelSelector:
    """
    Smart model size selection based on task type and hardware capabilities.
    
    Analyzes available hardware resources and task requirements to recommend
    the optimal model size for best performance/quality balance.
    """
    
    def __init__(self, hardware_detector: Optional[HardwareDetector] = None):
        self.hardware = hardware_detector or HardwareDetector()
        self._model_tiers = self._define_model_tiers()
        self._task_requirements = self._define_task_requirements()
    
    def _define_model_tiers(self) -> Dict[ModelSize, ModelTier]:
        """Define model tiers with hardware requirements"""
        return {
            ModelSize.TINY: ModelTier(
                size=ModelSize.TINY,
                min_vram_gb=0.5,
                min_ram_gb=2.0,
                parameter_range="0.1B - 1B",
                typical_speed="50-100 tok/s",
                capability=ModelCapability.BASIC,
                recommended_tasks=[TaskType.TEXT, TaskType.CODE]
            ),
            ModelSize.SMALL: ModelTier(
                size=ModelSize.SMALL,
                min_vram_gb=2.0,
                min_ram_gb=4.0,
                parameter_range="1B - 3B",
                typical_speed="30-60 tok/s",
                capability=ModelCapability.GOOD,
                recommended_tasks=[TaskType.TEXT, TaskType.CODE, TaskType.PDF]
            ),
            ModelSize.MEDIUM: ModelTier(
                size=ModelSize.MEDIUM,
                min_vram_gb=4.0,
                min_ram_gb=8.0,
                parameter_range="3B - 7B",
                typical_speed="20-40 tok/s",
                capability=ModelCapability.GOOD,
                recommended_tasks=[TaskType.TEXT, TaskType.CODE, TaskType.PDF, TaskType.IMAGE]
            ),
            ModelSize.LARGE: ModelTier(
                size=ModelSize.LARGE,
                min_vram_gb=8.0,
                min_ram_gb=16.0,
                parameter_range="7B - 13B",
                typical_speed="10-25 tok/s",
                capability=ModelCapability.EXCELLENT,
                recommended_tasks=[TaskType.TEXT, TaskType.CODE, TaskType.PDF, TaskType.IMAGE]
            ),
            ModelSize.XLARGE: ModelTier(
                size=ModelSize.XLARGE,
                min_vram_gb=16.0,
                min_ram_gb=32.0,
                parameter_range="13B+",
                typical_speed="5-15 tok/s",
                capability=ModelCapability.EXCELLENT,
                recommended_tasks=[TaskType.TEXT, TaskType.CODE, TaskType.PDF, TaskType.IMAGE]
            )
        }
    
    def _define_task_requirements(self) -> Dict[TaskType, Dict]:
        """Define minimum model requirements for each task type"""
        return {
            TaskType.TEXT: {
                'min_size': ModelSize.TINY,
                'preferred_size': ModelSize.MEDIUM,
                'quality_priority': 0.7
            },
            TaskType.CODE: {
                'min_size': ModelSize.SMALL,
                'preferred_size': ModelSize.MEDIUM,
                'quality_priority': 0.8
            },
            TaskType.PDF: {
                'min_size': ModelSize.SMALL,
                'preferred_size': ModelSize.LARGE,
                'quality_priority': 0.8
            },
            TaskType.IMAGE: {
                'min_size': ModelSize.MEDIUM,
                'preferred_size': ModelSize.LARGE,
                'quality_priority': 0.9
            },
            TaskType.AUDIO: {
                'min_size': ModelSize.TINY,  # Whisper models are separate
                'preferred_size': ModelSize.SMALL,
                'quality_priority': 0.6
            }
        }
    
    def select_model_size(self, task_type: TaskType, quality_preference: float = 0.7) -> ModelRecommendation:
        """
        Select optimal model size for given task and hardware.
        
        Args:
            task_type: Type of task to perform
            quality_preference: 0.0 (speed) to 1.0 (quality)
            
        Returns:
            ModelRecommendation with size and reasoning
        """
        available_vram = self._get_available_vram()
        available_ram = self._get_available_ram()
        
        # Get task requirements
        task_req = self._task_requirements.get(task_type, self._task_requirements[TaskType.TEXT])
        
        # Find compatible model sizes
        compatible_sizes = []
        for size, tier in self._model_tiers.items():
            if (available_vram >= tier.min_vram_gb and 
                available_ram >= tier.min_ram_gb and
                task_type in tier.recommended_tasks):
                compatible_sizes.append(size)
        
        if not compatible_sizes:
            # Fall back to CPU-only recommendations
            return self._cpu_fallback_recommendation(task_type, available_ram)
        
        # Select based on quality preference
        if quality_preference >= 0.8:
            # Prefer largest compatible model
            recommended = max(compatible_sizes, key=lambda x: self._model_tiers[x].min_vram_gb)
        elif quality_preference <= 0.3:
            # Prefer smallest compatible model for speed
            recommended = min(compatible_sizes, key=lambda x: self._model_tiers[x].min_vram_gb)
        else:
            # Balanced choice - prefer task's preferred size if available
            preferred = task_req['preferred_size']
            if preferred in compatible_sizes:
                recommended = preferred
            else:
                # Choose closest to preferred
                recommended = min(compatible_sizes, 
                                key=lambda x: abs(list(ModelSize).index(x) - list(ModelSize).index(preferred)))
        
        # Calculate hardware utilization
        recommended_tier = self._model_tiers[recommended]
        hardware_util = {
            'vram_usage': recommended_tier.min_vram_gb / available_vram,
            'ram_usage': recommended_tier.min_ram_gb / available_ram,
            'gpu_available': available_vram > 2.0
        }
        
        # Generate fallback options
        fallbacks = [size for size in compatible_sizes if size != recommended]
        fallbacks.sort(key=lambda x: self._model_tiers[x].min_vram_gb, reverse=True)
        
        # Performance estimates
        performance = {
            'speed': recommended_tier.typical_speed,
            'quality': recommended_tier.capability.value,
            'memory_efficient': hardware_util['vram_usage'] < 0.8
        }
        
        confidence = self._calculate_confidence(recommended, task_type, hardware_util)
        reasoning = self._generate_reasoning(recommended, task_type, hardware_util, quality_preference)
        
        return ModelRecommendation(
            recommended_size=recommended,
            confidence=confidence,
            reasoning=reasoning,
            hardware_utilization=hardware_util,
            fallback_options=fallbacks[:2],  # Top 2 fallbacks
            performance_estimate=performance
        )
    
    def _get_available_vram(self) -> float:
        """Get available GPU VRAM in GB"""
        if not self.hardware.gpus:
            return 0.0
        
        # Return largest GPU memory (primary GPU)
        return max(gpu.memory_gb for gpu in self.hardware.gpus if gpu.is_available)
    
    def _get_available_ram(self) -> float:
        """Get available system RAM in GB"""
        if not self.hardware.system_info:
            return 8.0  # Conservative fallback
        
        return self.hardware.system_info.available_ram_gb
    
    def _cpu_fallback_recommendation(self, task_type: TaskType, available_ram: float) -> ModelRecommendation:
        """Provide CPU-only fallback recommendation"""
        # For CPU-only, recommend based on available RAM
        if available_ram >= 16.0:
            recommended = ModelSize.MEDIUM
        elif available_ram >= 8.0:
            recommended = ModelSize.SMALL
        else:
            recommended = ModelSize.TINY
        
        return ModelRecommendation(
            recommended_size=recommended,
            confidence=0.6,
            reasoning=f"CPU-only fallback for {task_type.value} task with {available_ram:.1f}GB RAM",
            hardware_utilization={'vram_usage': 0.0, 'ram_usage': 0.5, 'gpu_available': False},
            fallback_options=[ModelSize.TINY],
            performance_estimate={'speed': 'slow', 'quality': 'basic', 'memory_efficient': True}
        )
    
    def _calculate_confidence(self, recommended: ModelSize, task_type: TaskType, hardware_util: Dict) -> float:
        """Calculate confidence score for recommendation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if well within hardware limits
        if hardware_util['vram_usage'] < 0.7:
            confidence += 0.2
        
        # Higher confidence if task matches model capabilities
        tier = self._model_tiers[recommended]
        if task_type in tier.recommended_tasks:
            confidence += 0.2
        
        # Lower confidence if pushing hardware limits
        if hardware_util['vram_usage'] > 0.9:
            confidence -= 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def _generate_reasoning(self, recommended: ModelSize, task_type: TaskType, 
                          hardware_util: Dict, quality_pref: float) -> str:
        """Generate human-readable reasoning for recommendation"""
        tier = self._model_tiers[recommended]
        vram = self._get_available_vram()
        
        if not hardware_util['gpu_available']:
            return f"Recommended {recommended.value} model for CPU-only inference on {task_type.value} task"
        
        quality_desc = "high quality" if quality_pref >= 0.7 else "balanced" if quality_pref >= 0.4 else "fast"
        
        return (f"Recommended {recommended.value} model ({tier.parameter_range}) for {task_type.value} task. "
                f"With {vram:.1f}GB VRAM, expect {tier.typical_speed} for {quality_desc} results.")
    
    def get_model_requirements(self, model_size: ModelSize) -> ModelTier:
        """Get hardware requirements for specific model size"""
        return self._model_tiers[model_size]
    
    def estimate_performance(self, model_size: ModelSize, task_type: TaskType) -> Dict[str, str]:
        """Estimate performance for model size and task combination"""
        tier = self._model_tiers[model_size]
        vram_available = self._get_available_vram()
        
        # Adjust speed estimates based on available hardware
        if vram_available >= tier.min_vram_gb * 1.5:
            speed_modifier = "fast"
        elif vram_available >= tier.min_vram_gb:
            speed_modifier = "normal"
        else:
            speed_modifier = "slow"
        
        return {
            'speed': f"{tier.typical_speed} ({speed_modifier})",
            'quality': tier.capability.value,
            'suitability': "excellent" if task_type in tier.recommended_tasks else "limited"
        }
