"""Dataclasses representing the primary data contracts for KS AutoModel."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PipelineId = str


@dataclass(slots=True)
class HardwareInfo:
    """Snapshot of the host machine capabilities used for model selection."""

    cpu_name: str
    cpu_cores: int
    ram_gb: float
    os_name: str
    gpu_vendor: Optional[str] = None
    gpu_name: Optional[str] = None
    vram_gb: Optional[float] = None
    tier: str = "cpu_only"
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {
            "cpu": {"name": self.cpu_name, "cores": self.cpu_cores},
            "ram_gb": round(self.ram_gb, 2),
            "gpu": (
                {"vendor": self.gpu_vendor, "name": self.gpu_name, "vram_gb": self.vram_gb}
                if self.gpu_name
                else None
            ),
            "os": self.os_name,
            "tier": self.tier,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class AppProfile:
    """Summary of an analysed application directory."""

    project_path: Path
    summary: str
    tasks: List[str]
    hints: Dict[str, object] = field(default_factory=dict)

    def describe(self) -> str:
        return f"{self.summary} | Tasks: {', '.join(self.tasks) or 'unknown'}"


@dataclass(slots=True)
class ModelCandidate:
    """Represents a single model asset returned by a provider."""

    identifier: str
    display_name: str
    task: str
    framework: str
    format: str
    size_mb: float
    license: str
    url: str
    sha256: Optional[str] = None
    quantization: Optional[str] = None
    hardware_tier_hint: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    score: float = 0.0
    provider: str = "unknown"
    metadata: Dict[str, object] = field(default_factory=dict)

    def is_compatible_with(self, tier: str) -> bool:
        if not self.hardware_tier_hint:
            return True
        order = ["cpu_only", "edge_4g", "mid_8g", "pro_12g", "max"]
        try:
            return order.index(tier) >= order.index(self.hardware_tier_hint)
        except ValueError:
            return True


@dataclass(slots=True)
class PipelineStage:
    """Single stage in a pipeline recommendation."""

    task: str
    candidate: ModelCandidate
    rationale: str


@dataclass(slots=True)
class PipelineConfig:
    """Final composed pipeline recommendation."""

    pipeline_id: PipelineId
    stages: List[PipelineStage]
    estimated_disk_mb: float
    estimated_vram_gb: float
    estimated_latency_ms: float
    favor_quality: bool
    target_dir: Path
    notes: List[str] = field(default_factory=list)

    @property
    def tasks(self) -> Iterable[str]:
        return [stage.task for stage in self.stages]

    @property
    def total_models(self) -> int:
        return len(self.stages)

    def summary(self) -> Dict[str, object]:
        return {
            "id": self.pipeline_id,
            "tasks": list(self.tasks),
            "estimated_disk_mb": round(self.estimated_disk_mb, 1),
            "estimated_vram_gb": round(self.estimated_vram_gb, 2),
            "estimated_latency_ms": round(self.estimated_latency_ms, 1),
            "models": [
                {
                    "name": stage.candidate.display_name,
                    "task": stage.task,
                    "format": stage.candidate.format,
                    "size_mb": stage.candidate.size_mb,
                    "license": stage.candidate.license,
                    "provider": stage.candidate.provider,
                }
                for stage in self.stages
            ],
            "notes": list(self.notes),
        }
