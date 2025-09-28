"""
🔧 Model Optimizer - Performance Tuning

Features:
- Context length optimization
- Quantization selection
- GPU layer calculation
- Performance profiling
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class QuantizationType(Enum):
    """Quantization type enumeration"""
    FP32 = "fp32"
    FP16 = "fp16"
    Q8_0 = "q8_0"
    Q6_K = "q6_k"
    Q4_K_M = "q4_k_m"
    Q4_0 = "q4_0"

class ModelOptimizer:
    """
    Model-specific optimization and configuration handler.
    """

    def __init__(self):
        self.optimization_cache: Dict[str, Dict] = {}
        logger.info("🔧 Model Optimizer initialized")

    def optimize_context_length(self, model_path: str, available_memory_gb: float) -> int:
        """Calculate optimal context length based on model and memory"""
        model_size_gb = self._estimate_model_size(model_path)
        
        # Base context calculations
        if model_size_gb <= 1.0:
            base_context = 8192
        elif model_size_gb <= 4.0:
            base_context = 4096
        elif model_size_gb <= 8.0:
            base_context = 2048
        else:
            base_context = 1024

        # Adjust based on available memory
        memory_ratio = available_memory_gb / model_size_gb
        if memory_ratio > 4.0:
            context_multiplier = 2.0
        elif memory_ratio > 2.0:
            context_multiplier = 1.5
        else:
            context_multiplier = 0.8

        optimal_context = int(base_context * context_multiplier)
        
        # Ensure power of 2 for efficiency
        optimal_context = self._round_to_power_of_2(optimal_context)
        
        logger.info(f"Optimal context length: {optimal_context} (model: {model_size_gb:.1f}GB, memory: {available_memory_gb:.1f}GB)")
        return optimal_context

    def select_quantization(self, model_size_gb: float, available_memory_gb: float,
                          target_performance: str = "balanced") -> QuantizationType:
        """Select optimal quantization based on constraints"""
        memory_pressure = model_size_gb / available_memory_gb

        if target_performance == "speed":
            if memory_pressure > 0.8:
                return QuantizationType.Q4_0
            elif memory_pressure > 0.6:
                return QuantizationType.Q6_K
            else:
                return QuantizationType.FP16

        elif target_performance == "quality":
            if memory_pressure > 0.9:
                return QuantizationType.Q8_0
            elif memory_pressure > 0.7:
                return QuantizationType.Q6_K
            else:
                return QuantizationType.FP16

        else:  # balanced
            if memory_pressure > 0.8:
                return QuantizationType.Q4_K_M
            elif memory_pressure > 0.6:
                return QuantizationType.Q6_K
            elif memory_pressure > 0.4:
                return QuantizationType.Q8_0
            else:
                return QuantizationType.FP16

    def calculate_gpu_layers(self, model_path: str, gpu_memory_gb: float) -> int:
        """Calculate optimal number of GPU layers"""
        model_size_gb = self._estimate_model_size(model_path)
        
        # Estimate layers based on model architecture
        total_layers = self._estimate_layer_count(model_path)
        
        # Calculate how many layers fit in GPU memory (with safety margin)
        usable_gpu_memory = gpu_memory_gb * 0.8  # 80% safety margin
        layers_per_gb = total_layers / model_size_gb
        max_gpu_layers = int(usable_gpu_memory * layers_per_gb)
        
        # Ensure we don't exceed total layers
        optimal_layers = min(max_gpu_layers, total_layers)
        
        logger.info(f"GPU layers: {optimal_layers}/{total_layers} (GPU memory: {gpu_memory_gb:.1f}GB)")
        return optimal_layers

    def create_optimization_profile(self, model_path: str, available_memory_gb: float,
                                  gpu_memory_gb: Optional[float] = None) -> Dict:
        """Create comprehensive optimization profile for a model"""
        model_name = Path(model_path).stem
        
        profile = {
            "model_path": model_path,
            "model_size_gb": self._estimate_model_size(model_path),
            "context_length": self.optimize_context_length(model_path, available_memory_gb),
            "quantization": self.select_quantization(
                self._estimate_model_size(model_path), 
                available_memory_gb
            ).value,
            "cpu_threads": self._calculate_cpu_threads(),
            "batch_size": self._calculate_batch_size(available_memory_gb)
        }

        # Add GPU-specific optimizations if GPU is available
        if gpu_memory_gb:
            profile.update({
                "gpu_layers": self.calculate_gpu_layers(model_path, gpu_memory_gb),
                "gpu_memory_gb": gpu_memory_gb,
                "use_gpu": True
            })
        else:
            profile["use_gpu"] = False

        # Cache the optimization
        self.optimization_cache[model_name] = profile
        
        logger.info(f"Created optimization profile for {model_name}")
        return profile

    def get_cached_optimization(self, model_path: str) -> Optional[Dict]:
        """Get cached optimization profile"""
        model_name = Path(model_path).stem
        return self.optimization_cache.get(model_name)

    def _estimate_model_size(self, model_path: str) -> float:
        """Estimate model size in GB"""
        if os.path.exists(model_path):
            size_bytes = os.path.getsize(model_path)
            return size_bytes / (1024**3)
        else:
            # Estimate based on filename patterns
            path_lower = model_path.lower()
            if "7b" in path_lower:
                return 4.0
            elif "13b" in path_lower:
                return 8.0
            elif "70b" in path_lower:
                return 40.0
            else:
                return 2.0  # Default estimate

    def _estimate_layer_count(self, model_path: str) -> int:
        """Estimate number of layers based on model"""
        path_lower = model_path.lower()
        
        if "7b" in path_lower:
            return 32
        elif "13b" in path_lower:
            return 40
        elif "70b" in path_lower:
            return 80
        elif "mixtral" in path_lower:
            return 32
        elif "qwen" in path_lower:
            return 28
        else:
            return 24  # Default estimate

    def _calculate_cpu_threads(self) -> int:
        """Calculate optimal CPU thread count"""
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        
        # Use 3/4 of available cores, minimum 1, maximum 16
        optimal_threads = max(1, min(16, int(cpu_count * 0.75)))
        
        return optimal_threads

    def _calculate_batch_size(self, available_memory_gb: float) -> int:
        """Calculate optimal batch size"""
        if available_memory_gb > 16:
            return 32
        elif available_memory_gb > 8:
            return 16
        elif available_memory_gb > 4:
            return 8
        else:
            return 1

    def _round_to_power_of_2(self, value: int) -> int:
        """Round value to nearest power of 2"""
        import math
        return 2 ** round(math.log2(value))

if __name__ == "__main__":
    # Example usage
    optimizer = ModelOptimizer()
    
    # Test optimization
    profile = optimizer.create_optimization_profile(
        "models/llama-7b.gguf", 
        available_memory_gb=16.0, 
        gpu_memory_gb=8.0
    )
    
    print(f"Optimization profile: {json.dumps(profile, indent=2)}")
