import subprocess
import sys
import unittest
from pathlib import Path


class TestCliReleaseCommands(unittest.TestCase):
    def test_version_command_outputs_semver(self):
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "cli.py", "version"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        value = (result.stdout or "").strip()
        parts = value.split(".")
        self.assertEqual(len(parts), 3, msg=f"unexpected version: {value}")
        self.assertTrue(all(part.isdigit() for part in parts), msg=f"unexpected version: {value}")

    def test_smoke_run_command_passes(self):
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "cli.py", "smoke-run"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        self.assertIn("smoke-run: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
