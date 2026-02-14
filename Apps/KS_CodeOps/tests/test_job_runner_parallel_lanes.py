import json
import os
import sys
import tempfile
import time
import unittest

from src.core.job_runner import JobRunner


class _DummySequencer:
    def _log(self, _message: str):
        return None

    def send_text(self, _text: str, press_enter: bool, target_name=None):
        return True

    def send_image(self, _image_path: str, press_enter: bool, target_name=None):
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
    multi_lane_parallel = True
    multi_lane_max_lanes = 2
    target_health_max_age_s = 1800.0
    lane_lock_stale_s = 120.0

    def __init__(self, adapter_script: str):
        self.python_executable = sys.executable
        self.targets = {"copilot": {}, "gemini": {}}
        self.enabled_targets = ["copilot", "gemini"]
        self.target_health_file = ""
        self.worker_adapters = {
            "slow_adapter": {
                "command": "\"{python}\" \"{adapter_script}\" \"{request_file}\" \"{response_file}\"",
                "command_vars": {"adapter_script": adapter_script},
                "timeout_s": 20,
                "poll_interval_s": 0.1,
            }
        }


class TestJobRunnerParallelLanes(unittest.TestCase):
    def test_parallel_worker_lanes_complete_faster_than_serial(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter_script = os.path.join(temp_dir, "adapter_slow.py")
            with open(adapter_script, "w", encoding="utf-8") as handle:
                handle.write(
                    "import json, sys, time\n"
                    "request_path, response_path = sys.argv[1], sys.argv[2]\n"
                    "with open(request_path, 'r', encoding='utf-8') as r:\n"
                    "    payload = json.load(r)\n"
                    "time.sleep(1.5)\n"
                    "step_id = payload.get('step_id', 'unknown')\n"
                    "response = {\n"
                    "    'status': 'ok',\n"
                    "    'output_text': '# Parallel\\n' + step_id + '\\n',\n"
                    "}\n"
                    "with open(response_path, 'w', encoding='utf-8') as w:\n"
                    "    json.dump(response, w)\n"
                )

            plan = {
                "name": "parallel_lanes_test",
                "steps": [
                    {
                        "id": "s1",
                        "type": "worker_contract",
                        "target": "copilot",
                        "content": "alpha",
                        "worker": {"adapter": "slow_adapter"},
                        "output_file": "outputs/s1.md",
                        "validator": {"type": "exists"},
                    },
                    {
                        "id": "s2",
                        "type": "worker_contract",
                        "target": "gemini",
                        "content": "beta",
                        "worker": {"adapter": "slow_adapter"},
                        "output_file": "outputs/s2.md",
                        "validator": {"type": "exists"},
                    },
                ],
            }
            with open(os.path.join(temp_dir, "plan.json"), "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)

            runner = JobRunner(_DummySequencer(), _DummyConfig(adapter_script))
            started = time.time()
            ok = runner.run_job(temp_dir)
            elapsed = time.time() - started

            self.assertTrue(ok)
            self.assertLess(elapsed, 2.6, msg=f"expected parallel runtime, got {elapsed:.2f}s")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "outputs", "s1.md")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "outputs", "s2.md")))

            with open(os.path.join(temp_dir, "status.json"), "r", encoding="utf-8") as handle:
                status = json.load(handle)
            self.assertEqual(status.get("mode"), "parallel_lanes")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "lane_summary.json")))


if __name__ == "__main__":
    unittest.main()
