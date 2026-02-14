from typing import Any, Dict, List


class MultiLaneDispatcher:
    POLICY_NAME = "target_affinity_round_robin_v1"

    def __init__(self, config):
        self.config = config

    def _enabled_targets(self) -> List[str]:
        enabled = getattr(self.config, "enabled_targets", None)
        targets = getattr(self.config, "targets", {})
        if not isinstance(enabled, list):
            return []
        return [name for name in enabled if isinstance(name, str) and name in targets]

    def _requested_lane_count(self) -> int:
        try:
            value = int(getattr(self.config, "multi_lane_max_lanes", 2))
        except Exception:
            value = 2
        return max(2, value)

    def _is_multi_lane_requested(self) -> bool:
        return bool(getattr(self.config, "multi_lane_enabled", False))

    def _is_parallel_enabled(self) -> bool:
        return bool(getattr(self.config, "multi_lane_parallel", False))

    def _init_lanes(self, lane_targets: List[str]) -> List[Dict[str, Any]]:
        lanes: List[Dict[str, Any]] = []
        for idx, target in enumerate(lane_targets, start=1):
            lanes.append(
                {
                    "id": f"lane_{idx:02d}",
                    "target": target,
                    "step_ids": [],
                }
            )
        return lanes

    def build_dispatch_plan(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        enabled_targets = self._enabled_targets()
        requested = self._is_multi_lane_requested()

        if not requested:
            return {
                "dispatch_mode": "single_lane",
                "execution_mode": "single_lane",
                "policy": "single_lane_only",
                "fallback_reason": "multi_lane_disabled",
                "lanes": [{"id": "lane_01", "target": "single_lane", "step_ids": [s.get("id") for s in steps]}],
            }

        if len(enabled_targets) < 2:
            return {
                "dispatch_mode": "single_lane",
                "execution_mode": "single_lane",
                "policy": "single_lane_only",
                "fallback_reason": "insufficient_enabled_targets",
                "lanes": [{"id": "lane_01", "target": "single_lane", "step_ids": [s.get("id") for s in steps]}],
            }

        lane_count = min(self._requested_lane_count(), len(enabled_targets))
        lane_targets = enabled_targets[:lane_count]
        lanes = self._init_lanes(lane_targets)
        target_to_lane = {lane["target"]: lane for lane in lanes}
        rr_index = 0

        for step in steps:
            step_id = step.get("id")
            step_type = str(step.get("type", "text")).lower()

            if step_type == "validate":
                lanes[0]["step_ids"].append(step_id)
                continue

            target = str(step.get("target", "")).strip()
            lane = target_to_lane.get(target)
            if lane is None:
                lane = lanes[rr_index % len(lanes)]
                rr_index += 1
            lane["step_ids"].append(step_id)

        if self._is_parallel_enabled():
            return {
                "dispatch_mode": "multi_lane",
                "execution_mode": "parallel_lanes",
                "policy": self.POLICY_NAME,
                "fallback_reason": None,
                "lanes": lanes,
            }

        return {
            "dispatch_mode": "multi_lane_skeleton",
            "execution_mode": "single_lane_fallback",
            "policy": self.POLICY_NAME,
            "fallback_reason": "skeleton_dispatch_only",
            "lanes": lanes,
        }
