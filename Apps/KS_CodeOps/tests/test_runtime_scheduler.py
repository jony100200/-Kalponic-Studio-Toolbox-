import unittest

from src.core.runtime_scheduler import RuleBasedTaskScheduler


class _DummyConfig:
    def __init__(self):
        self.targets = {
            "copilot": {},
            "gemini": {},
            "codex": {},
            "cline": {},
        }
        self.enabled_targets = ["copilot", "gemini", "codex", "cline"]
        self.active_target = "copilot"


class TestRuntimeScheduler(unittest.TestCase):
    def test_assigns_missing_targets_by_rules(self):
        scheduler = RuleBasedTaskScheduler(_DummyConfig())
        steps = [
            {"id": "step_research", "type": "text"},
            {"id": "step_design", "type": "text"},
            {"id": "step_build", "type": "text"},
            {"id": "step_qa", "type": "text"},
        ]

        assignments = scheduler.assign_missing_targets(steps)
        self.assertEqual(len(assignments), 4)
        self.assertEqual(steps[0]["target"], "copilot")
        self.assertEqual(steps[1]["target"], "gemini")
        self.assertEqual(steps[2]["target"], "codex")
        self.assertEqual(steps[3]["target"], "cline")

    def test_keeps_existing_targets_and_skips_validate_steps(self):
        scheduler = RuleBasedTaskScheduler(_DummyConfig())
        steps = [
            {"id": "step_existing", "type": "text", "target": "copilot"},
            {"id": "step_validate", "type": "validate"},
            {"id": "step_new", "type": "text"},
        ]

        assignments = scheduler.assign_missing_targets(steps)
        self.assertEqual(len(assignments), 1)
        self.assertEqual(steps[0]["target"], "copilot")
        self.assertNotIn("target", steps[1])
        self.assertIn("target", steps[2])


if __name__ == "__main__":
    unittest.main()
