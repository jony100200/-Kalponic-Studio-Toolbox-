import unittest

from src.core.sequencer import VSCodeSequencer


class _DummyAutomation:
    pass


class _DummyConfig:
    def __init__(self):
        self.targets = {
            "copilot": {"command_open_in_test": False},
            "gemini": {"command_open_in_test": True},
        }
        self.enabled_targets = ["copilot", "gemini"]
        self.active_target = "gemini"
        self.target_settle_delay_s = 0.0
        self.auto_enter = False

    def save(self):
        return None


class TestSequencerConfigMutation(unittest.TestCase):
    def test_test_sequence_restores_config_state(self):
        config = _DummyConfig()
        sequencer = VSCodeSequencer(_DummyAutomation(), config)

        original_enabled = list(config.enabled_targets)
        original_active = config.active_target

        def _fake_send_text(*_args, **_kwargs):
            return True

        sequencer.send_text = _fake_send_text
        results = sequencer.run_target_test_sequence(
            targets=["copilot"],
            delay_between_s=0.0,
            text_prefix="TEST",
            allow_command_open=True,
        )

        self.assertTrue(results.get("copilot"))
        self.assertEqual(config.enabled_targets, original_enabled)
        self.assertEqual(config.active_target, original_active)


if __name__ == "__main__":
    unittest.main()
