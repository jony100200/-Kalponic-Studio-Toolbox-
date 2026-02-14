import json
import time
from typing import Callable, Optional, Dict, Any, List


class VSCodeSequencer:
    def __init__(self, automation, config):
        self.automation = automation
        self.config = config
        self.log_callback: Optional[Callable[[str], None]] = None

    def set_log_callback(self, callback: Callable[[str], None]):
        self.log_callback = callback

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def test_focus(self) -> bool:
        self._log("Testing focus...")
        ok = self.automation.focus_input()
        self._log("Focus test passed" if ok else "Focus test failed")
        return ok

    def list_targets(self) -> List[str]:
        if not isinstance(self.config.targets, dict):
            return []
        return list(self.config.targets.keys())

    def enabled_targets(self) -> List[str]:
        enabled = getattr(self.config, "enabled_targets", None)
        if not isinstance(enabled, list):
            return []
        return [name for name in enabled if name in self.config.targets]

    def set_enabled_targets(self, target_names: List[str]):
        if not target_names:
            raise ValueError("At least one enabled target is required")
        normalized = []
        for name in target_names:
            if name not in self.config.targets:
                raise ValueError(f"Unknown target: {name}")
            if name not in normalized:
                normalized.append(name)
        self.config.enabled_targets = normalized
        if self.config.active_target not in normalized:
            self.config.active_target = normalized[0]
        self.config.save()
        self._log(f"Enabled targets set: {', '.join(normalized)}")

    def _is_target_enabled(self, name: str) -> bool:
        enabled = self.enabled_targets()
        return name in enabled if enabled else False

    def set_active_target(self, target_name: str):
        if target_name not in self.config.targets:
            raise ValueError(f"Unknown target: {target_name}")
        if not self._is_target_enabled(target_name):
            raise ValueError(f"Target is disabled: {target_name}")
        self.config.active_target = target_name
        self.config.save()
        self._log(f"Active target set to: {target_name}")

    def _target_payload(self, target_name: Optional[str]) -> Dict[str, Any]:
        name = target_name or self.config.active_target
        target = self.config.targets.get(name)
        if not target:
            raise ValueError(f"Target not configured: {name}")
        return {"name": name, **target}

    def _allow_command_open_for(self, target_name: Optional[str], force_no_send: bool) -> bool:
        target = self._target_payload(target_name)
        if not force_no_send:
            return True
        return bool(target.get("command_open_in_test", False))

    def _focus_window_with_retry(self, retries: int = 3, sleep_s: float = 0.12) -> bool:
        for attempt in range(1, retries + 1):
            if self.automation.focus_window():
                return True
            if attempt < retries:
                time.sleep(sleep_s)
        return False

    def activate_target(
        self,
        target_name: Optional[str] = None,
        force_open: bool = False,
        allow_command_open: bool = True,
    ) -> bool:
        target = self._target_payload(target_name)
        name = target["name"]
        if not self._is_target_enabled(name):
            self._log(f"Target {name} is disabled")
            return False
        self._log(f"Activating target: {name}")
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
                self._log(f"Target {name} force-open retry {attempt}/3")
                time.sleep(0.12)
        elif force_open and not allow_command_open:
            self._log(f"Target {name} force-open suppressed in test mode")
            ok = self._focus_window_with_retry()
        elif click_only_activation:
            self._log(f"Target {name} click-only activation: no command/icon interactions")
            ok = self._focus_window_with_retry()
        elif not allow_command_open:
            self._log(f"Target {name} test-mode activation: no command/icon interactions")
            ok = self._focus_window_with_retry()
        elif assume_open:
            self._log(f"Target {name} assume-open mode: skipping open-chat command")
            ok = self._focus_window_with_retry()
        else:
            for attempt in range(1, 4):
                ok = self.automation.activate_panel(
                    command=target.get("command"),
                    focus_sequence=target.get("focus_sequence"),
                    fallback_click=target.get("fallback_click"),
                )
                if ok:
                    break
                self._log(f"Target {name} activation retry {attempt}/3")
                time.sleep(0.12)

        settle_delay_s = float(target.get("settle_delay_s", self.config.target_settle_delay_s))
        if ok and settle_delay_s > 0:
            self._log(f"Waiting {settle_delay_s:.2f}s for target settle")
            time.sleep(settle_delay_s)
        self._log(f"Target {name} ready" if ok else f"Target {name} activation failed")
        return ok

    def record_click(self, seconds: int = 4):
        self._log(f"Recording fallback click in {seconds} seconds...")
        value = self.automation.record_fallback_click(seconds=seconds)
        self._log(f"Saved fallback click: {value}")

    def record_target_click(self, target_name: Optional[str] = None, seconds: int = 4):
        target = self._target_payload(target_name)
        name = target["name"]
        self._log(f"Recording fallback click for target {name} in {seconds} seconds...")
        value = self.automation.record_fallback_click(seconds=seconds)
        target["fallback_click"] = dict(value)
        self.config.targets[name] = {k: v for k, v in target.items() if k != "name"}
        self.config.save()
        self._log(f"Saved target fallback click for {name}: {value}")

    def _focus_and_verify_target_input(
        self,
        target: Dict[str, Any],
        target_name: str,
        allow_command_open: bool = True,
    ) -> bool:
        base = target.get("fallback_click") or {}
        base_x = float(base.get("x_rel", 0.86))
        y_candidates = [
            float(base.get("y_rel", 0.90)),
            0.92,
            0.90,
            0.88,
            0.86,
            0.92,
        ]
        probe_text = f"KS_CODEOPS_INPUT_VERIFY_{target_name.upper()}"
        for y_rel in y_candidates:
            click = {"x_rel": base_x, "y_rel": y_rel}
            if not self.automation.focus_target_input(click):
                continue
            if self.automation.probe_type_text(probe_text, clear_after=True):
                if target.get("fallback_click") != click:
                    target["fallback_click"] = dict(click)
                    self.config.targets[target_name] = {k: v for k, v in target.items() if k != "name"}
                    self.config.save()
                    self._log(f"Adjusted target click for {target_name}: {click}")
                return True

        if bool(target.get("open_if_needed", False)) and allow_command_open:
            self._log(f"Input verify failed for {target_name}; trying open-if-needed path")
            if self.activate_target(target_name, force_open=True, allow_command_open=True):
                for y_rel in y_candidates:
                    click = {"x_rel": base_x, "y_rel": y_rel}
                    if not self.automation.focus_target_input(click):
                        continue
                    if self.automation.probe_type_text(probe_text, clear_after=True):
                        if target.get("fallback_click") != click:
                            target["fallback_click"] = dict(click)
                            self.config.targets[target_name] = {k: v for k, v in target.items() if k != "name"}
                            self.config.save()
                            self._log(f"Adjusted target click for {target_name}: {click}")
                        return True

        return False

    def send_text(
        self,
        text: str,
        press_enter: bool,
        target_name: Optional[str] = None,
        allow_command_open: bool = True,
    ):
        target = self._target_payload(target_name)
        name = target["name"]
        self._log(f"Sending text via target: {name}")
        activated = self.activate_target(name, allow_command_open=allow_command_open)
        if not activated:
            self._log(f"Activation failed for {name}; trying in-place focus fallback")
            if not self._focus_window_with_retry():
                self._log(f"Failed to activate target: {name}")
                return False
        if not self._focus_and_verify_target_input(target, name, allow_command_open=allow_command_open):
            self._log(f"Failed input verification (clicked non-input area): {name}")
            return False
        py_ok = self.automation.send_text(text, press_enter=press_enter, assume_focused=True)
        if py_ok:
            self._log("Text sent" if press_enter else "Text typed (test mode, not sent)")
        else:
            self._log("Failed to send text")
        ok = py_ok
        return ok

    def send_image(
        self,
        image_path: str,
        press_enter: bool,
        target_name: Optional[str] = None,
        allow_command_open: bool = True,
    ):
        target = self._target_payload(target_name)
        name = target["name"]
        self._log(f"Sending image via target {name}: {image_path}")
        activated = self.activate_target(name, allow_command_open=allow_command_open)
        if not activated:
            self._log(f"Activation failed for {name}; trying in-place focus fallback")
            if not self._focus_window_with_retry():
                self._log(f"Failed to activate target: {name}")
                return False
        if not self._focus_and_verify_target_input(target, name, allow_command_open=allow_command_open):
            self._log(f"Failed input verification (clicked non-input area): {name}")
            return False
        py_ok = self.automation.send_image(image_path, press_enter=press_enter, assume_focused=True)
        if py_ok:
            self._log("Image sent" if press_enter else "Image pasted (test mode, not sent)")
        else:
            self._log("Failed to send image")
        ok = py_ok
        return ok

    def probe_target_input(
        self,
        target_name: str,
        probe_text: str,
        clear_after: bool = True,
        allow_command_open: bool = False,
    ) -> bool:
        target = self._target_payload(target_name)
        name = target["name"]
        self._log(f"Probing target input: {name}")
        activated = self.activate_target(name, allow_command_open=allow_command_open)
        if not activated:
            self._log(f"Probe activation failed for {name}; trying in-place focus fallback")
            if not self.automation.focus_window():
                self._log(f"Probe failed: target activation failed ({name})")
                return False
        if not self._focus_and_verify_target_input(target, name, allow_command_open=allow_command_open):
            self._log(f"Probe failed: target input focus failed ({name})")
            return False
        ok = self.automation.probe_type_text(probe_text, clear_after=clear_after)
        self._log(f"Probe passed: {name}" if ok else f"Probe failed: {name}")
        return ok

    def auto_calibrate_target_click(self, target_name: str) -> bool:
        target = self._target_payload(target_name)
        name = target["name"]
        if not self._is_target_enabled(name):
            self._log(f"Target {name} is disabled")
            return False

        candidate_points = []
        for x in [0.10, 0.14, 0.18, 0.22, 0.26, 0.30]:
            for y in [0.84, 0.88, 0.90, 0.92]:
                candidate_points.append({"x_rel": x, "y_rel": y})
        candidate_points.extend([
            {"x_rel": 0.82, "y_rel": 0.90},
            {"x_rel": 0.86, "y_rel": 0.90},
        ])

        self._log(f"Auto-calibrating target click: {name}")
        probe_text = f"KS_CODEOPS_CALIBRATE_{name.upper()}"
        for point in candidate_points:
            if not self.activate_target(name):
                self._log(f"Auto-calibration skipped point; activation failed ({name})")
                continue
            self._log(f"Trying click {name}: x={point['x_rel']:.2f}, y={point['y_rel']:.2f}")
            if not self.automation.focus_target_input(point):
                continue
            first_ok = self.automation.probe_type_text(probe_text, clear_after=True)
            if not first_ok:
                continue
            time.sleep(0.08)
            if not self.automation.focus_target_input(point):
                continue
            second_ok = self.automation.probe_type_text(probe_text, clear_after=True)
            if second_ok:
                target["fallback_click"] = dict(point)
                self.config.targets[name] = {k: v for k, v in target.items() if k != "name"}
                self.config.save()
                self._log(f"Auto-calibration passed for {name}: {point}")
                return True

        self._log(f"Auto-calibration failed for {name}")
        return False

    def run_sequence(self, sequence_file: str, force_no_send: bool = False):
        self._log(f"Running sequence: {sequence_file}")
        with open(sequence_file, "r", encoding="utf-8") as handle:
            steps = json.load(handle)
        if not isinstance(steps, list):
            raise ValueError("Sequence must be a JSON array")

        for idx, step in enumerate(steps, start=1):
            step_type = step.get("type")
            step_target = step.get("target")
            wait_time = float(step.get("wait", 0))
            press_enter = bool(step.get("press_enter", self.config.auto_enter))
            if force_no_send:
                press_enter = False
            self._log(f"Step {idx}/{len(steps)}: {step_type} (target={step_target or self.config.active_target})")
            if step_type == "text":
                allow_open = self._allow_command_open_for(step_target, force_no_send)
                if not self.send_text(
                    step.get("content", ""),
                    press_enter=press_enter,
                    target_name=step_target,
                    allow_command_open=allow_open,
                ):
                    return False
            elif step_type == "image":
                path = step.get("path")
                if not path:
                    raise ValueError(f"Step {idx} missing image path")
                allow_open = self._allow_command_open_for(step_target, force_no_send)
                if not self.send_image(
                    path,
                    press_enter=press_enter,
                    target_name=step_target,
                    allow_command_open=allow_open,
                ):
                    return False
            else:
                raise ValueError(f"Unsupported step type: {step_type}")
            if wait_time > 0:
                time.sleep(wait_time)

        self._log("Sequence completed")
        return True

    def dispatch_multi(
        self,
        dispatch_items: List[Dict[str, Any]],
        default_press_enter: bool = True,
        force_no_send: bool = False,
    ) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for item in dispatch_items:
            target = item.get("target")
            content = item.get("content", "")
            press_enter = bool(item.get("press_enter", default_press_enter))
            if force_no_send:
                press_enter = False
            if not target:
                raise ValueError("dispatch item missing target")
            if not content:
                raise ValueError(f"dispatch item for target '{target}' missing content")
            allow_open = self._allow_command_open_for(target, force_no_send)
            ok = self.send_text(
                content,
                press_enter=press_enter,
                target_name=target,
                allow_command_open=allow_open,
            )
            results[target] = bool(ok)
        return results

    def run_target_test_sequence(self, targets: List[str], delay_between_s: float = 1.0, text_prefix: str = "KS_CODEOPS_SEQ") -> Dict[str, bool]:
        if not targets:
            raise ValueError("No targets provided for test sequence")

        valid_targets = []
        for name in targets:
            if name not in self.config.targets:
                raise ValueError(f"Unknown target: {name}")
            if name not in valid_targets:
                valid_targets.append(name)

        self.set_enabled_targets(valid_targets)

        results: Dict[str, bool] = {}
        for index, name in enumerate(valid_targets, start=1):
            self._log(f"[SEQUENCE] {index}/{len(valid_targets)} target={name}")
            payload = f"{text_prefix}_{name.upper()}"
            ok = self.send_text(
                payload,
                press_enter=False,
                target_name=name,
                allow_command_open=True,
            )
            results[name] = bool(ok)
            self._log(f"[SEQUENCE] {'PASS' if ok else 'FAIL'} target={name}")
            if index < len(valid_targets) and delay_between_s > 0:
                time.sleep(delay_between_s)

        return results

    def test_targets_next(self, target_names: List[str], pause_s: float = 1.0) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for target_name in target_names:
            if target_name not in self.config.targets:
                raise ValueError(f"Unknown target: {target_name}")
            if not self._is_target_enabled(target_name):
                self._log(f"Target {target_name} is disabled")
                results[target_name] = False
                continue

            self._log(f"Next target: {target_name}")
            allow_open = bool(self._target_payload(target_name).get("command_open_in_test", False))
            probe_text = f"KS_CODEOPS_PROBE_{target_name.upper()}"
            probed = self.probe_target_input(
                target_name,
                probe_text,
                clear_after=True,
                allow_command_open=allow_open,
            )
            if not probed:
                results[target_name] = False
                if pause_s > 0:
                    time.sleep(pause_s)
                continue

            typed = self.send_text(
                text=f"KS_CODEOPS_NEXT_{target_name.upper()}",
                press_enter=False,
                target_name=target_name,
                allow_command_open=allow_open,
            )
            results[target_name] = bool(typed)
            if pause_s > 0:
                time.sleep(pause_s)

        return results
