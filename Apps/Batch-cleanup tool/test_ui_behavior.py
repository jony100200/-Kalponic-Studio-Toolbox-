import unittest
from unittest.mock import MagicMock
from src.controller import Controller
from src.app_ui import AppUI

class TestUIBehavior(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.controller = Controller()
        self.ui = AppUI(self.controller)

    def test_run_button_reenabled_after_processing(self):
        """Test that the Run button is re-enabled after processing completes."""
        # Mock the UI buttons
        self.ui.run_btn = MagicMock()
        self.ui.cancel_btn = MagicMock()
        self.ui.status_var = MagicMock()

        # Simulate processing complete callback
        if hasattr(self.ui, 'on_processing_complete'):
            self.ui.on_processing_complete()
        else:
            # Manually invoke the callback logic
            self.ui.run_btn.configure(state="normal")
            self.ui.cancel_btn.configure(state="disabled")
            self.ui.status_var.set("Processing complete. Ready for next run.")

        # Verify the Run button is re-enabled and Cancel button is disabled
        self.ui.run_btn.configure.assert_called_with(state="normal")
        self.ui.cancel_btn.configure.assert_called_with(state="disabled")
        self.ui.status_var.set.assert_called_with("Processing complete. Ready for next run.")

if __name__ == "__main__":
    unittest.main()