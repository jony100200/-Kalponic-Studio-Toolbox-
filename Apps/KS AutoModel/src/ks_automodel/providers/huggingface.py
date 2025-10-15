"""Hugging Face model provider implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from ..core.utils import setup_logging
from ..data import ModelCandidate, ModelRegistry
from .base import ModelProvider

logger = setup_logging()


@dataclass
class HuggingFaceProvider(ModelProvider):
    """Query Hugging Face Hub and/or a local registry for models."""

    registry: ModelRegistry | None = None
    online_enabled: bool = True
    is_enabled: bool = True
    name: str = "huggingface"

    def search(
        self,
        task: str,
        preferred_formats: Sequence[str],
        license_allow_list: Sequence[str],
        tags: Sequence[str],
        limit: int = 5,
    ) -> List[ModelCandidate]:
        results: List[ModelCandidate] = []
        if self.registry:
            results.extend(
                self._filter_candidates(
                    list(self.registry.find_by_task(task)), preferred_formats, license_allow_list
                )
            )
        if self.online_enabled:
            results.extend(
                self._search_online(task, preferred_formats, license_allow_list, tags, limit=limit)
            )
        # Deduplicate by identifier while preserving order
        seen = set()
        unique: List[ModelCandidate] = []
        for candidate in results:
            if candidate.identifier in seen:
                continue
            seen.add(candidate.identifier)
            unique.append(candidate)
            if len(unique) >= limit:
                break
        return unique

    # Internal helpers -------------------------------------------------

    def _filter_candidates(
        self,
        candidates: List[ModelCandidate],
        preferred_formats: Sequence[str],
        license_allow_list: Sequence[str],
    ) -> List[ModelCandidate]:
        formatted: List[ModelCandidate] = []
        preferred_lower = [fmt.lower() for fmt in preferred_formats]
        allowed_licenses = {lic.lower() for lic in license_allow_list} if license_allow_list else None
        for candidate in candidates:
            if preferred_lower and candidate.format.lower() not in preferred_lower:
                continue
            if allowed_licenses and candidate.license.lower() not in allowed_licenses:
                continue
            formatted.append(candidate)
        return formatted

    def _search_online(
        self,
        task: str,
        preferred_formats: Sequence[str],
        license_allow_list: Sequence[str],
        tags: Sequence[str],
        limit: int,
    ) -> List[ModelCandidate]:
        try:
            from huggingface_hub import HfApi
        except Exception:
            logger.debug("huggingface_hub not available; skipping online search.")
            return []

        api = HfApi()
        query = {"pipeline_tag": task}
        if tags:
            query["tags"] = list(tags)

        try:
            models = api.list_models(filter=query, limit=limit)
        except Exception as exc:
            logger.debug("Failed to query Hugging Face Hub: %s", exc)
            return []

        results: List[ModelCandidate] = []
        preferred_lower = [fmt.lower() for fmt in preferred_formats]
        allowed_licenses = {lic.lower() for lic in license_allow_list} if license_allow_list else None
        for model in models:
            if allowed_licenses and (model.license or "unknown").lower() not in allowed_licenses:
                continue
            format_guess = self._infer_format(model.tags or [], preferred_lower)
            if preferred_lower and format_guess not in preferred_lower:
                continue
            identifier = model.modelId
            size_mb = (model.safetensorsSize or model.latestSiblings or None)
            size_guess = 0.0
            if isinstance(size_mb, (int, float)):
                size_guess = float(size_mb) / (1024 * 1024)
            candidate = ModelCandidate(
                identifier=identifier,
                display_name=model.modelId.split("/")[-1],
                task=task,
                framework="huggingface",
                format=format_guess or "unknown",
                size_mb=size_guess,
                license=model.license or "unknown",
                url=f"https://huggingface.co/{model.modelId}",
                provider=self.name,
                tags=model.tags or [],
                metadata={"likes": model.likes or 0},
            )
            results.append(candidate)
        return results

    def _infer_format(self, tags: Sequence[str], preferred_formats: Sequence[str]) -> str:
        tags_lower = [tag.lower() for tag in tags]
        for fmt in preferred_formats:
            if fmt.lower() in tags_lower:
                return fmt.lower()
        if "onnx" in tags_lower:
            return "onnx"
        if "int8" in tags_lower:
            return "int8"
        return preferred_formats[0].lower() if preferred_formats else "unknown"
