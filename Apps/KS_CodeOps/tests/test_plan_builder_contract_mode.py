import json
import os
import tempfile
import unittest

from src.core.plan_builder import PlanBuilder


class _DummyConfig:
    def __init__(self, worker_adapters):
        self.targets = {"copilot": {}}
        self.enabled_targets = ["copilot"]
        self.active_target = "copilot"
        self.worker_adapters = worker_adapters


class TestPlanBuilderContractMode(unittest.TestCase):
    def _write_brief(self, job_dir: str) -> str:
        brief_path = os.path.join(job_dir, "brief.md")
        with open(brief_path, "w", encoding="utf-8") as handle:
            handle.write("Build a TODO app with auth.\n")
        return brief_path

    def test_prefers_worker_contract_when_target_adapter_exists(self):
        adapters = {
            "copilot_vscode": {
                "mode": "vscode_chat",
                "target": "copilot",
                "allow_command_open": False,
                "capture": {"source": "bridge"},
            }
        }
        config = _DummyConfig(worker_adapters=adapters)

        with tempfile.TemporaryDirectory() as temp_dir:
            brief_path = self._write_brief(temp_dir)
            builder = PlanBuilder(config)
            plan = builder.create_plan(
                job_dir=temp_dir,
                brief_path=brief_path,
                target_name="copilot",
                force=True,
                project_name="contract_mode_test",
            )

            self.assertTrue(plan.get("steps"))
            first = plan["steps"][0]
            self.assertEqual(first.get("type"), "worker_contract")
            self.assertEqual((first.get("worker") or {}).get("adapter"), "copilot_vscode")
            self.assertEqual((first.get("capture") or {}).get("source"), "bridge")

            with open(os.path.join(temp_dir, "plan.json"), "r", encoding="utf-8") as handle:
                persisted = json.load(handle)
            self.assertEqual((persisted["steps"][0].get("worker") or {}).get("adapter"), "copilot_vscode")

    def test_legacy_mode_forces_text_steps(self):
        adapters = {
            "copilot_vscode": {
                "mode": "vscode_chat",
                "target": "copilot",
                "allow_command_open": False,
                "capture": {"source": "bridge"},
            }
        }
        config = _DummyConfig(worker_adapters=adapters)

        with tempfile.TemporaryDirectory() as temp_dir:
            brief_path = self._write_brief(temp_dir)
            builder = PlanBuilder(config)
            plan = builder.create_plan(
                job_dir=temp_dir,
                brief_path=brief_path,
                target_name="copilot",
                force=True,
                project_name="legacy_mode_test",
                prefer_worker_contract=False,
            )

            self.assertTrue(plan.get("steps"))
            first = plan["steps"][0]
            self.assertEqual(first.get("type"), "text")
            self.assertNotIn("worker", first)
            self.assertEqual((first.get("capture") or {}).get("source"), "bridge")


if __name__ == "__main__":
    unittest.main()
