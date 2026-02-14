import json
import os
import tempfile
import unittest

from src.core.job_runner import JobRunner


class _DummySequencer:
    def _log(self, _message: str):
        return None


class _DummyConfig:
    eta_step_seconds = 8.0
    active_target = "copilot"
    completion_timeout_s = 90.0
    completion_poll_interval_s = 2.0
    completion_require_fresh_capture = True
    capture_begin_marker = "BEGIN_OUTPUT"
    capture_end_marker = "END_OUTPUT"
    bridge_response_file = ".ks_codeops/bridge/latest_response.txt"


class TestJobRunnerResumeBehavior(unittest.TestCase):
    def test_completed_step_with_missing_output_is_rerun_and_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = {
                "name": "resume_test",
                "steps": [
                    {
                        "id": "step_ok",
                        "type": "validate",
                        "output_file": "outputs/result.md",
                        "validator": {"type": "exists"},
                    }
                ],
            }
            status = {
                "mode": "single_lane",
                "state": "running",
                "current_step": None,
                "steps": {
                    "step_ok": {
                        "state": "completed",
                        "attempts": 1,
                        "last_error": None,
                        "updated_at": "2026-01-01T00:00:00",
                    }
                },
                "started_at": "2026-01-01T00:00:00",
            }

            with open(os.path.join(temp_dir, "plan.json"), "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)
            with open(os.path.join(temp_dir, "status.json"), "w", encoding="utf-8") as handle:
                json.dump(status, handle, indent=2)

            runner = JobRunner(_DummySequencer(), _DummyConfig())
            ok = runner.run_job(temp_dir)
            self.assertFalse(ok)

            with open(os.path.join(temp_dir, "status.json"), "r", encoding="utf-8") as handle:
                final_status = json.load(handle)
            self.assertEqual(final_status["state"], "failed")
            self.assertEqual(final_status["failed_step"], "step_ok")


if __name__ == "__main__":
    unittest.main()
