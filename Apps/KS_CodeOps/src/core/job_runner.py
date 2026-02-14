import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.core.capture_runtime import CaptureRuntime
from src.core.lane_runtime import LaneRuntimeCoordinator
from src.core.multi_lane_dispatcher import MultiLaneDispatcher
from src.core.plan_builder import PlanBuilder
from src.core.runtime_scheduler import RuleBasedTaskScheduler
from src.core.step_validator import StepValidator
from src.core.worker_contract import WorkerContractRuntime


class JobRunner:
    def __init__(self, sequencer, config):
        self.sequencer = sequencer
        self.config = config
        self.capture_runtime = CaptureRuntime(config=self.config, artifacts_dir_provider=self._artifacts_dir)
        self.step_validator = StepValidator()
        self.worker_contract = WorkerContractRuntime(config=self.config)

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
        return self.step_validator.validate_step(job_dir, step)

    def _extract_output_blocks(self, content: str) -> List[str]:
        return self.capture_runtime.extract_output_blocks(content)

    def _capture_source_text(self, job_dir: str, step: Dict[str, Any]) -> str:
        return self.capture_runtime.capture_source_text(job_dir, step)

    def _capture_signature(self, text: str) -> str:
        return self.capture_runtime.capture_signature(text)

    def _default_require_fresh_capture(self, step: Dict[str, Any], source: str) -> bool:
        return self.capture_runtime.default_require_fresh_capture(step, source)

    def _wait_for_completion(self, job_dir: str, step: Dict[str, Any], baseline_signature: str) -> Dict[str, Any]:
        return self.capture_runtime.wait_for_completion(job_dir, step, baseline_signature)

    def _persist_step_artifacts(self, job_dir: str, step: Dict[str, Any], step_id: str, attempt: int) -> Dict[str, Any]:
        return self.capture_runtime.persist_step_artifacts(job_dir, step, step_id, attempt)

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
        return self.capture_runtime.can_capture_fallback(step)

    def _step_output_is_ready(self, job_dir: str, step: Dict[str, Any]) -> bool:
        try:
            return bool(self._validate_step(job_dir, step))
        except Exception:
            return False

    def _parallel_supported(self, steps: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        for step in steps:
            step_type = str(step.get("type", "text")).lower()
            if step_type in {"worker_contract", "validate"}:
                continue
            return False, f"unsupported_step_type:{step_type}"
        return True, None

    def _run_worker_contract_step(
        self,
        job_dir: str,
        step: Dict[str, Any],
        step_id: str,
        attempt: int,
        lane_id: Optional[str],
        target: Optional[str],
    ) -> Dict[str, Any]:
        return self.worker_contract.execute_step(
            job_dir=job_dir,
            step=step,
            step_id=step_id,
            attempt=attempt,
            lane_id=lane_id,
            target=target,
            send_text_fn=self.sequencer.send_text,
            capture_runtime=self.capture_runtime,
            log_fn=lambda message: self._log(job_dir, message),
        )

    def _collect_lane_steps(
        self,
        steps: List[Dict[str, Any]],
        dispatch_plan: Dict[str, Any],
        lane_runtime: LaneRuntimeCoordinator,
    ) -> Dict[str, List[Dict[str, Any]]]:
        steps_by_id = {str(step.get("id")): step for step in steps}
        lane_steps: Dict[str, List[Dict[str, Any]]] = {}

        lanes = dispatch_plan.get("lanes") if isinstance(dispatch_plan.get("lanes"), list) else []
        for lane in lanes:
            lane_id = str(lane.get("id") or "")
            if not lane_id:
                continue
            assigned: List[Dict[str, Any]] = []
            raw_ids = lane.get("step_ids") if isinstance(lane.get("step_ids"), list) else []
            for step_id in raw_ids:
                step = steps_by_id.get(str(step_id))
                if step is not None and step not in assigned:
                    assigned.append(step)
            lane_steps[lane_id] = assigned

        for step in steps:
            step_id = str(step.get("id"))
            lane_id = lane_runtime.lane_for_step(step_id)
            lane_steps.setdefault(lane_id, [])
            if step not in lane_steps[lane_id]:
                lane_steps[lane_id].append(step)

        return lane_steps

    def _run_parallel_worker_lanes(
        self,
        job_dir: str,
        steps: List[Dict[str, Any]],
        status: Dict[str, Any],
        dispatch_plan: Dict[str, Any],
        lane_runtime: LaneRuntimeCoordinator,
    ) -> bool:
        lane_steps = self._collect_lane_steps(steps=steps, dispatch_plan=dispatch_plan, lane_runtime=lane_runtime)
        lane_ids = [lane_id for lane_id, items in lane_steps.items() if items]
        if not lane_ids:
            status["state"] = "completed"
            status["current_step"] = None
            status["current_lane"] = None
            status["finished_at"] = datetime.now().isoformat()
            summary = lane_runtime.finalize_run(job_dir, dispatch_plan, overall_state="completed")
            status["lane_summary_state"] = summary.get("state")
            self._save_status(job_dir, status)
            return True

        status_lock = threading.Lock()
        stop_event = threading.Event()
        failure: Dict[str, Any] = {"step_id": None, "lane_id": None, "error": None}

        status.setdefault("lane_current_steps", {})
        status["lane_current_steps"] = {}

        def _set_failure(step_id: str, lane_id: str, error: str):
            with status_lock:
                if failure["step_id"] is None:
                    failure["step_id"] = step_id
                    failure["lane_id"] = lane_id
                    failure["error"] = error
            stop_event.set()

        def _run_lane(lane_id: str):
            lane_items = lane_steps.get(lane_id, [])
            for step_index, step in enumerate(lane_items):
                if stop_event.is_set():
                    break

                step_id = str(step.get("id"))
                step_state = status["steps"][step_id]
                step_state["lane_id"] = lane_id

                with status_lock:
                    status["current_lane"] = lane_id
                    status["current_step"] = step_id
                    lane_current = status.setdefault("lane_current_steps", {})
                    lane_current[lane_id] = step_id
                    self._save_status(job_dir, status)

                eta_s = self._estimate_eta_seconds(lane_items, step_index)
                self._log(job_dir, f"[PARALLEL] lane={lane_id} step={step_id} eta~{int(eta_s)}s")

                if step_state["state"] == "completed":
                    if self._step_output_is_ready(job_dir, step):
                        self._log(job_dir, f"[PARALLEL] lane={lane_id} skip completed step: {step_id}")
                        continue
                    with status_lock:
                        step_state["state"] = "pending"
                        step_state["attempts"] = 0
                        step_state["last_error"] = "Previously completed output missing/invalid; rerun required"
                        step_state["updated_at"] = datetime.now().isoformat()
                        self._save_status(job_dir, status)

                if step_state["state"] == "failed":
                    with status_lock:
                        step_state["attempts"] = 0
                        step_state["last_error"] = None
                        step_state["updated_at"] = datetime.now().isoformat()
                        self._save_status(job_dir, status)

                max_retries = int(step.get("max_retries", 2))
                step_type = str(step.get("type", "text")).lower()
                target = step.get("target")
                success = False

                for attempt in range(step_state.get("attempts", 0) + 1, max_retries + 2):
                    if stop_event.is_set():
                        break

                    attempt_started = time.time()
                    attempt_success = False
                    attempt_error = None
                    execution_target = target

                    with status_lock:
                        step_state["attempts"] = attempt
                        self._mark_step(step_state, "running")
                        self._save_status(job_dir, status)
                    self._log(job_dir, f"[PARALLEL] lane={lane_id} running {step_id} (attempt {attempt}/{max_retries + 1})")

                    try:
                        if step_type != "validate":
                            resolved_target, reroute_reason = lane_runtime.resolve_target(target, lane_id)
                            if resolved_target:
                                execution_target = resolved_target
                            if reroute_reason and execution_target != target:
                                lane_runtime.record_reroute(
                                    job_dir=job_dir,
                                    lane_id=lane_id,
                                    from_target=str(target),
                                    to_target=str(execution_target),
                                    reason=reroute_reason,
                                )
                                self._log(
                                    job_dir,
                                    f"[HEALTH] Rerouted step {step_id} from {target} to {execution_target} ({reroute_reason})",
                                )

                        lane_runtime.start_step_attempt(
                            job_dir=job_dir,
                            lane_id=lane_id,
                            step_id=step_id,
                            attempt=attempt,
                            target=execution_target,
                        )

                        if step_type == "worker_contract":
                            contract_result = self._run_worker_contract_step(
                                job_dir=job_dir,
                                step=step,
                                step_id=step_id,
                                attempt=attempt,
                                lane_id=lane_id,
                                target=execution_target,
                            )
                            output_written = contract_result.get("output_written")
                            if output_written:
                                self._log(job_dir, f"[WORKER] step={step_id} wrote {output_written}")
                        elif step_type == "validate":
                            pass
                        else:
                            raise RuntimeError(f"Parallel lane executor does not support step type: {step_type}")

                        if not self._validate_step(job_dir, step):
                            raise RuntimeError("Validation failed. Required output artifact not ready.")

                        with status_lock:
                            self._mark_step(step_state, "completed")
                            self._save_status(job_dir, status)
                        self._log(job_dir, f"[PARALLEL] lane={lane_id} completed step: {step_id}")
                        attempt_success = True
                        success = True
                        break

                    except Exception as exc:
                        attempt_error = str(exc)
                        with status_lock:
                            self._mark_step(step_state, "failed", error=attempt_error)
                            self._save_status(job_dir, status)
                        self._log(job_dir, f"[PARALLEL] lane={lane_id} failed step {step_id}: {attempt_error}")
                    finally:
                        lane_runtime.finish_step_attempt(
                            job_dir=job_dir,
                            lane_id=lane_id,
                            step_id=step_id,
                            success=attempt_success,
                            duration_s=max(0.0, time.time() - attempt_started),
                            error=attempt_error,
                        )

                if not success:
                    _set_failure(step_id=step_id, lane_id=lane_id, error=str(step_state.get("last_error") or "failed"))
                    break

            with status_lock:
                lane_current = status.setdefault("lane_current_steps", {})
                lane_current.pop(lane_id, None)
                self._save_status(job_dir, status)

        worker_limit = max(1, min(int(getattr(self.config, "multi_lane_max_lanes", len(lane_ids))), len(lane_ids)))
        with ThreadPoolExecutor(max_workers=worker_limit) as executor:
            futures = [executor.submit(_run_lane, lane_id) for lane_id in lane_ids]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    _set_failure(step_id="unknown", lane_id="unknown", error=str(exc))

        if failure["step_id"] is not None:
            status["state"] = "failed"
            status["failed_step"] = failure["step_id"]
            status["current_lane"] = failure.get("lane_id")
            status["finished_at"] = datetime.now().isoformat()
            summary = lane_runtime.finalize_run(job_dir, dispatch_plan, overall_state="failed")
            status["lane_summary_state"] = summary.get("state")
            self._save_status(job_dir, status)
            self._log(job_dir, f"Job failed at step: {failure['step_id']}")
            return False

        status["state"] = "completed"
        status["current_step"] = None
        status["current_lane"] = None
        status["finished_at"] = datetime.now().isoformat()
        summary = lane_runtime.finalize_run(job_dir, dispatch_plan, overall_state="completed")
        status["lane_summary_state"] = summary.get("state")
        self._save_status(job_dir, status)
        self._log(job_dir, "Job completed successfully")
        return True

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

        scheduler = RuleBasedTaskScheduler(self.config)
        scheduled = scheduler.assign_missing_targets(steps)
        dispatcher = MultiLaneDispatcher(self.config)
        dispatch_plan = dispatcher.build_dispatch_plan(steps)
        if scheduled:
            plan["runtime_assignment_policy"] = scheduler.POLICY_NAME
            for item in scheduled:
                self._log(
                    job_dir,
                    f"[SCHEDULER] step={item['step_id']} target={item['target']} reason={item['reason']}",
                )

        plan["dispatch"] = dispatch_plan
        self._write_json(plan_path, plan)

        lane_runtime = LaneRuntimeCoordinator(self.config)
        lane_context = lane_runtime.initialize(
            job_dir=job_dir,
            dispatch_plan=dispatch_plan,
            step_ids=step_ids,
        )

        status = self._load_status(job_dir, step_ids)
        status["state"] = "running"
        status["mode"] = str(dispatch_plan.get("execution_mode", "single_lane"))
        status["dispatch_mode"] = str(dispatch_plan.get("dispatch_mode", "single_lane"))
        status["dispatch_policy"] = str(dispatch_plan.get("policy", "single_lane_only"))
        status["dispatch_lanes"] = dispatch_plan.get("lanes", [])
        status["dispatch_fallback_reason"] = dispatch_plan.get("fallback_reason")
        status["current_lane"] = None
        status["lanes_root"] = lane_context.get("lanes_root")
        status["lane_summary_file"] = lane_context.get("summary_path")
        status["lane_health"] = lane_context.get("health")
        status.pop("failed_step", None)
        status.pop("finished_at", None)
        self._save_status(job_dir, status)

        self._log(job_dir, f"Job started in {status['mode']} mode: {job_dir}")
        self._log(job_dir, f"[LANES] Runtime directory: {lane_context.get('lanes_root')}")
        if status["dispatch_mode"] == "multi_lane_skeleton":
            self._log(
                job_dir,
                "[DISPATCH] Multi-lane skeleton active; using single-lane fallback executor for safe execution",
            )
        else:
            reason = status.get("dispatch_fallback_reason") or "single_lane"
            self._log(job_dir, f"[DISPATCH] Single-lane dispatch mode ({reason})")
        lane_health = lane_context.get("health") or {}
        if lane_health.get("usable"):
            healthy_targets = lane_health.get("healthy_targets", [])
            self._log(job_dir, f"[HEALTH] Snapshot active ({', '.join(healthy_targets)})")
        else:
            self._log(job_dir, f"[HEALTH] Snapshot unavailable ({lane_health.get('reason', 'unknown')})")

        if status["mode"] == "parallel_lanes":
            supported, reason = self._parallel_supported(steps)
            if supported:
                self._log(job_dir, "[DISPATCH] Parallel lane executor active")
                return self._run_parallel_worker_lanes(
                    job_dir=job_dir,
                    steps=steps,
                    status=status,
                    dispatch_plan=dispatch_plan,
                    lane_runtime=lane_runtime,
                )
            fallback_reason = f"parallel_executor_fallback:{reason}"
            status["mode"] = "single_lane_fallback"
            status["dispatch_fallback_reason"] = fallback_reason
            self._save_status(job_dir, status)
            self._log(job_dir, f"[DISPATCH] Falling back to single-lane executor ({fallback_reason})")

        for step_index, step in enumerate(steps):
            step_id = step["id"]
            lane_id = lane_runtime.lane_for_step(step_id)
            status["current_step"] = step_id
            status["current_lane"] = lane_id
            step_state = status["steps"][step_id]
            step_state["lane_id"] = lane_id
            self._save_status(job_dir, status)

            eta_s = self._estimate_eta_seconds(steps, step_index)
            self._log(job_dir, f"ETA remaining ~{int(eta_s)}s (lane={lane_id})")

            if step_state["state"] == "completed":
                if self._step_output_is_ready(job_dir, step):
                    self._log(job_dir, f"Skipping completed step: {step_id}")
                    continue
                step_state["state"] = "pending"
                step_state["attempts"] = 0
                step_state["last_error"] = "Previously completed output missing/invalid; rerun required"
                step_state["updated_at"] = datetime.now().isoformat()
                self._save_status(job_dir, status)
                self._log(job_dir, f"Completed step output missing/invalid, rerunning: {step_id}")

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
                attempt_started = time.time()
                attempt_success = False
                attempt_error = None
                execution_target = target

                step_state["attempts"] = attempt
                self._mark_step(step_state, "running")
                self._save_status(job_dir, status)
                self._log(job_dir, f"Running step {step_id} (attempt {attempt}/{max_retries + 1})")

                try:
                    if str(step_type).lower() != "validate":
                        resolved_target, reroute_reason = lane_runtime.resolve_target(target, lane_id)
                        if resolved_target:
                            execution_target = resolved_target
                        if reroute_reason and execution_target != target:
                            lane_runtime.record_reroute(
                                job_dir=job_dir,
                                lane_id=lane_id,
                                from_target=str(target),
                                to_target=str(execution_target),
                                reason=reroute_reason,
                            )
                            self._log(
                                job_dir,
                                f"[HEALTH] Rerouted step {step_id} from {target} to {execution_target} ({reroute_reason})",
                            )

                    lane_runtime.start_step_attempt(
                        job_dir=job_dir,
                        lane_id=lane_id,
                        step_id=step_id,
                        attempt=attempt,
                        target=execution_target,
                    )

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
                        sent = self.sequencer.send_text(
                            text,
                            press_enter=bool(step.get("press_enter", True)),
                            target_name=execution_target,
                        )
                        if not sent:
                            send_success = False
                    elif step_type == "image":
                        image_path = step.get("image_path")
                        if not image_path:
                            raise ValueError(f"Step '{step_id}' missing image_path")
                        full_path = os.path.join(job_dir, image_path)
                        sent = self.sequencer.send_image(
                            full_path,
                            press_enter=bool(step.get("press_enter", False)),
                            target_name=execution_target,
                        )
                        if not sent:
                            send_success = False
                    elif step_type == "validate":
                        pass
                    elif step_type == "worker_contract":
                        contract_result = self._run_worker_contract_step(
                            job_dir=job_dir,
                            step=step,
                            step_id=step_id,
                            attempt=attempt,
                            lane_id=lane_id,
                            target=execution_target,
                        )
                        output_written = contract_result.get("output_written")
                        if output_written:
                            self._log(job_dir, f"[WORKER] step={step_id} wrote {output_written}")
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
                    attempt_success = True
                    success = True
                    break

                except Exception as exc:
                    attempt_error = str(exc)
                    self._mark_step(step_state, "failed", error=attempt_error)
                    self._save_status(job_dir, status)
                    self._log(job_dir, f"Step failed: {step_id} | {attempt_error}")
                finally:
                    lane_runtime.finish_step_attempt(
                        job_dir=job_dir,
                        lane_id=lane_id,
                        step_id=step_id,
                        success=attempt_success,
                        duration_s=max(0.0, time.time() - attempt_started),
                        error=attempt_error,
                    )

            if not success:
                status["state"] = "failed"
                status["failed_step"] = step_id
                status["finished_at"] = datetime.now().isoformat()
                status["current_lane"] = lane_id
                summary = lane_runtime.finalize_run(
                    job_dir=job_dir,
                    dispatch_plan=dispatch_plan,
                    overall_state="failed",
                )
                status["lane_summary_state"] = summary.get("state")
                self._save_status(job_dir, status)
                self._log(job_dir, f"Job failed at step: {step_id}")
                return False

        status["state"] = "completed"
        status["current_step"] = None
        status["current_lane"] = None
        status["finished_at"] = datetime.now().isoformat()
        summary = lane_runtime.finalize_run(
            job_dir=job_dir,
            dispatch_plan=dispatch_plan,
            overall_state="completed",
        )
        status["lane_summary_state"] = summary.get("state")
        self._save_status(job_dir, status)
        self._log(job_dir, "Job completed successfully")
        return True
