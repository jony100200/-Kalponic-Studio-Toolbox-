"""Aggregate providers to find model candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from ..data import ModelCandidate
from ..providers import ModelProvider


@dataclass
class SearchFilters:
    task: str
    preferred_formats: Sequence[str]
    license_allow_list: Sequence[str]
    limit: int = 6
    tags: Sequence[str] = ()


class ModelFinder:
    """Coordinates multiple providers to gather candidate models."""

    def __init__(self, providers: Iterable[ModelProvider]) -> None:
        self.providers = list(providers)

    def search(self, filters: SearchFilters) -> List[ModelCandidate]:
        results: List[ModelCandidate] = []
        for provider in self.providers:
            if not provider.is_enabled:
                continue
            provider_results = provider.search(
                task=filters.task,
                preferred_formats=filters.preferred_formats,
                license_allow_list=list(filters.license_allow_list),
                tags=list(filters.tags),
                limit=filters.limit,
            )
            results.extend(provider_results)
        # Deduplicate by identifier
        unique: Dict[str, ModelCandidate] = {}
        for candidate in results:
            unique.setdefault(candidate.identifier, candidate)
        return list(unique.values())
