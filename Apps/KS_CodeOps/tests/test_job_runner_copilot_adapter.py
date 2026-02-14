import json
import os
import tempfile
import unittest
from datetime import datetime

from src.core.job_runner import JobRunner


class _BridgeSequencer:
    def __init__(self, job_dir: str, bridge_rel_path: str):
        self.job_dir = job_dir
        self.bridge_rel_path = bridge_rel_path
        self.calls = []

    def _log(self, _message: str):
        return None

    def send_text(self, text: str, press_enter: bool, target_name=None, allow_command_open: bool = True):
        self.calls.append(
            {
                "text": text,
                "press_enter": bool(press_enter),
                "target_name": target_name,
                "allow_command_open": bool(allow_command_open),
            }
        )
        bridge_full = os.path.join(self.job_dir, self.bridge_rel_path)
        os.makedirs(os.path.dirname(bridge_full), exist_ok=True)
        payload = (
            "BEGIN_OUTPUT\n"
            "# Copilot Output\n"
            f"{text}\n"
            f"timestamp={datetime.now().isoformat()}\n"
            "END_OUTPUT\n"
        )
        with open(bridge_full, "w", encoding="utf-8") as handle:
            handle.write(payload)
        return True

    def send_image(self, _image_path: str, press_enter: bool, target_name=None, allow_command_open: bool = True):
        return True


class _DummyConfig:
    eta_step_seconds = 8.0
    active_target = "copilot"
    completion_timeout_s = 20.0
    completion_poll_interval_s = 0.1
    completion_require_fresh_capture = True
    capture_begin_marker = "BEGIN_OUTPUT"
    capture_end_marker = "END_OUTPUT"
    multi_lane_enabled = False
    multi_lane_parallel = False
    multi_lane_max_lanes = 2
    target_health_max_age_s = 1800.0
    lane_lock_stale_s = 120.0
    python_executable = "python"

    def __init__(self, bridge_rel_path: str):
        self.bridge_response_file = bridge_rel_path
        self.target_health_file = ""
        self.targets = {"copilot": {}, "gemini": {}}
        self.enabled_targets = ["copilot", "gemini"]
        self.worker_adapters = {
            "copilot_vscode": {
                "mode": "vscode_chat",
                "target": "copilot",
                "allow_command_open": False,
                "press_enter": True,
                "capture": {"source": "bridge"},
                "timeout_s": 20.0,
                "poll_interval_s": 0.1,
            }
        }


class TestJobRunnerCopilotAdapter(unittest.TestCase):
    def test_copilot_vscode_adapter_uses_bridge_capture_and_contract_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_rel = os.path.join(".ks_codeops", "bridge", "latest_response.txt")
            sequencer = _BridgeSequencer(job_dir=temp_dir, bridge_rel_path=bridge_rel)
            config = _DummyConfig(bridge_rel_path=bridge_rel)

            plan = {
                "name": "copilot_adapter_test",
                "steps": [
                    {
                        "id": "copilot_worker",
                        "type": "worker_contract",
                        "target": "copilot",
                        "content": "Implement health summary",
                        "worker": {"adapter": "copilot_vscode"},
                        "output_file": "outputs/copilot_worker.md",
                        "validator": {"type": "sections", "required": ["# Copilot Output"]},
                    }
                ],
            }
            with open(os.path.join(temp_dir, "plan.json"), "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)

            runner = JobRunner(sequencer=sequencer, config=config)
            ok = runner.run_job(temp_dir)
            self.assertTrue(ok)

            self.assertTrue(sequencer.calls)
            call = sequencer.calls[0]
            self.assertEqual(call["target_name"], "copilot")
            self.assertFalse(call["allow_command_open"])
            self.assertTrue(call["press_enter"])

            output_path = os.path.join(temp_dir, "outputs", "copilot_worker.md")
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as handle:
                output = handle.read()
            self.assertIn("# Copilot Output", output)

            worker_dir = os.path.join(temp_dir, "artifacts", "copilot_worker", "attempt_1_worker_contract")
            response_path = os.path.join(worker_dir, "response.json")
            self.assertTrue(os.path.exists(os.path.join(worker_dir, "request.json")))
            self.assertTrue(os.path.exists(response_path))
            with open(response_path, "r", encoding="utf-8") as handle:
                response = json.load(handle)
            self.assertEqual(response.get("status"), "ok")
            self.assertEqual(response.get("target"), "copilot")


if __name__ == "__main__":
    unittest.main()
