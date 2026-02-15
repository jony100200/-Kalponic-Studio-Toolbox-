import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCliInitJobContractMode(unittest.TestCase):
    def test_init_job_defaults_to_worker_contract_and_supports_legacy_flag(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            brief_path = os.path.join(temp_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Build a CLI automation helper.\n")

            result = subprocess.run(
                [
                    sys.executable,
                    "cli.py",
                    "init-job",
                    "--dir",
                    temp_dir,
                    "--brief",
                    "brief.md",
                    "--target",
                    "copilot",
                    "--force",
                ],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )

            plan_path = os.path.join(temp_dir, "plan.json")
            with open(plan_path, "r", encoding="utf-8") as handle:
                plan = json.load(handle)
            first = plan["steps"][0]
            self.assertEqual(first.get("type"), "worker_contract")
            self.assertEqual((first.get("worker") or {}).get("adapter"), "copilot_vscode")

            legacy_result = subprocess.run(
                [
                    sys.executable,
                    "cli.py",
                    "init-job",
                    "--dir",
                    temp_dir,
                    "--brief",
                    "brief.md",
                    "--target",
                    "copilot",
                    "--force",
                    "--legacy-text-steps",
                ],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                legacy_result.returncode,
                0,
                msg=f"stdout:\n{legacy_result.stdout}\n\nstderr:\n{legacy_result.stderr}",
            )

            with open(plan_path, "r", encoding="utf-8") as handle:
                legacy_plan = json.load(handle)
            legacy_first = legacy_plan["steps"][0]
            self.assertEqual(legacy_first.get("type"), "text")
            self.assertNotIn("worker", legacy_first)


if __name__ == "__main__":
    unittest.main()
