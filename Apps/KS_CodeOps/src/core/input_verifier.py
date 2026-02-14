from typing import Any, Callable, Dict, List


class TargetInputVerifier:
    def __init__(self, automation, config, log: Callable[[str], None], activate_target: Callable[..., bool]):
        self.automation = automation
        self.config = config
        self.log = log
        self.activate_target = activate_target

    def build_input_click_candidates(self, target: Dict[str, Any]) -> List[Dict[str, float]]:
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

        candidates: List[Dict[str, float]] = []
        seen = set()
        for y_rel in y_candidates:
            key = (round(base_x, 5), round(float(y_rel), 5))
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"x_rel": base_x, "y_rel": float(y_rel)})
        return candidates

    def _try_focus_verify_candidates(
        self,
        target: Dict[str, Any],
        target_name: str,
        click_candidates: List[Dict[str, float]],
        probe_text: str,
    ) -> bool:
        for click in click_candidates:
            if not self.automation.focus_target_input(click):
                continue
            if self.automation.probe_type_text(probe_text, clear_after=True):
                if target.get("fallback_click") != click:
                    target["fallback_click"] = dict(click)
                    self.config.targets[target_name] = {k: v for k, v in target.items() if k != "name"}
                    self.config.save()
                    self.log(f"[VERIFY] Adjusted target click for {target_name}: {click}")
                return True
        return False

    def focus_and_verify_target_input(
        self,
        target: Dict[str, Any],
        target_name: str,
        allow_command_open: bool = True,
    ) -> bool:
        click_candidates = self.build_input_click_candidates(target)
        probe_text = f"KS_CODEOPS_INPUT_VERIFY_{target_name.upper()}"

        if self._try_focus_verify_candidates(target, target_name, click_candidates, probe_text):
            return True

        if bool(target.get("open_if_needed", False)) and allow_command_open:
            self.log(f"[VERIFY] Input verify failed for {target_name}; trying open-if-needed path")
            if self.activate_target(target_name=target_name, force_open=True, allow_command_open=True):
                if self._try_focus_verify_candidates(target, target_name, click_candidates, probe_text):
                    return True

        return False
