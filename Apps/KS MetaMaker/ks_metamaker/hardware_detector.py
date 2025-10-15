"""
🔧 Hardware Detector for KS MetaMaker
=====================================
Detects system hardware capabilities for optimal AI model selection
"""

import platform
import subprocess
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


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
    cpu_name: str
    cpu_cores: int
    total_ram_gb: float
    available_ram_gb: float
    python_version: str


class HardwareDetector:
    """Hardware detection for KS MetaMaker AI model optimization"""

    def __init__(self):
        self.system_info: Optional[SystemInfo] = None
        self.gpus: List[GPUInfo] = []
        self._detect_system()
        self._detect_gpus()

    def _detect_system(self) -> None:
        """Detect basic system information"""
        memory = psutil.virtual_memory()

        # Get CPU name
        cpu_name = "Unknown CPU"
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'name'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    if len(lines) > 1:
                        cpu_name = lines[1]
            elif platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            cpu_name = line.split(':')[1].strip()
                            break
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    cpu_name = result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not detect CPU name: {e}")

        self.system_info = SystemInfo(
            platform=f"{platform.system()} {platform.release()}",
            cpu_name=cpu_name,
            cpu_cores=psutil.cpu_count(logical=True),  # Include hyperthreading
            total_ram_gb=round(memory.total / (1024**3), 1),
            available_ram_gb=round(memory.available / (1024**3), 1),
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

        # CPU fallback if no GPU detected
        if not self.gpus:
            self.gpus.append(GPUInfo(
                name="CPU Only",
                memory_gb=0.0,  # No VRAM
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
                                memory_gb=round(float(parts[1]) / 1024, 1),
                                vendor="nvidia",
                                is_available=True,
                                driver_version=parts[2] if parts[2] != '[N/A]' else None,
                                compute_capability=parts[3] if parts[3] != '[N/A]' else None
                            ))
        except Exception as e:
            logger.debug(f"NVIDIA GPU detection failed: {e}")
        return gpus

    def _detect_amd(self) -> List[GPUInfo]:
        """Detect AMD GPUs using rocm-smi"""
        gpus = []
        try:
            result = subprocess.run(['rocm-smi', '--showproductname'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'GPU' in result.stdout:
                # Try to get memory info
                memory_gb = 8.0  # Default assumption
                try:
                    mem_result = subprocess.run(['rocm-smi', '--showmeminfo'],
                                               capture_output=True, text=True, timeout=5)
                    if mem_result.returncode == 0:
                        # Parse memory info - this is approximate
                        memory_gb = 8.0  # Could be improved with better parsing
                except:
                    pass

                gpus.append(GPUInfo(
                    name="AMD GPU (ROCm)",
                    memory_gb=memory_gb,
                    vendor="amd",
                    is_available=True
                ))
        except Exception as e:
            logger.debug(f"AMD GPU detection failed: {e}")
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
                        line = line.strip()
                        if 'Intel' in line and ('Graphics' in line or 'UHD' in line or 'Iris' in line):
                            # Estimate VRAM for common Intel GPUs
                            memory_gb = 4.0  # Typical integrated GPU
                            if 'Iris' in line or 'Xe' in line:
                                memory_gb = 8.0  # Newer integrated GPUs
                            gpus.append(GPUInfo(
                                name=line,
                                memory_gb=memory_gb,
                                vendor="intel",
                                is_available=True
                            ))
                            break
            except Exception as e:
                logger.debug(f"Intel GPU detection failed: {e}")
        return gpus

    def get_primary_gpu(self) -> Optional[GPUInfo]:
        """Get the primary GPU (first available GPU)"""
        available_gpus = [gpu for gpu in self.gpus if gpu.is_available]
        return available_gpus[0] if available_gpus else None

    def get_hardware_summary(self) -> Dict:
        """Get complete hardware summary"""
        return {
            "system": {
                "platform": self.system_info.platform,
                "cpu_name": self.system_info.cpu_name,
                "cpu_cores": self.system_info.cpu_cores,
                "total_ram_gb": self.system_info.total_ram_gb,
                "available_ram_gb": self.system_info.available_ram_gb,
                "python_version": self.system_info.python_version
            },
            "gpus": [
                {
                    "name": gpu.name,
                    "memory_gb": gpu.memory_gb,
                    "vendor": gpu.vendor,
                    "available": gpu.is_available,
                    "driver": gpu.driver_version,
                    "compute": gpu.compute_capability
                }
                for gpu in self.gpus
            ]
        }

    def get_system_profile(self) -> str:
        """
        Classify system into one of five tiers based on VRAM:
        - cpu_only: no GPU
        - edge_4g: ≤ 4 GB VRAM
        - mid_8g: 6-8 GB VRAM
        - pro_12g: 10-12 GB VRAM
        - max: > 12 GB VRAM
        """
        primary_gpu = self.get_primary_gpu()

        if not primary_gpu or primary_gpu.vendor == "cpu":
            return "cpu_only"

        vram = primary_gpu.memory_gb

        if vram <= 4:
            return "edge_4g"
        elif 6 <= vram <= 8:
            return "mid_8g"
        elif 10 <= vram <= 12:
            return "pro_12g"
        else:  # vram > 12
            return "max"