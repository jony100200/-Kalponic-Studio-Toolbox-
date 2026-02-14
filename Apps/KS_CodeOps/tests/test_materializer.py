import os
import tempfile
import unittest

from src.core.materializer import AppMaterializer


class TestAppMaterializer(unittest.TestCase):
    def setUp(self):
        self.materializer = AppMaterializer()

    def test_materialize_writes_relative_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "source.md")
            out_dir = os.path.join(temp_dir, "out")
            content = (
                "FILE: app/main.py\n"
                "```python\n"
                "print('hello')\n"
                "```\n"
            )
            with open(source_path, "w", encoding="utf-8") as handle:
                handle.write(content)

            written = self.materializer.materialize(source_file=source_path, output_dir=out_dir)
            expected = os.path.join(out_dir, "app", "main.py")

            self.assertIn("app/main.py", written)
            self.assertTrue(os.path.exists(expected))

    def test_materialize_blocks_absolute_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "source.md")
            out_dir = os.path.join(temp_dir, "out")
            absolute_target = os.path.join(temp_dir, "escape.txt").replace("\\", "/")
            content = (
                f"FILE: {absolute_target}\n"
                "```txt\n"
                "bad\n"
                "```\n"
            )
            with open(source_path, "w", encoding="utf-8") as handle:
                handle.write(content)

            with self.assertRaises(ValueError):
                self.materializer.materialize(source_file=source_path, output_dir=out_dir)

    def test_materialize_blocks_traversal_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "source.md")
            out_dir = os.path.join(temp_dir, "out")
            content = (
                "FILE: ../escape.txt\n"
                "```txt\n"
                "bad\n"
                "```\n"
            )
            with open(source_path, "w", encoding="utf-8") as handle:
                handle.write(content)

            with self.assertRaises(ValueError):
                self.materializer.materialize(source_file=source_path, output_dir=out_dir)


if __name__ == "__main__":
    unittest.main()
