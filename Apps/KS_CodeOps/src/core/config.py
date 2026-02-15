import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Dict, Any, List


def default_targets() -> Dict[str, Dict[str, Any]]:
    return {
        "copilot": {
            "command": "Chat: Open Chat",
            "focus_sequence": ["ctrl+alt+i"],
            "fallback_click": {"x_rel": 0.86, "y_rel": 0.92},
            "assume_open": True,
            "click_only_activation": True,
            "open_if_needed": False,
            "command_open_in_test": False,
            "settle_delay_s": 0.2,
        },
        "gemini": {
            "command": "Gemini: Open Chat",
            "focus_sequence": ["ctrl+shift+p", "tab", "tab"],
            "fallback_click": {"x_rel": 0.86, "y_rel": 0.92},
            "assume_open": False,
            "click_only_activation": False,
            "open_if_needed": True,
            "command_open_in_test": True,
            "settle_delay_s": 0.6,
        },
        "codex": {
            "command": "Codex: Open Chat",
            "focus_sequence": ["ctrl+shift+p", "tab", "tab"],
            "fallback_click": {"x_rel": 0.86, "y_rel": 0.92},
            "assume_open": False,
            "click_only_activation": False,
            "open_if_needed": True,
            "command_open_in_test": True,
            "settle_delay_s": 0.6,
        },
        "kilo": {
            "command": "Kilo Code: Open Chat",
            "focus_sequence": ["ctrl+shift+p", "tab", "tab"],
            "fallback_click": {"x_rel": 0.86, "y_rel": 0.92},
            "assume_open": False,
            "click_only_activation": False,
            "open_if_needed": True,
            "command_open_in_test": True,
            "settle_delay_s": 0.6,
        },
        "cline": {
            "command": "Cline: Open In Sidebar",
            "focus_sequence": ["ctrl+shift+p", "tab", "tab"],
            "fallback_click": {"x_rel": 0.86, "y_rel": 0.92},
            "assume_open": False,
            "click_only_activation": False,
            "open_if_needed": True,
            "command_open_in_test": True,
            "settle_delay_s": 0.6,
        },
    }


def default_worker_adapters() -> Dict[str, Dict[str, Any]]:
    return {
        "copilot_vscode": {
            "mode": "vscode_chat",
            "target": "copilot",
            "allow_command_open": False,
            "press_enter": True,
            "capture": {"source": "bridge"},
            "timeout_s": 120.0,
            "poll_interval_s": 1.0,
        },
        "cline_vscode": {
            "mode": "vscode_chat",
            "target": "cline",
            "allow_command_open": True,
            "press_enter": True,
            "capture": {"source": "bridge"},
            "timeout_s": 120.0,
            "poll_interval_s": 1.0,
        },
        "gemini_vscode": {
            "mode": "vscode_chat",
            "target": "gemini",
            "allow_command_open": True,
            "press_enter": True,
            "capture": {"source": "bridge"},
            "timeout_s": 120.0,
            "poll_interval_s": 1.0,
        },
        "codex_vscode": {
            "mode": "vscode_chat",
            "target": "codex",
            "allow_command_open": True,
            "press_enter": True,
            "capture": {"source": "bridge"},
            "timeout_s": 120.0,
            "poll_interval_s": 1.0,
        },
        "kilo_vscode": {
            "mode": "vscode_chat",
            "target": "kilo",
            "allow_command_open": True,
            "press_enter": True,
            "capture": {"source": "bridge"},
            "timeout_s": 120.0,
            "poll_interval_s": 1.0,
        },
    }


@dataclass
class AppConfig:
    window_title: str = "KS CodeOps"
    maximize_on_focus: bool = True
    focus_profile: str = "chat_panel"
    automation_backend: str = "pyautogui"
    verify_marker: str = "<<<TEST>>>"
    capture_begin_marker: str = "BEGIN_OUTPUT"
    capture_end_marker: str = "END_OUTPUT"
    bridge_response_file: str = ".ks_codeops/bridge/latest_response.txt"
    completion_timeout_s: float = 90.0
    completion_poll_interval_s: float = 2.0
    completion_require_fresh_capture: bool = True
    eta_step_seconds: float = 8.0
    multi_lane_enabled: bool = False
    multi_lane_max_lanes: int = 2
    multi_lane_parallel: bool = False
    target_health_file: str = "target_health.json"
    target_health_max_age_s: float = 1800.0
    lane_lock_stale_s: float = 300.0
    worker_adapters: Dict[str, Dict[str, Any]] = None
    python_executable: str = sys.executable
    target_settle_delay_s: float = 0.5
    active_target: str = "copilot"
    enabled_targets: List[str] = None
    auto_enter: bool = False
    image_upload_delay: float = 2.5
    fallback_click: Dict[str, float] = None
    targets: Dict[str, Dict] = None
    _config_file: str = "config.json"

    def __post_init__(self):
        if self.fallback_click is None:
            self.fallback_click = {"x_rel": 0.5, "y_rel": 0.9}
        if self.targets is None:
            self.targets = {}
        if self.worker_adapters is None:
            self.worker_adapters = {}
        if self.enabled_targets is None:
            self.enabled_targets = []
        self.load()
        self._ensure_defaults()

    def _ensure_defaults(self):
        base = default_targets()
        if not isinstance(self.targets, dict):
            self.targets = {}
        for name, target in base.items():
            if name not in self.targets or not isinstance(self.targets.get(name), dict):
                self.targets[name] = dict(target)
            else:
                if "command" not in self.targets[name]:
                    self.targets[name]["command"] = target["command"]
                if "focus_sequence" not in self.targets[name]:
                    self.targets[name]["focus_sequence"] = list(target["focus_sequence"])
                if "fallback_click" not in self.targets[name]:
                    self.targets[name]["fallback_click"] = dict(target["fallback_click"])
                if "assume_open" not in self.targets[name]:
                    self.targets[name]["assume_open"] = bool(target["assume_open"])
                if "click_only_activation" not in self.targets[name]:
                    self.targets[name]["click_only_activation"] = bool(target["click_only_activation"])
                if "open_if_needed" not in self.targets[name]:
                    self.targets[name]["open_if_needed"] = bool(target["open_if_needed"])
                if "command_open_in_test" not in self.targets[name]:
                    self.targets[name]["command_open_in_test"] = bool(target["command_open_in_test"])
                if "settle_delay_s" not in self.targets[name]:
                    self.targets[name]["settle_delay_s"] = float(target["settle_delay_s"])
        if not self.active_target or self.active_target not in self.targets:
            self.active_target = "copilot" if "copilot" in self.targets else next(iter(self.targets.keys()), "copilot")

        if not isinstance(self.enabled_targets, list):
            self.enabled_targets = []
        self.enabled_targets = [name for name in self.enabled_targets if isinstance(name, str) and name in self.targets]
        if not self.enabled_targets:
            self.enabled_targets = ["copilot"] if "copilot" in self.targets else [self.active_target]
        if self.active_target not in self.enabled_targets:
            self.active_target = self.enabled_targets[0]
        if not isinstance(self.worker_adapters, dict):
            self.worker_adapters = {}
        adapter_defaults = default_worker_adapters()
        for name, payload in adapter_defaults.items():
            if name not in self.worker_adapters or not isinstance(self.worker_adapters.get(name), dict):
                self.worker_adapters[name] = dict(payload)
                continue
            for key, value in payload.items():
                if key not in self.worker_adapters[name]:
                    if isinstance(value, dict):
                        self.worker_adapters[name][key] = dict(value)
                    else:
                        self.worker_adapters[name][key] = value

    def load(self):
        if not os.path.exists(self._config_file):
            return
        with open(self._config_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        # Ensure fallback_click and targets exist after loading
        if not hasattr(self, "fallback_click") or self.fallback_click is None:
            self.fallback_click = {"x_rel": 0.5, "y_rel": 0.9}
        if not hasattr(self, "targets") or self.targets is None:
            self.targets = {}
        if not hasattr(self, "enabled_targets") or self.enabled_targets is None:
            self.enabled_targets = []
        if not hasattr(self, "worker_adapters") or self.worker_adapters is None:
            self.worker_adapters = {}
        if not hasattr(self, "active_target") or not self.active_target:
            self.active_target = "copilot"
        if not hasattr(self, "python_executable") or not self.python_executable:
            self.python_executable = sys.executable

    def save(self):
        payload = {k: v for k, v in asdict(self).items() if not k.startswith("_")}
        with open(self._config_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def as_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if not k.startswith("_")}
