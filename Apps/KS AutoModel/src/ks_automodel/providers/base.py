"""Base provider interface for fetching model metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

from ..data import ModelCandidate


class ModelProvider(ABC):
    """Common interface for model repositories."""

    name: str = "base"
    is_enabled: bool = True

    @abstractmethod
    def search(
        self,
        task: str,
        preferred_formats: Sequence[str],
        license_allow_list: Sequence[str],
        tags: Sequence[str],
        limit: int = 5,
    ) -> List[ModelCandidate]:
        """Return a list of model candidates for the given task."""
