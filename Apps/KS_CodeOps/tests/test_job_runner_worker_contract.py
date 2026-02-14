import json
import os
import sys
import tempfile
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
    multi_lane_enabled = False
    multi_lane_parallel = False
    multi_lane_max_lanes = 2
    target_health_max_age_s = 1800.0
    lane_lock_stale_s = 120.0

    def __init__(self, adapter_script: str):
        self.python_executable = sys.executable
        self.targets = {"copilot": {}, "gemini": {}}
        self.enabled_targets = ["copilot", "gemini"]
        self.target_health_file = ""
        self.worker_adapters = {
            "dummy_adapter": {
                "command": "\"{python}\" \"{adapter_script}\" \"{request_file}\" \"{response_file}\"",
                "command_vars": {"adapter_script": adapter_script},
                "timeout_s": 20,
                "poll_interval_s": 0.1,
            }
        }


class TestJobRunnerWorkerContract(unittest.TestCase):
    def test_worker_contract_step_writes_output_and_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter_script = os.path.join(temp_dir, "adapter.py")
            with open(adapter_script, "w", encoding="utf-8") as handle:
                handle.write(
                    "import json, sys\n"
                    "request_path, response_path = sys.argv[1], sys.argv[2]\n"
                    "with open(request_path, 'r', encoding='utf-8') as r:\n"
                    "    payload = json.load(r)\n"
                    "content = payload.get('step', {}).get('content', '')\n"
                    "response = {\n"
                    "    'status': 'ok',\n"
                    "    'output_text': '# Worker Output\\n' + content + '\\n',\n"
                    "    'notes_md': 'notes',\n"
                    "    'diff_patch': 'diff --git a/file b/file',\n"
                    "}\n"
                    "with open(response_path, 'w', encoding='utf-8') as w:\n"
                    "    json.dump(response, w)\n"
                )

            plan = {
                "name": "worker_contract_test",
                "steps": [
                    {
                        "id": "worker_step",
                        "type": "worker_contract",
                        "target": "copilot",
                        "content": "hello from worker",
                        "worker": {"adapter": "dummy_adapter"},
                        "output_file": "outputs/worker.md",
                        "validator": {"type": "sections", "required": ["# Worker Output"]},
                    }
                ],
            }
            with open(os.path.join(temp_dir, "plan.json"), "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)

            runner = JobRunner(_DummySequencer(), _DummyConfig(adapter_script))
            ok = runner.run_job(temp_dir)
            self.assertTrue(ok)

            output_path = os.path.join(temp_dir, "outputs", "worker.md")
            self.assertTrue(os.path.exists(output_path))

            worker_dir = os.path.join(temp_dir, "artifacts", "worker_step", "attempt_1_worker_contract")
            self.assertTrue(os.path.exists(os.path.join(worker_dir, "request.json")))
            self.assertTrue(os.path.exists(os.path.join(worker_dir, "response.json")))
            self.assertTrue(os.path.exists(os.path.join(worker_dir, "notes.md")))
            self.assertTrue(os.path.exists(os.path.join(worker_dir, "diff.patch")))


if __name__ == "__main__":
    unittest.main()
