"""Scoring logic for model candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from ..data import AppProfile, HardwareInfo, ModelCandidate


@dataclass
class ScoringPreferences:
    favor_quality: bool = False
    license_allow_list: Sequence[str] = ()
    max_size_mb: float = 500.0


class ScoringEngine:
    """Rank model candidates based on hardware fit and preferences."""

    def __init__(self, prefs: ScoringPreferences | None = None) -> None:
        self.prefs = prefs or ScoringPreferences()

    def score(
        self,
        hardware: HardwareInfo,
        profile: AppProfile,
        candidates: Iterable[ModelCandidate],
    ) -> List[ModelCandidate]:
        scored: List[ModelCandidate] = []
        for candidate in candidates:
            score = self._base_score(candidate, hardware)
            if self._violates_license(candidate):
                score -= 100
            if candidate.size_mb > self.prefs.max_size_mb and not self.prefs.favor_quality:
                score -= (candidate.size_mb - self.prefs.max_size_mb) * 0.2
            if candidate.task in profile.tasks:
                score += 20
            if candidate.quantization in {"int8", "fp16"}:
                score += 10
            if candidate.is_compatible_with(hardware.tier):
                score += 5
            candidate.score = round(score, 3)
            scored.append(candidate)
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored

    def _base_score(self, candidate: ModelCandidate, hardware: HardwareInfo) -> float:
        size_penalty = candidate.size_mb / 100
        tier_bonus = 5 if candidate.is_compatible_with(hardware.tier) else -10
        return 50 - size_penalty + tier_bonus

    def _violates_license(self, candidate: ModelCandidate) -> bool:
        if not self.prefs.license_allow_list:
            return False
        return candidate.license.lower() not in self.prefs.license_allow_list
