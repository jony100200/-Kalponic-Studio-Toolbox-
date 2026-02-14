import unittest

from src.core.multi_lane_dispatcher import MultiLaneDispatcher


class _DummyConfig:
    def __init__(self, multi_lane_enabled: bool, enabled_targets=None, multi_lane_parallel: bool = False):
        self.targets = {
            "copilot": {},
            "gemini": {},
            "codex": {},
        }
        self.enabled_targets = enabled_targets or ["copilot", "gemini", "codex"]
        self.multi_lane_enabled = multi_lane_enabled
        self.multi_lane_max_lanes = 2
        self.multi_lane_parallel = multi_lane_parallel


class TestMultiLaneDispatcher(unittest.TestCase):
    def test_falls_back_when_disabled(self):
        dispatcher = MultiLaneDispatcher(_DummyConfig(multi_lane_enabled=False))
        steps = [{"id": "s1", "type": "text", "target": "copilot"}]
        plan = dispatcher.build_dispatch_plan(steps)
        self.assertEqual(plan["dispatch_mode"], "single_lane")
        self.assertEqual(plan["execution_mode"], "single_lane")
        self.assertEqual(plan["fallback_reason"], "multi_lane_disabled")

    def test_falls_back_when_insufficient_targets(self):
        dispatcher = MultiLaneDispatcher(
            _DummyConfig(multi_lane_enabled=True, enabled_targets=["copilot"])
        )
        steps = [{"id": "s1", "type": "text", "target": "copilot"}]
        plan = dispatcher.build_dispatch_plan(steps)
        self.assertEqual(plan["dispatch_mode"], "single_lane")
        self.assertEqual(plan["fallback_reason"], "insufficient_enabled_targets")

    def test_builds_multi_lane_skeleton_plan(self):
        dispatcher = MultiLaneDispatcher(_DummyConfig(multi_lane_enabled=True))
        steps = [
            {"id": "s1", "type": "text", "target": "copilot"},
            {"id": "s2", "type": "text", "target": "gemini"},
            {"id": "s3", "type": "validate"},
        ]
        plan = dispatcher.build_dispatch_plan(steps)
        self.assertEqual(plan["dispatch_mode"], "multi_lane_skeleton")
        self.assertEqual(plan["execution_mode"], "single_lane_fallback")
        self.assertEqual(plan["fallback_reason"], "skeleton_dispatch_only")
        self.assertEqual(len(plan["lanes"]), 2)
        self.assertEqual(plan["lanes"][0]["target"], "copilot")
        self.assertEqual(plan["lanes"][1]["target"], "gemini")

    def test_enables_parallel_lane_execution_when_flagged(self):
        dispatcher = MultiLaneDispatcher(
            _DummyConfig(multi_lane_enabled=True, multi_lane_parallel=True)
        )
        steps = [
            {"id": "s1", "type": "worker_contract", "target": "copilot"},
            {"id": "s2", "type": "worker_contract", "target": "gemini"},
        ]
        plan = dispatcher.build_dispatch_plan(steps)
        self.assertEqual(plan["dispatch_mode"], "multi_lane")
        self.assertEqual(plan["execution_mode"], "parallel_lanes")
        self.assertIsNone(plan["fallback_reason"])
        self.assertEqual(len(plan["lanes"]), 2)


if __name__ == "__main__":
    unittest.main()
