"""Pipeline composition and estimation."""

from __future__ import annotations

import itertools
import uuid
from pathlib import Path
from typing import Iterable, List, Sequence

from ..data import ModelCandidate, PipelineConfig, PipelineStage


class PipelineComposer:
    """Compose a lightweight pipeline from scored candidates."""

    def compose(
        self,
        candidates_by_task: dict[str, Sequence[ModelCandidate]],
        target_dir: Path,
        favor_quality: bool,
    ) -> PipelineConfig:
        stages: List[PipelineStage] = []
        total_disk = 0.0
        total_vram = 0.0
        total_latency = 0.0

        for task, candidates in candidates_by_task.items():
            if not candidates:
                continue
            candidate = self._select_candidate(candidates, favor_quality)
            rationale = self._build_rationale(candidate, favor_quality)
            stages.append(PipelineStage(task=task, candidate=candidate, rationale=rationale))
            total_disk += candidate.size_mb
            total_vram += self._estimate_vram(candidate)
            total_latency += self._estimate_latency(candidate)

        pipeline_id = uuid.uuid4().hex[:10]
        return PipelineConfig(
            pipeline_id=pipeline_id,
            stages=stages,
            estimated_disk_mb=round(total_disk, 2),
            estimated_vram_gb=round(total_vram, 2),
            estimated_latency_ms=round(total_latency, 2),
            favor_quality=favor_quality,
            target_dir=target_dir,
            notes=[
                "Estimates are heuristic – verify before deployment.",
                "Pipeline composed with %s preference." % ("quality" if favor_quality else "small size"),
            ],
        )

    def _select_candidate(self, candidates: Sequence[ModelCandidate], favor_quality: bool) -> ModelCandidate:
        if favor_quality:
            return max(candidates, key=lambda c: c.score)
        return min(candidates, key=lambda c: (c.size_mb, -c.score))

    def _estimate_vram(self, candidate: ModelCandidate) -> float:
        baseline = 1.0 if candidate.format in {"onnx", "int8"} else 1.5
        if candidate.quantization == "fp16":
            baseline *= 0.6
        if candidate.quantization == "int8":
            baseline *= 0.4
        return max(0.5, baseline)

    def _estimate_latency(self, candidate: ModelCandidate) -> float:
        base = 150.0
        multiplier = 1.0
        if candidate.size_mb > 500:
            multiplier += 0.5
        if candidate.quantization in {"int8", "fp16"}:
            multiplier *= 0.7
        return base * multiplier
