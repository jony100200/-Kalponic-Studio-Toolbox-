"""
🎯 System Manager - KISS Orchestrator
Role: "Team Captain" - Coordinates all the focused players
SOLID Principle: Dependency Inversion - Uses abstractions, not implementations
"""

from .hardware_detector import HardwareDetector, GPUInfo, SystemInfo
from .system_config import SystemConfig
from .port_allocator import PortAllocator  
from .service_discovery import ServiceDiscovery, DetectedService
from typing import Dict, List, Optional, Any


class SystemManager:
    """KISS orchestrator for all system components"""
    
    def __init__(self, config_dir: str = "config"):
        # Initialize all focused components
        self.hardware = HardwareDetector()
        self.config = SystemConfig(f"{config_dir}/system.json")
        self.ports = PortAllocator(f"{config_dir}/ports.json")
        self.discovery = ServiceDiscovery(f"{config_dir}/discovered_services.json")
        
        # System is now ready
        self._initialized = True
    
    @property
    def is_ready(self) -> bool:
        """Check if system manager is ready"""
        return self._initialized
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status from all components"""
        return {
            "system_info": self.hardware.system_info.__dict__ if self.hardware.system_info else {},
            "gpus": [gpu.__dict__ for gpu in self.hardware.gpus],
            "memory_limits": self.get_memory_limits(),
            "port_allocations": self.ports.get_all_allocations(),
            "detected_services": len(self.discovery.detected_services),
            "ai_services": len(self.discovery.get_ai_services()),
            "ready": self.is_ready
        }
    
    def get_best_gpu(self) -> Optional[GPUInfo]:
        """Get the best GPU for model loading"""
        if not self.hardware.gpus:
            return None
        
        # Prioritize by vendor preference and memory
        def gpu_score(gpu: GPUInfo) -> tuple:
            vendor_scores = {"nvidia": 1000, "amd": 500, "intel": 100, "cpu": 1}
            vendor_score = vendor_scores.get(gpu.vendor, 0)
            return (vendor_score, gpu.memory_gb)
        
        return max(self.hardware.gpus, key=gpu_score)
    
    def get_memory_limits(self) -> Dict[str, float]:
        """Get safe memory limits for model loading"""
        if not self.hardware.system_info:
            return {}
        
        best_gpu = self.get_best_gpu()
        gpu_memory = best_gpu.memory_gb if best_gpu else 0
        
        return self.config.get_memory_limits(
            self.hardware.system_info.total_ram_gb,
            gpu_memory
        )
    
    def can_load_model(self, model_size_gb: float, use_gpu: bool = True) -> Dict[str, Any]:
        """Check if a model can be loaded with current resources"""
        memory_limits = self.get_memory_limits()
        best_gpu = self.get_best_gpu()
        
        # Determine which memory to check
        if use_gpu and best_gpu and best_gpu.vendor != "cpu":
            available_memory = memory_limits.get("safe_vram_gb", 0)
            memory_type = "VRAM"
        else:
            available_memory = memory_limits.get("safe_ram_gb", 0)
            memory_type = "RAM"
        
        can_load = model_size_gb <= available_memory
        
        return {
            "can_load": can_load,
            "model_size_gb": model_size_gb,
            "available_memory_gb": available_memory,
            "memory_type": memory_type,
            "gpu_acceleration": use_gpu and best_gpu and best_gpu.vendor != "cpu",
            "recommendation": self._get_loading_recommendation(model_size_gb, available_memory, best_gpu)
        }
    
    def _get_loading_recommendation(self, model_size_gb: float, available_gb: float, gpu: Optional[GPUInfo]) -> str:
        """Get recommendation for model loading"""
        if model_size_gb <= available_gb:
            return "✅ Can load model safely"
        elif model_size_gb <= available_gb * 1.2:
            return "⚠️ Tight fit - monitor memory usage"
        elif gpu and gpu.vendor != "cpu":
            return "💡 Try CPU loading or smaller model"
        else:
            return "❌ Insufficient memory - use smaller model"
    
    def allocate_service_port(self, service_name: str, preferred_port: Optional[int] = None) -> int:
        """Allocate port for a service with conflict checking"""
        # Check for external service conflicts
        if preferred_port:
            existing_service = self.discovery.get_service_by_port(preferred_port)
            if existing_service:
                print(f"Warning: Port {preferred_port} already used by {existing_service.name}")
        
        return self.ports.allocate_port(service_name, preferred_port)
    
    def scan_for_conflicts(self) -> Dict[str, List[str]]:
        """Scan for service and port conflicts"""
        # Refresh service discovery
        self.discovery.scan_for_services()
        
        # Check port conflicts
        port_conflicts = self.ports.check_port_conflicts()
        
        # Check for services on allocated ports
        service_conflicts = []
        for service_name, port in self.ports.get_all_allocations().items():
            external_service = self.discovery.get_service_by_port(port)
            if external_service:
                service_conflicts.append(f"{service_name} conflicts with {external_service.name} on port {port}")
        
        return {
            "port_conflicts": port_conflicts,
            "service_conflicts": service_conflicts,
            "external_ai_services": [f"{s.name} on port {s.port}" for s in self.discovery.get_ai_services()]
        }
    
    def get_optimal_settings(self, model_size_gb: float) -> Dict[str, Any]:
        """Get optimal settings for loading a specific model"""
        best_gpu = self.get_best_gpu()
        memory_limits = self.get_memory_limits()
        
        # Calculate GPU layers if using GPU
        gpu_layers = 0
        context_size = self.config.model_defaults.max_context_size
        
        if best_gpu and best_gpu.vendor != "cpu":
            available_vram = memory_limits.get("safe_vram_gb", 0)
            if model_size_gb <= available_vram:
                gpu_layers = -1  # Full GPU
            elif model_size_gb * 0.8 <= available_vram:
                gpu_layers = 32
            elif model_size_gb * 0.6 <= available_vram:
                gpu_layers = 24
            elif model_size_gb * 0.4 <= available_vram:
                gpu_layers = 16
            elif model_size_gb * 0.2 <= available_vram:
                gpu_layers = 8
        
        # Adjust context size based on available memory
        if gpu_layers > 0:
            if best_gpu.memory_gb >= 16:
                context_size = 8192
            elif best_gpu.memory_gb >= 8:
                context_size = 4096
            else:
                context_size = 2048
        else:
            # CPU only
            if self.hardware.system_info.available_ram_gb >= 16:
                context_size = 4096
            else:
                context_size = 2048
        
        return {
            "gpu_layers": gpu_layers,
            "context_size": context_size,
            "threads": self.config.get_cpu_threads(self.hardware.system_info.cpu_cores),
            "use_mmap": self.config.model_defaults.enable_mmap,
            "backend_recommendation": self._recommend_backend(best_gpu),
            "memory_allocation": {
                "vram_gb": best_gpu.memory_gb if best_gpu else 0,
                "ram_gb": self.hardware.system_info.available_ram_gb,
                "model_size_gb": model_size_gb
            }
        }
    
    def _recommend_backend(self, gpu: Optional[GPUInfo]) -> str:
        """Recommend best backend for current hardware"""
        if not gpu or gpu.vendor == "cpu":
            return "llama.cpp (CPU)"
        elif gpu.vendor == "nvidia":
            return "llama.cpp (CUDA)"
        elif gpu.vendor == "amd":
            return "llama.cpp (ROCm/OpenCL)"
        else:
            return "llama.cpp (CPU fallback)"
    
    def shutdown(self) -> None:
        """Clean shutdown - save all configurations"""
        self.config.save_config()
        self.ports.save_allocations()
        self.discovery.save_cache()
    
    def get_complete_summary(self) -> Dict[str, Any]:
        """Get everything in one summary"""
        return {
            "hardware": self.hardware.get_hardware_summary(),
            "config": self.config.get_config_summary(),
            "ports": self.ports.get_port_summary(),
            "services": self.discovery.get_discovery_summary(),
            "system_status": self.get_system_status(),
            "conflicts": self.scan_for_conflicts()
        }
