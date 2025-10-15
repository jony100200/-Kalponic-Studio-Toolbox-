"""Local registry helper for curated model metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import ModelCandidate


@dataclass
class ModelRegistry:
    """Loads curated models from JSON files for offline usage and testing."""

    registry_paths: List[Path]

    def __post_init__(self) -> None:
        self._cache: Dict[str, Dict[str, object]] = {}
        self.refresh()

    def refresh(self) -> None:
        self._cache.clear()
        for path in self.registry_paths:
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for entry in data.get("models", []):
                identifier = entry.get("identifier")
                if not identifier:
                    continue
                self._cache[identifier] = entry

    def list(self) -> Iterable[ModelCandidate]:
        for entry in self._cache.values():
            yield self._to_candidate(entry)

    def find_by_task(self, task: str) -> Iterable[ModelCandidate]:
        task_lower = task.lower()
        for entry in self._cache.values():
            if task_lower in (v.lower() for v in entry.get("tasks", [])):
                yield self._to_candidate(entry)

    def get(self, identifier: str) -> Optional[ModelCandidate]:
        entry = self._cache.get(identifier)
        return self._to_candidate(entry) if entry else None

    @staticmethod
    def _to_candidate(entry: Dict[str, object]) -> ModelCandidate:
        return ModelCandidate(
            identifier=entry["identifier"],
            display_name=entry.get("display_name", entry["identifier"]),
            task=entry.get("primary_task", entry.get("tasks", ["unknown"])[0]),
            framework=entry.get("framework", "onnx"),
            format=entry.get("format", "onnx"),
            size_mb=float(entry.get("size_mb", 0.0)),
            license=entry.get("license", "unknown"),
            url=entry.get("url", ""),
            sha256=entry.get("sha256"),
            quantization=entry.get("quantization"),
            hardware_tier_hint=entry.get("hardware_tier_hint"),
            tags=list(entry.get("tags", [])),
            provider=entry.get("provider", "registry"),
            metadata=entry.get("metadata", {}),
        )
