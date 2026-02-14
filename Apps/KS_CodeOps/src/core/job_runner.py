import json
import os
import re
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import pyperclip

from src.core.plan_builder import PlanBuilder


class JobRunner:
    def __init__(self, sequencer, config):
        self.sequencer = sequencer
        self.config = config

    def _status_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "status.json")

    def _log_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "log.txt")

    def _plan_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "plan.json")

    def _brief_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "brief.md")

    def _design_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "design.md")

    def _artifacts_dir(self, job_dir: str, step_id: str) -> str:
        return os.path.join(job_dir, "artifacts", step_id)

    def _read_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: str, payload: Dict[str, Any]):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _log(self, job_dir: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.sequencer._log(line)
        with open(self._log_path(job_dir), "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _load_status(self, job_dir: str, step_ids: List[str]) -> Dict[str, Any]:
        path = self._status_path(job_dir)
        if os.path.exists(path):
            status = self._read_json(path)
        else:
            status = {
                "mode": "single_lane",
                "state": "running",
                "current_step": None,
                "steps": {},
                "started_at": datetime.now().isoformat(),
            }

        if "steps" not in status or not isinstance(status["steps"], dict):
            status["steps"] = {}

        for step_id in step_ids:
            if step_id not in status["steps"]:
                status["steps"][step_id] = {
                    "state": "pending",
                    "attempts": 0,
                    "last_error": None,
                    "updated_at": None,
                }

        return status

    def _save_status(self, job_dir: str, status: Dict[str, Any]):
        self._write_json(self._status_path(job_dir), status)

    def _get_step_text(self, job_dir: str, step: Dict[str, Any]) -> str:
        if step.get("content"):
            return str(step["content"])

        prompt_file = step.get("prompt_file")
        if not prompt_file:
            raise ValueError(f"Step '{step.get('id')}' missing content or prompt_file")

        path = os.path.join(job_dir, prompt_file)
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()

    def _validate_step(self, job_dir: str, step: Dict[str, Any]) -> bool:
        output_file = step.get("output_file")
        validator = step.get("validator")

        if not output_file or not validator:
            return True

        out_path = os.path.join(job_dir, output_file)
        if not os.path.exists(out_path):
            return False

        vtype = validator.get("type", "exists")

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
            with open(out_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            return all(section in content for section in required)

        return True

    def _extract_output_blocks(self, content: str) -> List[str]:
        begin = re.escape(self.config.capture_begin_marker)
        end = re.escape(self.config.capture_end_marker)
        pattern = re.compile(rf"{begin}\s*(.*?)\s*{end}", re.DOTALL | re.IGNORECASE)
        return [match.strip() for match in pattern.findall(content) if match.strip()]

    def _capture_source_text(self, job_dir: str, step: Dict[str, Any]) -> str:
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

    def _capture_signature(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""

    def _default_require_fresh_capture(self, step: Dict[str, Any], source: str) -> bool:
        step_type = str(step.get("type", "text")).lower()
        if step_type == "validate":
            return False
        if source in {"file", "none", ""}:
            return False
        return bool(self.config.completion_require_fresh_capture)

    def _wait_for_completion(self, job_dir: str, step: Dict[str, Any], baseline_signature: str) -> Dict[str, Any]:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        if source in ("", "none"):
            return {"ready": True, "reason": "no_capture"}

        completion = step.get("completion") or {}
        timeout_s = float(completion.get("timeout_s", self.config.completion_timeout_s))
        poll_s = float(completion.get("poll_interval_s", self.config.completion_poll_interval_s))
        default_fresh = self._default_require_fresh_capture(step, source)
        require_fresh = bool(completion.get("require_fresh_capture", default_fresh))

        start = time.time()
        last_signature = baseline_signature
        while (time.time() - start) <= timeout_s:
            raw = self._capture_source_text(job_dir, step)
            signature = self._capture_signature(raw)
            blocks = self._extract_output_blocks(raw)
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

    def _persist_step_artifacts(self, job_dir: str, step: Dict[str, Any], step_id: str, attempt: int) -> Dict[str, Any]:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        if source in ("", "none"):
            return {"captured": False}

        raw = self._capture_source_text(job_dir, step)
        blocks = self._extract_output_blocks(raw)
        extracted = "\n\n".join(blocks).strip() if blocks else raw.strip()

        step_artifacts = self._artifacts_dir(job_dir, step_id)
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

    def _estimate_eta_seconds(self, steps: List[Dict[str, Any]], start_index: int) -> float:
        total = 0.0
        for future_step in steps[start_index:]:
            completion = future_step.get("completion") or {}
            total += float(future_step.get("wait", 0))
            total += float(completion.get("timeout_s", self.config.eta_step_seconds))
        return total

    def _mark_step(self, step_state: Dict[str, Any], state: str, error: Optional[str] = None):
        step_state["state"] = state
        step_state["last_error"] = error
        step_state["updated_at"] = datetime.now().isoformat()

    def _can_capture_fallback(self, step: Dict[str, Any]) -> bool:
        capture = step.get("capture") or {}
        source = str(capture.get("source", "none")).lower()
        return source in {"bridge", "file", "clipboard"}

    def run_job(self, job_dir: str):
        plan_path = self._plan_path(job_dir)
        if not os.path.exists(plan_path):
            brief_path = self._brief_path(job_dir)
            if os.path.exists(brief_path):
                builder = PlanBuilder(self.config)
                design_path = self._design_path(job_dir)
                design_arg = design_path if os.path.exists(design_path) else None
                builder.create_plan(
                    job_dir=job_dir,
                    brief_path=brief_path,
                    design_path=design_arg,
                    target_name=self.config.active_target,
                    force=False,
                    project_name=os.path.basename(job_dir),
                )
                self._log(job_dir, "Auto-generated plan.json from brief.md")

        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Missing plan.json in {job_dir}")

        plan = self._read_json(plan_path)
        steps = plan.get("steps") if isinstance(plan, dict) else None
        if not isinstance(steps, list) or not steps:
            raise ValueError("plan.json must contain a non-empty 'steps' array")

        step_ids = []
        for idx, step in enumerate(steps, start=1):
            step_id = step.get("id") or f"step_{idx}"
            step["id"] = step_id
            step_ids.append(step_id)

        status = self._load_status(job_dir, step_ids)
        self._save_status(job_dir, status)

        self._log(job_dir, f"Job started in single_lane mode: {job_dir}")

        for step_index, step in enumerate(steps):
            step_id = step["id"]
            status["current_step"] = step_id
            step_state = status["steps"][step_id]

            eta_s = self._estimate_eta_seconds(steps, step_index)
            self._log(job_dir, f"ETA remaining ~{int(eta_s)}s")

            if step_state["state"] == "completed":
                self._log(job_dir, f"Skipping completed step: {step_id}")
                continue

            if step_state["state"] == "failed":
                step_state["attempts"] = 0
                step_state["last_error"] = None
                step_state["updated_at"] = datetime.now().isoformat()
                self._save_status(job_dir, status)
                self._log(job_dir, f"Resetting failed step for fresh retry: {step_id}")

            max_retries = int(step.get("max_retries", 2))
            step_type = step.get("type", "text")
            target = step.get("target")

            success = False
            for attempt in range(step_state.get("attempts", 0) + 1, max_retries + 2):
                step_state["attempts"] = attempt
                self._mark_step(step_state, "running")
                self._save_status(job_dir, status)
                self._log(job_dir, f"Running step {step_id} (attempt {attempt}/{max_retries + 1})")

                try:
                    baseline_raw = ""
                    if self._can_capture_fallback(step):
                        try:
                            baseline_raw = self._capture_source_text(job_dir, step)
                        except Exception:
                            baseline_raw = ""
                    baseline_signature = self._capture_signature(baseline_raw)

                    send_success = True
                    if step_type == "text":
                        text = self._get_step_text(job_dir, step)
                        sent = self.sequencer.send_text(text, press_enter=bool(step.get("press_enter", True)), target_name=target)
                        if not sent:
                            send_success = False
                    elif step_type == "image":
                        image_path = step.get("image_path")
                        if not image_path:
                            raise ValueError(f"Step '{step_id}' missing image_path")
                        full_path = os.path.join(job_dir, image_path)
                        sent = self.sequencer.send_image(full_path, press_enter=bool(step.get("press_enter", False)), target_name=target)
                        if not sent:
                            send_success = False
                    elif step_type == "validate":
                        pass
                    else:
                        raise ValueError(f"Unsupported step type: {step_type}")

                    if not send_success:
                        if self._can_capture_fallback(step):
                            self._log(
                                job_dir,
                                f"Send failed for {step_id}, continuing with capture fallback ({(step.get('capture') or {}).get('source')})",
                            )
                        else:
                            raise RuntimeError("send failed and no capture fallback is configured")

                    wait_s = float(step.get("wait", 0))
                    if wait_s > 0:
                        time.sleep(wait_s)

                    completion_result = self._wait_for_completion(job_dir, step, baseline_signature)
                    if not completion_result.get("ready") and self._can_capture_fallback(step):
                        raise RuntimeError("Completion detection timeout: prompt may not be finished")

                    capture_result = self._persist_step_artifacts(job_dir, step, step_id, attempt)
                    if capture_result.get("captured"):
                        self._log(
                            job_dir,
                            f"Captured output for {step_id}: blocks={capture_result.get('block_count', 0)}",
                        )

                    if not self._validate_step(job_dir, step):
                        raise RuntimeError("Validation failed. Required output artifact not ready.")

                    self._mark_step(step_state, "completed")
                    self._save_status(job_dir, status)
                    self._log(job_dir, f"Step completed: {step_id}")
                    success = True
                    break

                except Exception as exc:
                    error = str(exc)
                    self._mark_step(step_state, "failed", error=error)
                    self._save_status(job_dir, status)
                    self._log(job_dir, f"Step failed: {step_id} | {error}")

            if not success:
                status["state"] = "failed"
                status["failed_step"] = step_id
                status["finished_at"] = datetime.now().isoformat()
                self._save_status(job_dir, status)
                self._log(job_dir, f"Job failed at step: {step_id}")
                return False

        status["state"] = "completed"
        status["current_step"] = None
        status["finished_at"] = datetime.now().isoformat()
        self._save_status(job_dir, status)
        self._log(job_dir, "Job completed successfully")
        return True
