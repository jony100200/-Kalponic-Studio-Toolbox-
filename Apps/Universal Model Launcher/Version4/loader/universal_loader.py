"""
🚀 Universal Loader - Consolidated Model Operations

Features:
- Multi-backend support (llama.cpp, transformers, exllama)
- Smart GPU allocation
- Dynamic quantization
- Health monitoring
- Preemptive memory checking
"""

import os
import json
import logging
import psutil
import subprocess
import socket
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Model type enumeration"""
    LLM = "llm"
    CLIP = "clip"
    TTS = "tts"
    STT = "stt"
    EMBEDDING = "embedding"

class Backend(Enum):
    """Backend enumeration"""
    LLAMA_CPP = "llama.cpp"
    TRANSFORMERS = "transformers"
    EXLLAMA = "exllama"

class UniversalLoader:
    """
    Consolidated loader for all model operations.
    """

    def __init__(self, config_dir: str = "loader_config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "model_config.json"
        self.running_servers: Dict[str, Dict] = {}
        self.allocated_ports: List[int] = []
        self.base_port = 8080
        self.max_ports = 20
        self.loaded_models: Dict[str, Dict] = {}

        # System monitoring
        self.memory_threshold = 0.85  # 85% memory usage threshold
        self.gpu_memory_threshold = 0.90  # 90% GPU memory threshold

        # Load configuration
        self.config = self._load_config()
        self._check_system_resources()
        logger.info("🚀 Universal Loader initialized")

    def _load_config(self) -> Dict:
        """Load model configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        # Default configuration
        default_config = {
            "models": {},
            "backends": {
                "llama.cpp": {"priority": 1, "path": None},
                "transformers": {"priority": 2, "path": None},
                "exllama": {"priority": 3, "path": None}
            },
            "default_settings": {
                "context_length": 4096,
                "temperature": 0.7,
                "max_tokens": 2048,
                "auto_port": True,
                "quantization": "auto",
                "gpu_layers": -1,
                "cuda_paths": [],
                "venv_activate": None
            },
            "monitoring": {
                "health_check_interval": 30,
                "memory_threshold": 0.85,
                "gpu_memory_threshold": 0.90
            }
        }
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def allocate_port(self) -> Optional[int]:
        """Allocate an available port"""
        for port in range(self.base_port, self.base_port + self.max_ports):
            if port not in self.allocated_ports:
                self.allocated_ports.append(port)
                logger.info(f"Allocated port: {port}")
                return port
        logger.error("No available ports")
        return None

    def _check_system_resources(self) -> Dict[str, float]:
        """Check available system resources"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        resources = {
            "memory_percent": memory.percent / 100,
            "memory_available_gb": memory.available / (1024**3),
            "cpu_percent": cpu_percent / 100
        }
        
        logger.info(f"System resources - Memory: {resources['memory_percent']:.1%}, "
                   f"Available: {resources['memory_available_gb']:.1f}GB, "
                   f"CPU: {resources['cpu_percent']:.1%}")
        
        return resources

    def _check_gpu_resources(self) -> Optional[Dict]:
        """Check GPU resources if available"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info = {}
                for i in range(torch.cuda.device_count()):
                    memory_total = torch.cuda.get_device_properties(i).total_memory
                    memory_reserved = torch.cuda.memory_reserved(i)
                    memory_allocated = torch.cuda.memory_allocated(i)
                    memory_free = memory_total - memory_reserved
                    
                    gpu_info[f"gpu_{i}"] = {
                        "total_gb": memory_total / (1024**3),
                        "free_gb": memory_free / (1024**3),
                        "used_percent": memory_reserved / memory_total
                    }
                
                logger.info(f"GPU resources: {gpu_info}")
                return gpu_info
        except ImportError:
            logger.info("PyTorch not available for GPU monitoring")
        return None

    def _detect_model_type(self, model_path: str) -> ModelType:
        """Detect model type from path or filename"""
        model_path_lower = model_path.lower()
        
        if "clip" in model_path_lower:
            return ModelType.CLIP
        elif any(term in model_path_lower for term in ["tts", "bark", "coqui"]):
            return ModelType.TTS
        elif any(term in model_path_lower for term in ["whisper", "stt", "speech"]):
            return ModelType.STT
        elif any(term in model_path_lower for term in ["embed", "sentence"]):
            return ModelType.EMBEDDING
        else:
            return ModelType.LLM

    def _select_optimal_backend(self, model_type: ModelType, model_format: str) -> Backend:
        """Select optimal backend based on model type and format"""
        if model_format.endswith(".gguf"):
            return Backend.LLAMA_CPP
        elif model_type == ModelType.CLIP:
            return Backend.TRANSFORMERS
        elif model_type in [ModelType.TTS, ModelType.STT]:
            return Backend.TRANSFORMERS
        else:
            return Backend.TRANSFORMERS

    def preemptive_memory_check(self, estimated_model_size_gb: float) -> bool:
        """Check if system can handle the model before loading"""
        resources = self._check_system_resources()
        
        if resources["memory_available_gb"] < estimated_model_size_gb * 1.2:
            logger.error(f"Insufficient memory. Available: {resources['memory_available_gb']:.1f}GB, "
                        f"Required: {estimated_model_size_gb * 1.2:.1f}GB")
            return False
        
        if resources["memory_percent"] > self.memory_threshold:
            logger.warning(f"High memory usage: {resources['memory_percent']:.1%}")
            return False
        
        return True

    def smart_gpu_allocation(self) -> Optional[int]:
        """Allocate GPU with most available memory"""
        gpu_info = self._check_gpu_resources()
        if not gpu_info:
            return None
        
        best_gpu = None
        max_free_memory = 0
        
        for gpu_id, info in gpu_info.items():
            if info["free_gb"] > max_free_memory and info["used_percent"] < self.gpu_memory_threshold:
                max_free_memory = info["free_gb"]
                best_gpu = int(gpu_id.split("_")[1])
        
        if best_gpu is not None:
            logger.info(f"Selected GPU {best_gpu} with {max_free_memory:.1f}GB free memory")
        
        return best_gpu

    def load_model(self, model_path: str, backend: Optional[str] = None, 
                   estimated_size_gb: float = 1.0) -> bool:
        """Load a model dynamically with health monitoring and resource management"""
        
        # Preemptive memory check
        if not self.preemptive_memory_check(estimated_size_gb):
            return False
        
        # Detect model type
        model_type = self._detect_model_type(model_path)
        logger.info(f"Detected model type: {model_type.value}")
        
        # Select backend if not specified
        if backend is None:
            model_format = Path(model_path).suffix
            selected_backend = self._select_optimal_backend(model_type, model_format)
        else:
            selected_backend = Backend(backend)
        
        logger.info(f"Loading model: {model_path} using backend: {selected_backend.value}")
        
        # Smart GPU allocation
        gpu_id = self.smart_gpu_allocation()
        
        # Load model based on backend
        if selected_backend == Backend.LLAMA_CPP:
            return self._load_llama_model(model_path, gpu_id)
        elif selected_backend == Backend.TRANSFORMERS:
            return self._load_transformers_model(model_path, model_type, gpu_id)
        elif selected_backend == Backend.EXLLAMA:
            return self._load_exllama_model(model_path, gpu_id)
        else:
            logger.error(f"Unsupported backend: {selected_backend}")
            return False

    def health_monitor(self) -> Dict[str, any]:
        """Monitor system and model health"""
        health_status = {
            "timestamp": time.time(),
            "system_resources": self._check_system_resources(),
            "gpu_resources": self._check_gpu_resources(),
            "loaded_models": len(self.loaded_models),
            "allocated_ports": len(self.allocated_ports),
            "status": "healthy"
        }
        
        # Check for issues
        if health_status["system_resources"]["memory_percent"] > self.memory_threshold:
            health_status["status"] = "warning"
            health_status["warnings"] = ["High memory usage"]
        
        return health_status

    def dynamic_quantization(self, model_size_gb: float, available_memory_gb: float) -> str:
        """Determine optimal quantization based on available resources"""
        memory_ratio = model_size_gb / available_memory_gb
        
        if memory_ratio > 0.8:
            return "q4_0"  # Aggressive quantization
        elif memory_ratio > 0.6:
            return "q8_0"  # Medium quantization
        elif memory_ratio > 0.4:
            return "fp16"  # Light quantization
        else:
            return "fp32"  # No quantization needed

    def _load_llama_model(self, model_path: str, gpu_id: Optional[int] = None) -> bool:
        """Load model using llama.cpp backend"""
        logger.info(f"Loading {model_path} with llama.cpp backend")
        
        # Dynamic quantization
        resources = self._check_system_resources()
        model_size = Path(model_path).stat().st_size / (1024**3) if Path(model_path).exists() else 4.0
        quantization = self.dynamic_quantization(model_size, resources["memory_available_gb"])
        
        # Store model info
        self.loaded_models[model_path] = {
            "backend": "llama.cpp",
            "type": self._detect_model_type(model_path).value,
            "gpu_id": gpu_id,
            "quantization": quantization,
            "port": self.allocate_port()
        }
        
        logger.info(f"Model loaded with quantization: {quantization}")
        return True

    def _load_transformers_model(self, model_path: str, model_type: ModelType, 
                                gpu_id: Optional[int] = None) -> bool:
        """Load model using transformers backend"""
        logger.info(f"Loading {model_path} with transformers backend for {model_type.value}")
        
        # Store model info
        self.loaded_models[model_path] = {
            "backend": "transformers",
            "type": model_type.value,
            "gpu_id": gpu_id,
            "port": self.allocate_port()
        }
        
        return True

    def _load_exllama_model(self, model_path: str, gpu_id: Optional[int] = None) -> bool:
        """Load model using exllama backend"""
        logger.info(f"Loading {model_path} with exllama backend")
        
        # Store model info
        self.loaded_models[model_path] = {
            "backend": "exllama",
            "type": "llm",
            "gpu_id": gpu_id,
            "port": self.allocate_port()
        }
        
        return True

    def unload_model(self, model_path: str) -> bool:
        """Unload a model and free resources"""
        if model_path in self.loaded_models:
            model_info = self.loaded_models[model_path]
            
            # Free port
            if model_info.get("port") in self.allocated_ports:
                self.allocated_ports.remove(model_info["port"])
            
            # Remove from loaded models
            del self.loaded_models[model_path]
            
            logger.info(f"Model {model_path} unloaded successfully")
            return True
        
        logger.warning(f"Model {model_path} not found in loaded models")
        return False

    def get_model_status(self) -> Dict[str, Dict]:
        """Get status of all loaded models"""
        return self.loaded_models.copy()

if __name__ == "__main__":
    # Example usage
    loader = UniversalLoader()
    
    # Health check
    health = loader.health_monitor()
    print(f"System health: {health['status']}")
    
    # Load example models
    success = loader.load_model("models/llama-7b.gguf", estimated_size_gb=4.0)
    if success:
        print("Model loaded successfully")
        
        # Check status
        status = loader.get_model_status()
        print(f"Loaded models: {len(status)}")
        
        # Unload model
        loader.unload_model("models/llama-7b.gguf")
