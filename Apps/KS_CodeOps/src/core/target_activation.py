import time
from typing import Any, Callable, Dict, Optional


class TargetActivator:
    def __init__(self, automation, config, is_target_enabled: Callable[[str], bool], log: Callable[[str], None]):
        self.automation = automation
        self.config = config
        self.is_target_enabled = is_target_enabled
        self.log = log

    def focus_window_with_retry(self, retries: int = 3, sleep_s: float = 0.12) -> bool:
        for attempt in range(1, retries + 1):
            if self.automation.focus_window():
                return True
            if attempt < retries:
                time.sleep(sleep_s)
        return False

    def activate_target(self, target: Dict[str, Any], force_open: bool = False, allow_command_open: bool = True) -> bool:
        name = target["name"]
        if not self.is_target_enabled(name):
            self.log(f"Target {name} is disabled")
            return False

        self.log(f"Activating target: {name}")
        assume_open = bool(target.get("assume_open", False))
        click_only_activation = bool(target.get("click_only_activation", False))

        ok = False
        if force_open and allow_command_open:
            for attempt in range(1, 4):
                ok = self.automation.activate_panel(
                    command=target.get("command"),
                    focus_sequence=target.get("focus_sequence"),
                    fallback_click=target.get("fallback_click"),
                )
                if ok:
                    break
                self.log(f"Target {name} force-open retry {attempt}/3")
                time.sleep(0.12)
        elif force_open and not allow_command_open:
            self.log(f"Target {name} force-open suppressed in test mode")
            ok = self.focus_window_with_retry()
        elif click_only_activation:
            self.log(f"Target {name} click-only activation: no command/icon interactions")
            ok = self.focus_window_with_retry()
        elif not allow_command_open:
            self.log(f"Target {name} test-mode activation: no command/icon interactions")
            ok = self.focus_window_with_retry()
        elif assume_open:
            self.log(f"Target {name} assume-open mode: skipping open-chat command")
            ok = self.focus_window_with_retry()
        else:
            for attempt in range(1, 4):
                ok = self.automation.activate_panel(
                    command=target.get("command"),
                    focus_sequence=target.get("focus_sequence"),
                    fallback_click=target.get("fallback_click"),
                )
                if ok:
                    break
                self.log(f"Target {name} activation retry {attempt}/3")
                time.sleep(0.12)

        settle_delay_s = float(target.get("settle_delay_s", self.config.target_settle_delay_s))
        if ok and settle_delay_s > 0:
            self.log(f"Waiting {settle_delay_s:.2f}s for target settle")
            time.sleep(settle_delay_s)

        self.log(f"Target {name} ready" if ok else f"Target {name} activation failed")
        return ok
