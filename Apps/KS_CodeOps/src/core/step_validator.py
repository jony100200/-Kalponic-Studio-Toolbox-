import json
import os
from typing import Any, Dict


class StepValidator:
    def validate_step(self, job_dir: str, step: Dict[str, Any]) -> bool:
        output_file = step.get("output_file")
        validator = step.get("validator")

        if not output_file or not validator:
            return True

        out_path = os.path.join(job_dir, output_file)
        if not os.path.exists(out_path):
            return False

        vtype = str(validator.get("type", "exists")).strip().lower()

        if vtype == "exists":
            return True

        if vtype == "json":
            try:
                with open(out_path, "r", encoding="utf-8") as handle:
                    json.load(handle)
                return True
            except Exception:
                return False

        if vtype == "sections":
            required = validator.get("required", [])
            if not isinstance(required, list) or any(not isinstance(section, str) for section in required):
                return False
            with open(out_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            return all(section in content for section in required)

        raise ValueError(f"Unsupported validator type: {vtype}")
