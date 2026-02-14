from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class AssignmentDecision:
    target: str
    reason: str


class TargetAssignmentPolicy:
    def __init__(self, config):
        self.config = config

    def enabled_targets(self) -> List[str]:
        enabled = getattr(self.config, "enabled_targets", None)
        if not isinstance(enabled, list):
            return []
        targets = getattr(self.config, "targets", {})
        return [name for name in enabled if isinstance(name, str) and name in targets]

    def assignment_pool(self, explicit_target: str = "") -> Dict[str, Any]:
        fixed_target = (explicit_target or "").strip()
        if fixed_target:
            return {"policy": "fixed_target", "pool": [fixed_target]}

        enabled_pool = self.enabled_targets()
        if enabled_pool:
            return {"policy": "auto_enabled_targets_v1", "pool": enabled_pool}

        fallback = getattr(self.config, "active_target", "copilot")
        return {"policy": "fallback_active_target", "pool": [fallback]}

    def select_for_phase(self, phase_title: str, index: int, target_pool: List[str]) -> AssignmentDecision:
        if not target_pool:
            fallback = getattr(self.config, "active_target", "copilot")
            return AssignmentDecision(target=fallback, reason="fallback_active_target")

        if len(target_pool) == 1:
            return AssignmentDecision(target=target_pool[0], reason="single_enabled_target")

        title = phase_title.lower()
        if any(token in title for token in ["research", "audit", "discovery", "constraints"]):
            return AssignmentDecision(target=target_pool[0], reason="rule_research")
        if any(token in title for token in ["design", "architecture", "structure", "plan"]):
            pick = target_pool[min(1, len(target_pool) - 1)]
            return AssignmentDecision(target=pick, reason="rule_design")
        if any(token in title for token in ["implement", "code", "prototype", "build"]):
            pick = target_pool[min(2, len(target_pool) - 1)]
            return AssignmentDecision(target=pick, reason="rule_implementation")
        if any(token in title for token in ["qa", "test", "validate", "package", "launch"]):
            return AssignmentDecision(target=target_pool[-1], reason="rule_qa")

        return AssignmentDecision(target=target_pool[(index - 1) % len(target_pool)], reason="round_robin")
