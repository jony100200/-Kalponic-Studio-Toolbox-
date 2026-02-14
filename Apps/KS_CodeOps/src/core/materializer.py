import os
import re
from typing import Dict


class AppMaterializer:
    def _parse_files(self, content: str) -> Dict[str, str]:
        pattern = re.compile(
            r"FILE:\s*(?P<path>[^\n\r]+)\s*\n```[a-zA-Z0-9_+-]*\n(?P<body>.*?)\n```",
            re.DOTALL,
        )
        items: Dict[str, str] = {}
        for match in pattern.finditer(content):
            rel_path = match.group("path").strip().replace("\\", "/")
            body = match.group("body")
            if rel_path:
                items[rel_path] = body
        return items

    def _safe_output_path(self, output_dir: str, rel_path: str) -> str:
        safe_rel_path = os.path.normpath(rel_path)
        if safe_rel_path in {"", ".", ".."}:
            raise ValueError(f"Unsafe path: {rel_path}")
        drive, _ = os.path.splitdrive(safe_rel_path)
        if drive or os.path.isabs(safe_rel_path):
            raise ValueError(f"Unsafe absolute path: {rel_path}")

        output_root = os.path.abspath(output_dir)
        full_path = os.path.abspath(os.path.join(output_root, safe_rel_path))
        try:
            common = os.path.commonpath([output_root, full_path])
        except ValueError as exc:
            raise ValueError(f"Unsafe path: {rel_path}") from exc
        if common != output_root:
            raise ValueError(f"Unsafe relative path: {rel_path}")
        return full_path

    def materialize(self, source_file: str, output_dir: str) -> Dict[str, str]:
        if not os.path.exists(source_file):
            raise FileNotFoundError(source_file)

        with open(source_file, "r", encoding="utf-8") as handle:
            content = handle.read()

        files = self._parse_files(content)
        if not files:
            raise ValueError("No FILE blocks found in source output")

        written: Dict[str, str] = {}
        for rel_path, body in files.items():
            full_path = self._safe_output_path(output_dir=output_dir, rel_path=rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as handle:
                handle.write(body)
            written[rel_path] = full_path

        return written
