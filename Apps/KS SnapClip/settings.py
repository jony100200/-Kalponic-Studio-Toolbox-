"""Settings management for KS SnapClip

Simple dataclass with JSON persistence. Supports portable mode via base folder.
"""
from dataclasses import dataclass, asdict
from typing import Optional
import json
import os
from pathlib import Path


@dataclass
class Settings:
    output_folder: str = "captures"
    auto_save: bool = False
    auto_copy: bool = True
    filename_prefix: str = "snap"
    filename_pattern: str = "{prefix}_{window}_{timestamp}.png"
    max_history: int = 20
    use_legacy_input_folder: bool = False
    start_minimized: bool = True
    hotkeys_enabled: bool = False
    hotkey_area: str = "<ctrl>+<alt>+s"
    hotkey_window: str = "<ctrl>+<alt>+w"
    hotkey_monitor: str = "<ctrl>+<alt>+m"


DEFAULT_SETTINGS = Settings()


def get_settings_path(portable: bool = False) -> str:
    if portable:
        base = Path(__file__).parent
        return str(base / "config.json")
    # system-wide per-user
    appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    cfgdir = Path(appdata) / "KS_SnapClip"
    cfgdir.mkdir(parents=True, exist_ok=True)
    return str(cfgdir / "config.json")


def load_settings(portable: bool = False) -> Settings:
    path = get_settings_path(portable)
    if not os.path.exists(path):
        return DEFAULT_SETTINGS
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            s = Settings(**data)
            return s
    except Exception:
        return DEFAULT_SETTINGS


def save_settings(s: Settings, portable: bool = False):
    path = get_settings_path(portable)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(s), f, indent=2)
    except Exception:
        pass
