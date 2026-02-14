import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCliRunJobExitCode(unittest.TestCase):
    def test_run_job_returns_non_zero_on_failure(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = {
                "name": "cli_exit_test",
                "steps": [
                    {
                        "id": "must_fail",
                        "type": "validate",
                        "output_file": "outputs/missing.md",
                        "validator": {"type": "exists"},
                    }
                ],
            }
            plan_path = os.path.join(temp_dir, "plan.json")
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(plan, handle, indent=2)

            command = [sys.executable, "cli.py", "run-job", "--dir", temp_dir]
            result = subprocess.run(
                command,
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                1,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
