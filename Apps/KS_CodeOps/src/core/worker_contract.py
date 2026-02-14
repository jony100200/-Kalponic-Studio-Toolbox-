import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional


class WorkerContractRuntime:
    def __init__(self, config):
        self.config = config

    def _worker_dir(self, job_dir: str, step_id: str, attempt: int) -> str:
        return os.path.join(job_dir, "artifacts", step_id, f"attempt_{attempt}_worker_contract")

    def _safe_output_path(self, job_dir: str, relative_path: str) -> str:
        if os.path.isabs(relative_path):
            raise ValueError(f"Worker output path must be relative: {relative_path}")
        normalized = os.path.normpath(relative_path)
        if normalized.startswith("..") or os.path.isabs(normalized):
            raise ValueError(f"Worker output path escapes job directory: {relative_path}")
        return os.path.join(job_dir, normalized)

    def _load_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: str, payload: Dict[str, Any]):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _write_text(self, path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def _adapter_defaults(self, adapter_name: str) -> Dict[str, Any]:
        adapters = getattr(self.config, "worker_adapters", None)
        if not isinstance(adapters, dict):
            return {}
        payload = adapters.get(adapter_name)
        return payload if isinstance(payload, dict) else {}

    def _merged_spec(self, step: Dict[str, Any]) -> Dict[str, Any]:
        worker = step.get("worker") or step.get("worker_contract") or {}
        if not isinstance(worker, dict):
            raise ValueError("worker contract payload must be an object")

        adapter = str(worker.get("adapter", "")).strip()
        defaults = self._adapter_defaults(adapter) if adapter else {}
        merged = dict(defaults)
        merged.update(worker)
        if adapter and "adapter" not in merged:
            merged["adapter"] = adapter
        return merged

    def _render_command(self, command_template: str, values: Dict[str, Any]) -> str:
        string_values = {k: str(v) for k, v in values.items()}
        return command_template.format_map(string_values)

    def _run_adapter_command(
        self,
        command: str,
        cwd: str,
        timeout_s: float,
        log_path: str,
        env: Optional[Dict[str, Any]] = None,
    ):
        process_env = os.environ.copy()
        if isinstance(env, dict):
            for key, value in env.items():
                process_env[str(key)] = str(value)

        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=max(1.0, float(timeout_s)),
            env=process_env,
        )

        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(f"command: {command}\n")
            handle.write(f"returncode: {result.returncode}\n\n")
            handle.write("stdout:\n")
            handle.write(result.stdout or "")
            handle.write("\n\nstderr:\n")
            handle.write(result.stderr or "")

        if result.returncode != 0:
            raise RuntimeError(f"Worker adapter command failed ({result.returncode})")

    def _wait_for_response(self, response_file: str, timeout_s: float, poll_interval_s: float):
        start = time.time()
        while (time.time() - start) <= timeout_s:
            if os.path.exists(response_file):
                return
            time.sleep(max(0.1, float(poll_interval_s)))
        raise TimeoutError(f"Timed out waiting for worker response: {response_file}")

    def _resolve_worker_text(self, job_dir: str, step: Dict[str, Any], spec: Dict[str, Any]) -> str:
        if isinstance(spec.get("prompt"), str) and spec.get("prompt").strip():
            return str(spec.get("prompt"))
        if isinstance(step.get("content"), str) and step.get("content").strip():
            return str(step.get("content"))

        prompt_file = step.get("prompt_file")
        if isinstance(prompt_file, str) and prompt_file.strip():
            path = prompt_file if os.path.isabs(prompt_file) else os.path.join(job_dir, prompt_file)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()

        raise ValueError("worker_contract step requires content, worker.prompt, or prompt_file")

    def _merge_capture_step(self, step: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(step)
        capture = merged.get("capture")
        if not isinstance(capture, dict):
            capture = {}
        spec_capture = spec.get("capture")
        if isinstance(spec_capture, dict):
            updated = dict(capture)
            updated.update(spec_capture)
            capture = updated
        merged["capture"] = capture
        return merged

    def _run_vscode_chat_adapter(
        self,
        job_dir: str,
        step: Dict[str, Any],
        spec: Dict[str, Any],
        request_payload: Dict[str, Any],
        response_file: str,
        send_text_fn: Callable[[str, bool, Optional[str], bool], bool],
        capture_runtime: Any,
        log_fn: Optional[Callable[[str], None]] = None,
    ):
        if send_text_fn is None:
            raise ValueError("vscode_chat adapter requires send_text_fn")
        if capture_runtime is None:
            raise ValueError("vscode_chat adapter requires capture_runtime")

        text = self._resolve_worker_text(job_dir=job_dir, step=step, spec=spec)
        step_with_capture = self._merge_capture_step(step=step, spec=spec)

        target = request_payload.get("target")
        if not isinstance(target, str) or not target.strip():
            target = str(spec.get("target", "")).strip() or "copilot"
        press_enter = bool(spec.get("press_enter", step.get("press_enter", True)))
        allow_command_open = bool(spec.get("allow_command_open", False))
        wait_s = float(step.get("wait", spec.get("wait", 0.0)))

        baseline_raw = ""
        can_capture = capture_runtime.can_capture_fallback(step_with_capture)
        if can_capture:
            try:
                baseline_raw = capture_runtime.capture_source_text(job_dir, step_with_capture)
            except Exception:
                baseline_raw = ""
        baseline_signature = capture_runtime.capture_signature(baseline_raw)

        sent = bool(send_text_fn(text, press_enter, target, allow_command_open))
        if not sent:
            raise RuntimeError(f"vscode_chat send failed for target: {target}")

        if wait_s > 0:
            time.sleep(wait_s)

        if can_capture:
            completion = capture_runtime.wait_for_completion(job_dir, step_with_capture, baseline_signature)
            if not completion.get("ready"):
                raise RuntimeError("vscode_chat completion detection timeout")
            capture_result = capture_runtime.persist_step_artifacts(
                job_dir=job_dir,
                step=step_with_capture,
                step_id=str(request_payload.get("step_id") or step.get("id") or "step"),
                attempt=int(request_payload.get("attempt") or 1),
            )
            extracted_file = capture_result.get("extracted_file")
            output_text = ""
            if isinstance(extracted_file, str) and os.path.exists(extracted_file):
                with open(extracted_file, "r", encoding="utf-8") as handle:
                    output_text = handle.read()
        else:
            output_text = ""
            capture_result = {"captured": False}

        response_payload = {
            "status": "ok",
            "adapter": str(spec.get("adapter", "vscode_chat")),
            "target": target,
            "sent": True,
            "captured": bool(capture_result.get("captured", False)),
            "output_text": output_text,
            "meta": {
                "allow_command_open": allow_command_open,
                "press_enter": press_enter,
                "capture_source": (step_with_capture.get("capture") or {}).get("source", "none"),
            },
        }
        self._write_json(response_file, response_payload)

        if log_fn:
            log_fn(
                f"[WORKER] vscode_chat adapter target={target} captured={response_payload['captured']}"
            )

    def execute_step(
        self,
        job_dir: str,
        step: Dict[str, Any],
        step_id: str,
        attempt: int,
        lane_id: Optional[str],
        target: Optional[str],
        send_text_fn: Optional[Callable[[str, bool, Optional[str], bool], bool]] = None,
        capture_runtime: Any = None,
        log_fn: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        spec = self._merged_spec(step)
        adapter = str(spec.get("adapter", "")).strip() or "inline"

        worker_dir = self._worker_dir(job_dir, step_id, attempt)
        os.makedirs(worker_dir, exist_ok=True)

        request_file = os.path.join(worker_dir, str(spec.get("request_file", "request.json")))
        response_file = os.path.join(worker_dir, str(spec.get("response_file", "response.json")))
        notes_file = os.path.join(worker_dir, str(spec.get("notes_file", "notes.md")))
        diff_file = os.path.join(worker_dir, str(spec.get("diff_file", "diff.patch")))
        command_log = os.path.join(worker_dir, "command.log")

        request_payload = {
            "contract_version": 1,
            "created_at": datetime.now().isoformat(),
            "job_dir": job_dir,
            "step_id": step_id,
            "attempt": int(attempt),
            "lane_id": lane_id,
            "target": target,
            "step": step,
        }
        self._write_json(request_file, request_payload)

        mode = str(spec.get("mode", "")).strip().lower()
        if mode in {"vscode_chat", "copilot_vscode_chat"} or adapter in {"copilot_vscode", "copilot_vscode_chat"}:
            self._run_vscode_chat_adapter(
                job_dir=job_dir,
                step=step,
                spec=spec,
                request_payload=request_payload,
                response_file=response_file,
                send_text_fn=send_text_fn,
                capture_runtime=capture_runtime,
                log_fn=log_fn,
            )

        command_template = str(spec.get("command", "")).strip()
        if command_template:
            command_vars = {
                "python": getattr(self.config, "python_executable", "") or "python",
                "job_dir": job_dir,
                "step_id": step_id,
                "attempt": attempt,
                "lane_id": lane_id or "",
                "target": target or "",
                "request_file": request_file,
                "response_file": response_file,
                "notes_file": notes_file,
                "diff_file": diff_file,
                "worker_dir": worker_dir,
            }
            extra_vars = spec.get("command_vars")
            if isinstance(extra_vars, dict):
                for key, value in extra_vars.items():
                    command_vars[str(key)] = value
            command = self._render_command(command_template, command_vars)
            self._run_adapter_command(
                command=command,
                cwd=job_dir,
                timeout_s=float(spec.get("command_timeout_s", spec.get("timeout_s", 120.0))),
                log_path=command_log,
                env=spec.get("env"),
            )

        self._wait_for_response(
            response_file=response_file,
            timeout_s=float(spec.get("timeout_s", 120.0)),
            poll_interval_s=float(spec.get("poll_interval_s", 0.5)),
        )
        response = self._load_json(response_file)

        if not isinstance(response, dict):
            raise ValueError("Worker response must be a JSON object")
        if str(response.get("status", "ok")).lower() not in {"ok", "success"}:
            error = response.get("error") or "worker reported non-success status"
            raise RuntimeError(str(error))

        if isinstance(response.get("notes_md"), str):
            self._write_text(notes_file, response["notes_md"])
        if isinstance(response.get("diff_patch"), str):
            self._write_text(diff_file, response["diff_patch"])

        output_written = None
        output_text = response.get("output_text")
        if isinstance(output_text, str):
            output_file = str(step.get("output_file", "")).strip()
            if output_file:
                out_path = self._safe_output_path(job_dir, output_file)
                self._write_text(out_path, output_text)
                output_written = out_path
            else:
                fallback_out = os.path.join(worker_dir, "output.txt")
                self._write_text(fallback_out, output_text)
                output_written = fallback_out

        output_files = response.get("output_files")
        materialized = []
        if isinstance(output_files, dict):
            for rel_path, content in output_files.items():
                if not isinstance(rel_path, str):
                    continue
                if not isinstance(content, str):
                    continue
                full_path = self._safe_output_path(job_dir, rel_path)
                self._write_text(full_path, content)
                materialized.append(full_path)

        return {
            "captured": True,
            "adapter": adapter,
            "request_file": request_file,
            "response_file": response_file,
            "notes_file": notes_file if os.path.exists(notes_file) else None,
            "diff_file": diff_file if os.path.exists(diff_file) else None,
            "command_log": command_log if os.path.exists(command_log) else None,
            "output_written": output_written,
            "materialized_files": materialized,
        }
