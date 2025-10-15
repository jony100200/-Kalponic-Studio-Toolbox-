"""Hardware profiling utilities."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from typing import Optional

import psutil

from ..data import HardwareInfo
from .utils import setup_logging

logger = setup_logging()


@dataclass
class GPUInfo:
    vendor: str
    name: str
    vram_gb: float


class HardwareProfiler:
    """Inspect host machine to derive hardware tier for model selection."""

    def detect(self) -> HardwareInfo:
        cpu_name = self._get_cpu_name()
        cpu_cores = psutil.cpu_count(logical=True) or 1
        ram_gb = psutil.virtual_memory().total / (1024**3)
        os_name = f"{platform.system()}-{platform.release()}"

        gpu = self._detect_gpu()
        tier = self._classify_tier(ram_gb=ram_gb, gpu=gpu)
        notes = []
        if not gpu:
            notes.append("No discrete GPU detected; CPU-first recommendations will be used.")
        elif gpu.vram_gb < 4:
            notes.append("Limited VRAM detected; preferring lightweight checkpoints.")

        return HardwareInfo(
            cpu_name=cpu_name,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            os_name=os_name,
            gpu_vendor=gpu.vendor if gpu else None,
            gpu_name=gpu.name if gpu else None,
            vram_gb=gpu.vram_gb if gpu else None,
            tier=tier,
            notes=notes,
        )

    def _get_cpu_name(self) -> str:
        cpu = platform.processor() or platform.machine()
        if cpu:
            return cpu.strip()
        try:
            info = subprocess.check_output(["wmic", "cpu", "get", "Name"], text=True)
            lines = [line.strip() for line in info.splitlines() if line.strip() and "Name" not in line]
            if lines:
                return lines[0]
        except Exception:
            pass
        return "Unknown CPU"

    def _detect_gpu(self) -> Optional[GPUInfo]:
        # Try NVIDIA via nvidia-smi
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            first_line = output.strip().splitlines()[0]
            name, memory = [part.strip() for part in first_line.split(",")]
            vram_gb = float(memory.split()[0]) / 1024 if "MiB" in memory else float(memory)
            return GPUInfo(vendor="NVIDIA", name=name, vram_gb=round(vram_gb, 2))
        except Exception:
            logger.debug("nvidia-smi not available or GPU not detected.")

        # Try DirectX via systeminfo (Windows) - fallback rough estimate
        if platform.system().lower() == "windows":
            try:
                output = subprocess.check_output(
                    ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM"],
                    text=True,
                )
                lines = [line.strip() for line in output.splitlines() if line.strip() and "AdapterRAM" not in line]
                if lines:
                    parts = lines[0].split()
                    name = " ".join(parts[:-1])
                    ram = float(parts[-1])
                    vram_gb = ram / (1024**3)
                    return GPUInfo(vendor="Unknown", name=name, vram_gb=round(vram_gb, 2))
            except Exception:
                logger.debug("Could not read GPU via WMIC.")

        return None

    def _classify_tier(self, ram_gb: float, gpu: Optional[GPUInfo]) -> str:
        if not gpu:
            return "cpu_only"
        vram = gpu.vram_gb
        if vram is None:
            return "cpu_only"
        if vram < 4:
            return "edge_4g"
        if vram < 8:
            return "mid_8g"
        if vram < 12:
            return "pro_12g"
        return "max"
