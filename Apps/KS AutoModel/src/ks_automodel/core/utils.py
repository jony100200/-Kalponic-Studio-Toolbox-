"""Shared utilities for KS AutoModel."""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


LOGGER_NAME = "ks_automodel"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a module-level logger with sensible defaults."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(levelname)s %(asctime)s %(name)s] %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


@contextmanager
def safe_write_file(path: Path, overwrite: bool = True) -> Iterator[Path]:
    """
    Write to a temporary file and atomically move it into place.
    Avoids partially written configs when the app exits unexpectedly.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    try:
        yield tmp_path
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]


def read_json(path: Path, default: Optional[dict] = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default or {}


def resolve_project_path(path: Optional[str]) -> Path:
    if not path:
        return Path.cwd()
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Project path does not exist: {p}")
    return p


def get_cache_dir() -> Path:
    base = Path(os.environ.get("KS_AUTOMODEL_CACHE", Path.home() / ".ks_automodel"))
    cache_dir = base / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
