from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ScheduleDecision:
    target: str
    reason: str


class RuleBasedTaskScheduler:
    POLICY_NAME = "runtime_rule_scheduler_v1"

    def __init__(self, config):
        self.config = config

    def _enabled_targets(self) -> List[str]:
        enabled = getattr(self.config, "enabled_targets", None)
        if not isinstance(enabled, list):
            return []
        targets = getattr(self.config, "targets", {})
        return [name for name in enabled if isinstance(name, str) and name in targets]

    def _target_pool(self) -> List[str]:
        enabled = self._enabled_targets()
        if enabled:
            return enabled

        active = getattr(self.config, "active_target", "")
        targets = getattr(self.config, "targets", {})
        if isinstance(active, str) and active in targets:
            return [active]

        return list(targets.keys())

    def _step_descriptor(self, step: Dict[str, Any]) -> str:
        return " ".join(
            str(part)
            for part in [
                step.get("id", ""),
                step.get("type", ""),
                step.get("prompt_file", ""),
                step.get("assignment_hint", ""),
            ]
            if part
        ).lower()

    def _choose_target(self, descriptor: str, index: int, target_pool: List[str]) -> ScheduleDecision:
        if not target_pool:
            fallback = getattr(self.config, "active_target", "copilot")
            return ScheduleDecision(target=fallback, reason="fallback_active_target")

        if len(target_pool) == 1:
            return ScheduleDecision(target=target_pool[0], reason="single_enabled_target")

        if any(token in descriptor for token in ["research", "audit", "discovery", "constraints"]):
            return ScheduleDecision(target=target_pool[0], reason="rule_research")
        if any(token in descriptor for token in ["design", "architecture", "structure", "plan"]):
            pick = target_pool[min(1, len(target_pool) - 1)]
            return ScheduleDecision(target=pick, reason="rule_design")
        if any(token in descriptor for token in ["implement", "code", "prototype", "build"]):
            pick = target_pool[min(2, len(target_pool) - 1)]
            return ScheduleDecision(target=pick, reason="rule_implementation")
        if any(token in descriptor for token in ["qa", "test", "validate", "package", "launch"]):
            return ScheduleDecision(target=target_pool[-1], reason="rule_qa")

        return ScheduleDecision(target=target_pool[index % len(target_pool)], reason="round_robin")

    def assign_missing_targets(self, steps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        target_pool = self._target_pool()
        assignments: List[Dict[str, str]] = []

        for index, step in enumerate(steps):
            step_type = str(step.get("type", "text")).lower()
            if step_type == "validate":
                continue

            existing_target = str(step.get("target", "")).strip()
            if existing_target:
                continue

            decision = self._choose_target(
                descriptor=self._step_descriptor(step),
                index=index,
                target_pool=target_pool,
            )
            step["target"] = decision.target
            step["assignment_reason"] = decision.reason
            assignments.append(
                {
                    "step_id": str(step.get("id", f"step_{index + 1}")),
                    "target": decision.target,
                    "reason": decision.reason,
                }
            )

        return assignments
