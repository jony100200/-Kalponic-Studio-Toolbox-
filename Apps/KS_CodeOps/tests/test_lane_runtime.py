import json
import os
import tempfile
import unittest
from datetime import datetime

from src.core.lane_runtime import LaneRuntimeCoordinator


class _DummyConfig:
    def __init__(self, health_file: str):
        self.active_target = "copilot"
        self.targets = {
            "copilot": {},
            "gemini": {},
            "codex": {},
        }
        self.enabled_targets = ["copilot", "gemini", "codex"]
        self.target_health_file = health_file
        self.target_health_max_age_s = 1800.0
        self.lane_lock_stale_s = 120.0


class TestLaneRuntimeCoordinator(unittest.TestCase):
    def test_initialize_creates_lane_worktrees_and_status_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _DummyConfig(health_file=os.path.join(temp_dir, "target_health.json"))
            runtime = LaneRuntimeCoordinator(config)
            dispatch_plan = {
                "lanes": [
                    {"id": "lane_01", "target": "copilot", "step_ids": ["s1"]},
                    {"id": "lane_02", "target": "gemini", "step_ids": ["s2"]},
                ]
            }

            context = runtime.initialize(temp_dir, dispatch_plan, step_ids=["s1", "s2"])

            self.assertTrue(os.path.isdir(os.path.join(temp_dir, "lanes", "lane_01", "worktree")))
            self.assertTrue(os.path.isdir(os.path.join(temp_dir, "lanes", "lane_02", "worktree")))
            self.assertEqual(context["step_to_lane"]["s1"], "lane_01")
            self.assertEqual(context["step_to_lane"]["s2"], "lane_02")

            status_path = os.path.join(temp_dir, "lanes", "lane_01", "status.json")
            self.assertTrue(os.path.exists(status_path))
            with open(status_path, "r", encoding="utf-8") as handle:
                status = json.load(handle)
            self.assertEqual(status["metrics"]["steps_total"], 1)

    def test_resolve_target_reroutes_from_unhealthy_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            health_file = os.path.join(temp_dir, "target_health.json")
            with open(health_file, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "checked_at": datetime.now().isoformat(),
                        "targets": {
                            "copilot": {"healthy": False},
                            "gemini": {"healthy": True},
                        },
                    },
                    handle,
                    indent=2,
                )

            config = _DummyConfig(health_file=health_file)
            runtime = LaneRuntimeCoordinator(config)
            runtime.initialize(
                temp_dir,
                {"lanes": [{"id": "lane_01", "target": "copilot", "step_ids": ["s1"]}]},
                step_ids=["s1"],
            )

            target, reason = runtime.resolve_target("copilot", "lane_01")
            self.assertEqual(target, "gemini")
            self.assertEqual(reason, "unhealthy_target:copilot")

    def test_lock_status_and_summary_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = _DummyConfig(health_file=os.path.join(temp_dir, "target_health.json"))
            runtime = LaneRuntimeCoordinator(config)
            runtime.initialize(
                temp_dir,
                {"lanes": [{"id": "lane_01", "target": "copilot", "step_ids": ["s1"]}]},
                step_ids=["s1"],
            )

            runtime.start_step_attempt(temp_dir, "lane_01", "s1", attempt=1, target="copilot")
            lock_path = os.path.join(temp_dir, "lanes", "lane_01", "lock.json")
            self.assertTrue(os.path.exists(lock_path))

            runtime.finish_step_attempt(
                temp_dir,
                "lane_01",
                "s1",
                success=True,
                duration_s=0.5,
            )
            self.assertFalse(os.path.exists(lock_path))

            status_path = os.path.join(temp_dir, "lanes", "lane_01", "status.json")
            with open(status_path, "r", encoding="utf-8") as handle:
                status = json.load(handle)
            self.assertEqual(status["metrics"]["attempts_total"], 1)
            self.assertEqual(status["metrics"]["steps_completed"], 1)

            summary = runtime.finalize_run(
                job_dir=temp_dir,
                dispatch_plan={"dispatch_mode": "single_lane", "execution_mode": "single_lane"},
                overall_state="completed",
            )
            self.assertEqual(summary["state"], "completed")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "lane_summary.json")))


if __name__ == "__main__":
    unittest.main()
