import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class LaneRuntimeCoordinator:
    def __init__(self, config):
        self.config = config
        self._lanes: List[Dict[str, Any]] = []
        self._step_to_lane: Dict[str, str] = {}
        self._lane_targets: Dict[str, str] = {}
        self._health_snapshot: Dict[str, bool] = {}
        self._health_meta: Dict[str, Any] = {}
        self._run_started_at: Optional[datetime] = None

    def _now_iso(self) -> str:
        return datetime.now().isoformat()

    def _lanes_root(self, job_dir: str) -> str:
        return os.path.join(job_dir, "lanes")

    def _lane_dir(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lanes_root(job_dir), lane_id)

    def _lane_worktree_dir(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lane_dir(job_dir, lane_id), "worktree")

    def _lane_artifacts_dir(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lane_dir(job_dir, lane_id), "artifacts")

    def _lane_status_path(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lane_dir(job_dir, lane_id), "status.json")

    def _lane_lock_path(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lane_dir(job_dir, lane_id), "lock.json")

    def _lane_manifest_path(self, job_dir: str, lane_id: str) -> str:
        return os.path.join(self._lane_dir(job_dir, lane_id), "lane.json")

    def summary_path(self, job_dir: str) -> str:
        return os.path.join(job_dir, "lane_summary.json")

    def _parse_iso_datetime(self, value: Any) -> Optional[datetime]:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except Exception:
            return None

    def _read_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: str, payload: Dict[str, Any]):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _normalize_lanes(self, lanes: List[Dict[str, Any]], step_ids: List[str]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for index, lane in enumerate(lanes, start=1):
            lane_id = str(lane.get("id") or f"lane_{index:02d}")
            target = str(lane.get("target") or "single_lane")
            lane_step_ids = []
            raw_step_ids = lane.get("step_ids") if isinstance(lane.get("step_ids"), list) else []
            for step_id in raw_step_ids:
                if step_id is None:
                    continue
                sid = str(step_id)
                if sid and sid not in lane_step_ids:
                    lane_step_ids.append(sid)
            normalized.append({"id": lane_id, "target": target, "step_ids": lane_step_ids})

        if not normalized:
            normalized = [{"id": "lane_01", "target": "single_lane", "step_ids": list(step_ids)}]

        return normalized

    def _build_health_snapshot(self, payload: Dict[str, Any], path: str) -> Tuple[Dict[str, bool], Dict[str, Any]]:
        checked_at = payload.get("checked_at")
        checked_dt = self._parse_iso_datetime(checked_at)
        now = datetime.now()

        max_age_s = float(getattr(self.config, "target_health_max_age_s", 1800.0))
        if checked_dt is None:
            return {}, {"path": path, "usable": False, "reason": "missing_checked_at"}

        age_s = max(0.0, (now - checked_dt).total_seconds())
        if age_s > max_age_s:
            return {}, {
                "path": path,
                "usable": False,
                "reason": "stale_snapshot",
                "checked_at": checked_at,
                "age_s": age_s,
                "max_age_s": max_age_s,
            }

        targets_payload = payload.get("targets")
        if not isinstance(targets_payload, dict):
            return {}, {"path": path, "usable": False, "reason": "invalid_targets_payload"}

        healthy: Dict[str, bool] = {}
        unhealthy: List[str] = []
        for target, value in targets_payload.items():
            name = str(target).strip()
            if not name:
                continue
            if isinstance(value, dict):
                is_healthy = bool(value.get("healthy", False))
            else:
                is_healthy = bool(value)
            if is_healthy:
                healthy[name] = True
            else:
                unhealthy.append(name)

        return healthy, {
            "path": path,
            "usable": bool(healthy),
            "reason": "ok" if healthy else "no_healthy_targets",
            "checked_at": checked_at,
            "age_s": age_s,
            "max_age_s": max_age_s,
            "healthy_targets": sorted(healthy.keys()),
            "unhealthy_targets": sorted(unhealthy),
        }

    def _load_health_snapshot(self, job_dir: str) -> Tuple[Dict[str, bool], Dict[str, Any]]:
        candidate_paths: List[str] = []

        configured = str(getattr(self.config, "target_health_file", "target_health.json")).strip()
        if configured:
            if os.path.isabs(configured):
                candidate_paths.append(configured)
            else:
                candidate_paths.append(os.path.abspath(configured))
                candidate_paths.append(os.path.join(job_dir, configured))

        candidate_paths.append(os.path.join(job_dir, "health_status.json"))

        seen = set()
        deduped_paths = []
        for path in candidate_paths:
            normalized = os.path.normpath(path)
            if normalized in seen:
                continue
            deduped_paths.append(path)
            seen.add(normalized)

        for path in deduped_paths:
            if not os.path.exists(path):
                continue
            try:
                payload = self._read_json(path)
            except Exception:
                return {}, {"path": path, "usable": False, "reason": "invalid_json"}
            if not isinstance(payload, dict):
                return {}, {"path": path, "usable": False, "reason": "invalid_payload"}
            return self._build_health_snapshot(payload, path)

        return {}, {"path": None, "usable": False, "reason": "snapshot_not_found"}

    def _enabled_targets(self) -> List[str]:
        targets = getattr(self.config, "targets", {})
        enabled = getattr(self.config, "enabled_targets", [])
        if not isinstance(enabled, list):
            return []
        return [name for name in enabled if isinstance(name, str) and (not targets or name in targets)]

    def initialize(self, job_dir: str, dispatch_plan: Dict[str, Any], step_ids: List[str]) -> Dict[str, Any]:
        self._run_started_at = datetime.now()
        self._step_to_lane = {}
        self._lane_targets = {}

        raw_lanes = dispatch_plan.get("lanes")
        if not isinstance(raw_lanes, list):
            raw_lanes = []
        self._lanes = self._normalize_lanes(raw_lanes, step_ids)
        primary_lane = self._lanes[0]["id"]

        for lane in self._lanes:
            lane_id = lane["id"]
            self._lane_targets[lane_id] = lane["target"]
            for step_id in lane["step_ids"]:
                if step_id not in self._step_to_lane:
                    self._step_to_lane[step_id] = lane_id

        for step_id in step_ids:
            sid = str(step_id)
            if sid not in self._step_to_lane:
                self._step_to_lane[sid] = primary_lane
                self._lanes[0]["step_ids"].append(sid)

        lanes_root = self._lanes_root(job_dir)
        os.makedirs(lanes_root, exist_ok=True)
        lane_contexts: List[Dict[str, Any]] = []

        for lane in self._lanes:
            lane_id = lane["id"]
            lane_dir = self._lane_dir(job_dir, lane_id)
            worktree_dir = self._lane_worktree_dir(job_dir, lane_id)
            artifacts_dir = self._lane_artifacts_dir(job_dir, lane_id)
            os.makedirs(worktree_dir, exist_ok=True)
            os.makedirs(artifacts_dir, exist_ok=True)

            status_payload = {
                "lane_id": lane_id,
                "target": lane["target"],
                "state": "idle",
                "current_step": None,
                "current_target": None,
                "last_step": None,
                "last_error": None,
                "started_at": self._now_iso(),
                "updated_at": self._now_iso(),
                "metrics": {
                    "steps_total": len(lane["step_ids"]),
                    "steps_completed": 0,
                    "failed_attempts": 0,
                    "attempts_total": 0,
                    "retries_total": 0,
                    "reroutes_total": 0,
                    "duration_s": 0.0,
                },
            }
            self._write_json(self._lane_status_path(job_dir, lane_id), status_payload)
            self._write_json(
                self._lane_manifest_path(job_dir, lane_id),
                {
                    "lane_id": lane_id,
                    "target": lane["target"],
                    "step_ids": lane["step_ids"],
                    "worktree_dir": worktree_dir,
                    "artifacts_dir": artifacts_dir,
                },
            )

            lane_contexts.append(
                {
                    "id": lane_id,
                    "target": lane["target"],
                    "step_ids": lane["step_ids"],
                    "dir": lane_dir,
                    "worktree_dir": worktree_dir,
                    "artifacts_dir": artifacts_dir,
                    "status_file": self._lane_status_path(job_dir, lane_id),
                    "lock_file": self._lane_lock_path(job_dir, lane_id),
                }
            )

        self._health_snapshot, self._health_meta = self._load_health_snapshot(job_dir)

        return {
            "lanes_root": lanes_root,
            "summary_path": self.summary_path(job_dir),
            "lanes": lane_contexts,
            "step_to_lane": dict(self._step_to_lane),
            "health": dict(self._health_meta),
        }

    def lane_for_step(self, step_id: str) -> str:
        sid = str(step_id)
        lane = self._step_to_lane.get(sid)
        if lane:
            return lane
        if self._lanes:
            return self._lanes[0]["id"]
        return "lane_01"

    def _fallback_targets(self, lane_id: str, current_target: str) -> List[str]:
        candidates: List[str] = []
        lane_target = str(self._lane_targets.get(lane_id, "")).strip()
        if lane_target and lane_target != "single_lane":
            candidates.append(lane_target)
        candidates.extend(self._enabled_targets())
        candidates.extend(sorted(self._health_snapshot.keys()))

        deduped: List[str] = []
        for name in candidates:
            if not name or name == current_target:
                continue
            if name not in deduped:
                deduped.append(name)
        return deduped

    def resolve_target(self, step_target: Optional[str], lane_id: str) -> Tuple[Optional[str], Optional[str]]:
        target = str(step_target or "").strip()
        if not target:
            lane_target = str(self._lane_targets.get(lane_id, "")).strip()
            if lane_target and lane_target != "single_lane":
                target = lane_target
        if not target:
            fallback = str(getattr(self.config, "active_target", "")).strip()
            target = fallback if fallback else None

        if not target:
            return None, None
        if not self._health_snapshot:
            return target, None
        if self._health_snapshot.get(target, False):
            return target, None

        for candidate in self._fallback_targets(lane_id, target):
            if self._health_snapshot.get(candidate, False):
                return candidate, f"unhealthy_target:{target}"

        return target, None

    def _lock_is_stale(self, lock_payload: Dict[str, Any]) -> bool:
        acquired = self._parse_iso_datetime(lock_payload.get("acquired_at"))
        if acquired is None:
            return True
        stale_after_s = float(getattr(self.config, "lane_lock_stale_s", 300.0))
        age_s = max(0.0, (datetime.now() - acquired).total_seconds())
        return age_s > stale_after_s

    def acquire_lock(self, job_dir: str, lane_id: str, step_id: str, attempt: int):
        lock_path = self._lane_lock_path(job_dir, lane_id)
        if os.path.exists(lock_path):
            try:
                existing = self._read_json(lock_path)
            except Exception:
                existing = {}
            if isinstance(existing, dict) and not self._lock_is_stale(existing):
                raise RuntimeError(f"Lane lock active: {lane_id}")

        payload = {
            "lane_id": lane_id,
            "step_id": str(step_id),
            "attempt": int(attempt),
            "pid": os.getpid(),
            "acquired_at": self._now_iso(),
        }
        self._write_json(lock_path, payload)

    def release_lock(self, job_dir: str, lane_id: str):
        lock_path = self._lane_lock_path(job_dir, lane_id)
        if os.path.exists(lock_path):
            os.remove(lock_path)

    def _load_lane_status(self, job_dir: str, lane_id: str) -> Dict[str, Any]:
        path = self._lane_status_path(job_dir, lane_id)
        if os.path.exists(path):
            status = self._read_json(path)
        else:
            status = {"lane_id": lane_id, "state": "idle", "metrics": {}}
        if "metrics" not in status or not isinstance(status["metrics"], dict):
            status["metrics"] = {}
        status["metrics"].setdefault("steps_total", 0)
        status["metrics"].setdefault("steps_completed", 0)
        status["metrics"].setdefault("failed_attempts", 0)
        status["metrics"].setdefault("attempts_total", 0)
        status["metrics"].setdefault("retries_total", 0)
        status["metrics"].setdefault("reroutes_total", 0)
        status["metrics"].setdefault("duration_s", 0.0)
        return status

    def _save_lane_status(self, job_dir: str, lane_id: str, status: Dict[str, Any]):
        status["updated_at"] = self._now_iso()
        self._write_json(self._lane_status_path(job_dir, lane_id), status)

    def record_reroute(
        self,
        job_dir: str,
        lane_id: str,
        from_target: str,
        to_target: str,
        reason: str,
    ):
        status = self._load_lane_status(job_dir, lane_id)
        metrics = status["metrics"]
        metrics["reroutes_total"] = int(metrics.get("reroutes_total", 0)) + 1
        status["last_reroute"] = {
            "from_target": from_target,
            "to_target": to_target,
            "reason": reason,
            "at": self._now_iso(),
        }
        self._save_lane_status(job_dir, lane_id, status)

    def start_step_attempt(
        self,
        job_dir: str,
        lane_id: str,
        step_id: str,
        attempt: int,
        target: Optional[str],
    ):
        self.acquire_lock(job_dir, lane_id, step_id, attempt)
        status = self._load_lane_status(job_dir, lane_id)
        metrics = status["metrics"]
        metrics["attempts_total"] = int(metrics.get("attempts_total", 0)) + 1
        if int(attempt) > 1:
            metrics["retries_total"] = int(metrics.get("retries_total", 0)) + 1
        status["state"] = "running"
        status["current_step"] = str(step_id)
        status["current_target"] = str(target) if target else None
        self._save_lane_status(job_dir, lane_id, status)

    def finish_step_attempt(
        self,
        job_dir: str,
        lane_id: str,
        step_id: str,
        success: bool,
        duration_s: float,
        error: Optional[str] = None,
    ):
        status = self._load_lane_status(job_dir, lane_id)
        metrics = status["metrics"]
        metrics["duration_s"] = float(metrics.get("duration_s", 0.0)) + max(0.0, float(duration_s))

        if success:
            metrics["steps_completed"] = int(metrics.get("steps_completed", 0)) + 1
            status["state"] = "idle"
            status["last_error"] = None
        else:
            metrics["failed_attempts"] = int(metrics.get("failed_attempts", 0)) + 1
            status["state"] = "degraded"
            status["last_error"] = str(error) if error else "step_attempt_failed"

        status["last_step"] = str(step_id)
        status["current_step"] = None
        status["current_target"] = None
        self._save_lane_status(job_dir, lane_id, status)
        self.release_lock(job_dir, lane_id)

    def finalize_run(self, job_dir: str, dispatch_plan: Dict[str, Any], overall_state: str) -> Dict[str, Any]:
        finished_at = datetime.now()
        lanes_summary: List[Dict[str, Any]] = []

        for lane in self._lanes:
            lane_id = lane["id"]
            self.release_lock(job_dir, lane_id)
            status = self._load_lane_status(job_dir, lane_id)
            state = str(status.get("state", "idle"))
            if overall_state == "completed" and state in {"idle", "running"}:
                status["state"] = "completed"
            elif overall_state != "completed" and state == "running":
                status["state"] = "degraded"
            self._save_lane_status(job_dir, lane_id, status)
            lanes_summary.append(
                {
                    "lane_id": lane_id,
                    "target": lane.get("target"),
                    "state": status.get("state"),
                    "metrics": status.get("metrics", {}),
                    "status_file": self._lane_status_path(job_dir, lane_id),
                }
            )

        started_at = self._run_started_at or finished_at
        summary = {
            "state": overall_state,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_s": max(0.0, (finished_at - started_at).total_seconds()),
            "dispatch": {
                "mode": dispatch_plan.get("dispatch_mode"),
                "execution_mode": dispatch_plan.get("execution_mode"),
                "policy": dispatch_plan.get("policy"),
                "fallback_reason": dispatch_plan.get("fallback_reason"),
            },
            "health_snapshot": dict(self._health_meta),
            "lanes": lanes_summary,
        }
        self._write_json(self.summary_path(job_dir), summary)
        return summary
