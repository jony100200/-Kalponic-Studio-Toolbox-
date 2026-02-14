import hashlib
import os
import re
import time
from typing import Any, Callable, Dict, List

import pyperclip


class CaptureRuntime:
    def __init__(self, config, artifacts_dir_provider: Callable[[str, str], str]):
        self.config = config
        self.artifacts_dir_provider = artifacts_dir_provider

    def extract_output_blocks(self, content: str) -> List[str]:
        begin = re.escape(self.config.capture_begin_marker)
        end = re.escape(self.config.capture_end_marker)
        pattern = re.compile(rf"{begin}\s*(.*?)\s*{end}", re.DOTALL | re.IGNORECASE)
        return [match.strip() for match in pattern.findall(content) if match.strip()]

    def capture_source_text(self, job_dir: str, step: Dict[str, Any]) -> str:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()

        if source in ("", "none"):
            return ""

        if source == "clipboard":
            return pyperclip.paste() or ""

        if source == "file":
            path = capture.get("path")
            if not path:
                raise ValueError("capture.source=file requires capture.path")
            full_path = path if os.path.isabs(path) else os.path.join(job_dir, path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(full_path)
            with open(full_path, "r", encoding="utf-8") as handle:
                return handle.read()

        if source == "bridge":
            path = capture.get("path") or self.config.bridge_response_file
            if os.path.isabs(path):
                full_path = path
            else:
                full_path = os.path.join(job_dir, path)
                if not os.path.exists(full_path):
                    full_path = os.path.join(os.getcwd(), path)
            if not os.path.exists(full_path):
                return ""
            with open(full_path, "r", encoding="utf-8") as handle:
                return handle.read()

        raise ValueError(f"Unsupported capture source: {source}")

    def capture_signature(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""

    def default_require_fresh_capture(self, step: Dict[str, Any], source: str) -> bool:
        step_type = str(step.get("type", "text")).lower()
        if step_type == "validate":
            return False
        if source in {"file", "none", ""}:
            return False
        return bool(self.config.completion_require_fresh_capture)

    def can_capture_fallback(self, step: Dict[str, Any]) -> bool:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        return source in {"bridge", "file", "clipboard"}

    def wait_for_completion(self, job_dir: str, step: Dict[str, Any], baseline_signature: str) -> Dict[str, Any]:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        if source in ("", "none"):
            return {"ready": True, "reason": "no_capture"}

        completion = step.get("completion") or {}
        timeout_s = float(completion.get("timeout_s", self.config.completion_timeout_s))
        poll_s = float(completion.get("poll_interval_s", self.config.completion_poll_interval_s))
        default_fresh = self.default_require_fresh_capture(step, source)
        require_fresh = bool(completion.get("require_fresh_capture", default_fresh))

        start = time.time()
        last_signature = baseline_signature
        while (time.time() - start) <= timeout_s:
            raw = self.capture_source_text(job_dir, step)
            signature = self.capture_signature(raw)
            blocks = self.extract_output_blocks(raw)
            extracted = "\n\n".join(blocks).strip() if blocks else raw.strip()

            if extracted:
                if require_fresh:
                    if signature and signature != baseline_signature and signature != last_signature:
                        return {"ready": True, "raw": raw, "extracted": extracted, "blocks": len(blocks)}
                else:
                    return {"ready": True, "raw": raw, "extracted": extracted, "blocks": len(blocks)}

            last_signature = signature
            time.sleep(max(0.1, poll_s))

        return {"ready": False, "reason": "timeout"}

    def persist_step_artifacts(self, job_dir: str, step: Dict[str, Any], step_id: str, attempt: int) -> Dict[str, Any]:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        if source in ("", "none"):
            return {"captured": False}

        raw = self.capture_source_text(job_dir, step)
        blocks = self.extract_output_blocks(raw)
        extracted = "\n\n".join(blocks).strip() if blocks else raw.strip()

        step_artifacts = self.artifacts_dir_provider(job_dir, step_id)
        os.makedirs(step_artifacts, exist_ok=True)

        raw_file = os.path.join(step_artifacts, f"attempt_{attempt}_raw.txt")
        with open(raw_file, "w", encoding="utf-8") as handle:
            handle.write(raw)

        extracted_file = os.path.join(step_artifacts, f"attempt_{attempt}_extracted.txt")
        with open(extracted_file, "w", encoding="utf-8") as handle:
            handle.write(extracted)

        output_file = step.get("output_file")
        output_written = None
        if output_file and extracted:
            out_path = os.path.join(job_dir, output_file)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write(extracted)
            output_written = out_path

        return {
            "captured": True,
            "raw_file": raw_file,
            "extracted_file": extracted_file,
            "block_count": len(blocks),
            "output_written": output_written,
        }
