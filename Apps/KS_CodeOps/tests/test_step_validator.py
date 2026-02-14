import os
import tempfile
import unittest

from src.core.step_validator import StepValidator


class TestStepValidator(unittest.TestCase):
    def setUp(self):
        self.validator = StepValidator()

    def test_unknown_validator_type_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, "result.md")
            with open(out_file, "w", encoding="utf-8") as handle:
                handle.write("ok")

            step = {
                "output_file": "outputs/result.md",
                "validator": {"type": "mystery"},
            }
            with self.assertRaises(ValueError):
                self.validator.validate_step(temp_dir, step)

    def test_sections_validator_rejects_invalid_required_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = os.path.join(temp_dir, "outputs")
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, "result.md")
            with open(out_file, "w", encoding="utf-8") as handle:
                handle.write("# One\n# Two\n")

            step = {
                "output_file": "outputs/result.md",
                "validator": {"type": "sections", "required": "# One"},
            }
            self.assertFalse(self.validator.validate_step(temp_dir, step))


if __name__ == "__main__":
    unittest.main()
