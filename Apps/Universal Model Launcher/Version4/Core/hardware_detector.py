"""
🔧 Hardware Detector - Pure Hardware Discovery
Role: "Hardware Scout" - Just detect what's available
SOLID Principle: Single Responsibility - Hardware detection only
"""

import platform
import subprocess
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """GPU hardware information"""
    name: str
    memory_gb: float
    vendor: str  # "nvidia", "amd", "intel", "cpu"
    is_available: bool
    driver_version: Optional[str] = None
    compute_capability: Optional[str] = None


@dataclass
class SystemInfo:
    """System hardware information"""
    platform: str
    cpu_cores: int
    total_ram_gb: float
    available_ram_gb: float
    python_version: str


class HardwareDetector:
    """Pure hardware detection - no configuration, no optimization"""
    
    def __init__(self):
        self.system_info: Optional[SystemInfo] = None
        self.gpus: List[GPUInfo] = []
        self._detect_system()
        self._detect_gpus()
    
    def _detect_system(self) -> None:
        """Detect basic system information"""
        memory = psutil.virtual_memory()
        self.system_info = SystemInfo(
            platform=f"{platform.system()} {platform.release()}",
            cpu_cores=psutil.cpu_count(),
            total_ram_gb=memory.total / (1024**3),
            available_ram_gb=memory.available / (1024**3),
            python_version=platform.python_version()
        )
    
    def _detect_gpus(self) -> None:
        """Detect all available GPUs"""
        self.gpus = []
        
        # NVIDIA GPUs
        nvidia_gpus = self._detect_nvidia()
        self.gpus.extend(nvidia_gpus)
        
        # AMD GPUs  
        amd_gpus = self._detect_amd()
        self.gpus.extend(amd_gpus)
        
        # Intel GPUs
        intel_gpus = self._detect_intel()
        self.gpus.extend(intel_gpus)
        
        # CPU fallback
        if not self.gpus:
            self.gpus.append(GPUInfo(
                name="CPU Fallback",
                memory_gb=self.system_info.available_ram_gb * 0.5,
                vendor="cpu",
                is_available=True
            ))
    
    def _detect_nvidia(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using nvidia-smi"""
        gpus = []
        try:
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=name,memory.total,driver_version,compute_cap',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpus.append(GPUInfo(
                                name=f"NVIDIA {parts[0]}",
                                memory_gb=float(parts[1]) / 1024,
                                vendor="nvidia",
                                is_available=True,
                                driver_version=parts[2] if parts[2] != '[N/A]' else None,
                                compute_capability=parts[3] if parts[3] != '[N/A]' else None
                            ))
        except Exception:
            pass
        return gpus
    
    def _detect_amd(self) -> List[GPUInfo]:
        """Detect AMD GPUs using rocm-smi"""
        gpus = []
        try:
            result = subprocess.run(['rocm-smi', '--showproductname'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'GPU' in result.stdout:
                gpus.append(GPUInfo(
                    name="AMD GPU (ROCm)",
                    memory_gb=8.0,  # Default assumption
                    vendor="amd",
                    is_available=True
                ))
        except Exception:
            pass
        return gpus
    
    def _detect_intel(self) -> List[GPUInfo]:
        """Detect Intel GPUs"""
        gpus = []
        if platform.system() == "Windows":
            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Intel' in line and 'Graphics' in line:
                            gpus.append(GPUInfo(
                                name=line.strip(),
                                memory_gb=4.0,  # Typical integrated GPU
                                vendor="intel",
                                is_available=True
                            ))
                            break
            except Exception:
                pass
        return gpus
    
    def get_hardware_summary(self) -> Dict:
        """Get complete hardware summary"""
        return {
            "system": {
                "platform": self.system_info.platform,
                "cpu_cores": self.system_info.cpu_cores,
                "total_ram_gb": round(self.system_info.total_ram_gb, 1),
                "available_ram_gb": round(self.system_info.available_ram_gb, 1),
                "python_version": self.system_info.python_version
            },
            "gpus": [
                {
                    "name": gpu.name,
                    "memory_gb": round(gpu.memory_gb, 1),
                    "vendor": gpu.vendor,
                    "available": gpu.is_available,
                    "driver": gpu.driver_version,
                    "compute": gpu.compute_capability
                }
                for gpu in self.gpus
            ]
        }
