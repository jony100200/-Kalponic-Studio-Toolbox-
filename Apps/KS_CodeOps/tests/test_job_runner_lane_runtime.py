import json
import os
import tempfile
import unittest
from datetime import datetime

from src.core.job_runner import JobRunner


class _RecordingSequencer:
    def __init__(self):
        self.sent_targets = []

    def _log(self, _message: str):
        return None

    def send_text(self, _text: str, press_enter: bool, target_name=None):
        self.sent_targets.append(target_name)
        return True

    def send_image(self, _image_path: str, press_enter: bool, target_name=None):
        self.sent_targets.append(target_name)
        return True


class _DummyConfig:
    eta_step_seconds = 8.0
    active_target = "copilot"
    completion_timeout_s = 90.0
    completion_poll_interval_s = 2.0
    completion_require_fresh_capture = True
    capture_begin_marker = "BEGIN_OUTPUT"
    capture_end_marker = "END_OUTPUT"
    bridge_response_file = ".ks_codeops/bridge/latest_response.txt"
    multi_lane_enabled = True
    multi_lane_max_lanes = 2
    target_health_max_age_s = 1800.0
    lane_lock_stale_s = 120.0

    def __init__(self, health_file: str):
        self.target_health_file = health_file
        self.targets = {"copilot": {}, "gemini": {}}
        self.enabled_targets = ["copilot", "gemini"]


class TestJobRunnerLaneRuntime(unittest.TestCase):
    def test_reroutes_unhealthy_target_and_writes_lane_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            health_path = os.path.join(temp_dir, "target_health.json")
            with open(health_path, "w", encoding="utf-8") as handle:
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

            plan = {
                "name": "lane_runtime_reroute",
                "steps": [
                    {
                        "id": "s1",
                        "type": "text",
                        "content": "hello",
                        "target": "copilot",
                        "press_enter": False,
                    }
                ],
            }
            with open(os.path.join(temp_dir, "plan.json"), "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)

            sequencer = _RecordingSequencer()
            runner = JobRunner(sequencer, _DummyConfig(health_file=health_path))
            ok = runner.run_job(temp_dir)
            self.assertTrue(ok)
            self.assertEqual(sequencer.sent_targets, ["gemini"])

            summary_path = os.path.join(temp_dir, "lane_summary.json")
            self.assertTrue(os.path.exists(summary_path))
            with open(summary_path, "r", encoding="utf-8") as handle:
                summary = json.load(handle)
            self.assertEqual(summary["state"], "completed")
            self.assertTrue(summary["lanes"])


if __name__ == "__main__":
    unittest.main()
