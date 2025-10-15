"""Model download helpers."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

import requests

from ..data import ModelCandidate, PipelineConfig
from .utils import setup_logging

logger = setup_logging()


ProgressCallback = Callable[[str, float], None]


@dataclass
class DownloadResult:
    candidate: ModelCandidate
    path: Path
    sha256: Optional[str]


class ModelDownloader:
    """Download and verify model checkpoints."""

    def __init__(self, chunk_size: int = 2**20, simulate: bool = True) -> None:
        self.chunk_size = chunk_size
        self.simulate = simulate

    def download_pipeline(
        self,
        pipeline: PipelineConfig,
        progress: Optional[ProgressCallback] = None,
        verify_hashes: bool = False,
    ) -> Iterable[DownloadResult]:
        pipeline.target_dir.mkdir(parents=True, exist_ok=True)
        for stage in pipeline.stages:
            result = self.download_model(stage.candidate, pipeline.target_dir, progress, verify_hashes)
            yield result

    def download_model(
        self,
        candidate: ModelCandidate,
        target_dir: Path,
        progress: Optional[ProgressCallback] = None,
        verify_hash: bool = False,
    ) -> DownloadResult:
        target_dir.mkdir(parents=True, exist_ok=True)
        file_name = candidate.url.split("/")[-1] or f"{candidate.identifier}.bin"
        destination = target_dir / file_name
        logger.info("Downloading %s -> %s", candidate.display_name, destination)

        if self.simulate:
            destination.write_text(
                f"Simulated download for {candidate.display_name}\nSource: {candidate.url}\n",
                encoding="utf-8",
            )
            if progress:
                progress(candidate.display_name, 1.0)
            return DownloadResult(candidate=candidate, path=destination, sha256=None)

        with requests.get(candidate.url, stream=True, timeout=30) as response:
            response.raise_for_status()
            total = float(response.headers.get("Content-Length", 0))
            downloaded = 0.0
            hasher = hashlib.sha256()
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        hasher.update(chunk)
                        if progress and total:
                            progress(candidate.display_name, downloaded / total)

        sha256 = hasher.hexdigest()
        if verify_hash and candidate.sha256 and candidate.sha256.lower() != sha256.lower():
            destination.unlink(missing_ok=True)  # type: ignore[arg-type]
            raise ValueError(f"Checksum mismatch for {candidate.identifier}")

        return DownloadResult(candidate=candidate, path=destination, sha256=sha256)

    @staticmethod
    def cleanup_directory(path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)
