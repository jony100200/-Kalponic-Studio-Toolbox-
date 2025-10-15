"""Configuration manager for KS AutoModel."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import get_cache_dir, read_json, safe_write_file


DEFAULT_CONFIG = {
    "download_dir": str(Path.cwd() / "models"),
    "cache_dir": str(get_cache_dir()),
    "max_cache_gb": 6,
    "favor_quality": False,
    "ui_theme": "auto",
    "license_preferences": ["mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause"],
    "providers": {"huggingface": {"enabled": True}},
}


@dataclass
class ConfigManager:
    """Loads persisted config and provides access helpers."""

    config_path: Path
    _data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.config_path.exists():
            self._data = dict(DEFAULT_CONFIG)
            return
        self._data = DEFAULT_CONFIG | read_json(self.config_path, {})

    @property
    def download_dir(self) -> Path:
        path = Path(self._data.get("download_dir", DEFAULT_CONFIG["download_dir"]))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cache_dir(self) -> Path:
        path = Path(self._data.get("cache_dir", DEFAULT_CONFIG["cache_dir"]))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def favor_quality(self) -> bool:
        return bool(self._data.get("favor_quality", DEFAULT_CONFIG["favor_quality"]))

    @property
    def ui_theme(self) -> str:
        return str(self._data.get("ui_theme", DEFAULT_CONFIG["ui_theme"]))

    def update(self, **kwargs: Any) -> None:
        self._data.update(kwargs)
        self.save()

    def get_license_preferences(self) -> list[str]:
        return list(self._data.get("license_preferences", DEFAULT_CONFIG["license_preferences"]))

    def provider_enabled(self, name: str) -> bool:
        providers = self._data.get("providers", DEFAULT_CONFIG["providers"])
        return bool(providers.get(name, {}).get("enabled", False))

    def save(self) -> None:
        with safe_write_file(self.config_path) as tmp:
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
