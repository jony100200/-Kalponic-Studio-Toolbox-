import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.assignment_policy import TargetAssignmentPolicy


class PlanBuilder:
    def __init__(self, config):
        self.config = config
        self.assignment_policy = TargetAssignmentPolicy(config)

    def _worker_adapter_for_target(self, target_name: str) -> Optional[str]:
        target = str(target_name or "").strip()
        if not target:
            return None
        adapters = getattr(self.config, "worker_adapters", None)
        if not isinstance(adapters, dict):
            return None
        candidate = f"{target}_vscode"
        if isinstance(adapters.get(candidate), dict):
            return candidate
        return None

    def _is_vscode_chat_adapter(self, adapter_name: str) -> bool:
        adapters = getattr(self.config, "worker_adapters", None)
        if not isinstance(adapters, dict):
            return False
        payload = adapters.get(adapter_name)
        if not isinstance(payload, dict):
            return False
        mode = str(payload.get("mode", "")).strip().lower()
        return mode in {"vscode_chat", "copilot_vscode_chat"}

    def _read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()

    def _write_text(self, path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def _write_json(self, path: str, payload: Dict[str, Any]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _extract_phases(self, design_text: str) -> List[str]:
        phases: List[str] = []
        for line in design_text.splitlines():
            line = line.strip()
            if line.startswith("##") and "PHASE" in line.upper():
                clean = re.sub(r"[*#`]+", "", line).strip(" -")
                if clean and clean not in phases:
                    phases.append(clean)
        return phases

    def _phase_slug(self, text: str) -> str:
        text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
        return text[:48] if text else "phase"

    def _build_prompt(self, brief: str, step_title: str, phase_context: str, project_name: str) -> str:
        return (
            f"Project: {project_name}\n"
            f"Step: {step_title}\n"
            f"Phase Context: {phase_context}\n\n"
            "Use the brief below as the source of truth.\n"
            "Return practical implementation output only.\n"
            "Format your response inside this exact wrapper:\n"
            "BEGIN_OUTPUT\n"
            "<content>\n"
            "END_OUTPUT\n\n"
            "Brief:\n"
            f"{brief}\n"
        )

    def create_plan(
        self,
        job_dir: str,
        brief_path: str,
        design_path: Optional[str] = None,
        target_name: Optional[str] = None,
        force: bool = False,
        project_name: str = "KS CodeOps Job",
        prefer_worker_contract: bool = True,
    ) -> Dict[str, Any]:
        if not os.path.exists(brief_path):
            raise FileNotFoundError(f"Missing brief file: {brief_path}")

        plan_path = os.path.join(job_dir, "plan.json")
        prompts_dir = os.path.join(job_dir, "prompts")

        if os.path.exists(plan_path) and not force:
            raise FileExistsError("plan.json already exists. Use force=True to overwrite.")

        brief = self._read_text(brief_path)

        phases: List[str] = []
        if design_path and os.path.exists(design_path):
            phases = self._extract_phases(self._read_text(design_path))

        if not phases:
            phases = [
                "Phase 1 - Discovery and Constraints",
                "Phase 2 - Architecture and Module Plan",
                "Phase 3 - Implementation Breakdown",
                "Phase 4 - QA, Packaging, and Launch Checklist",
            ]

        assignment_context = self.assignment_policy.assignment_pool(target_name or "")
        target_pool = assignment_context["pool"]
        assignment_policy = assignment_context["policy"]

        steps: List[Dict[str, Any]] = []

        os.makedirs(prompts_dir, exist_ok=True)

        for index, phase_title in enumerate(phases, start=1):
            assignment = self.assignment_policy.select_for_phase(phase_title, index, target_pool)
            slug = self._phase_slug(phase_title)
            prompt_filename = f"{index:02d}_{slug}.md"
            prompt_path = os.path.join(prompts_dir, prompt_filename)
            prompt_text = self._build_prompt(
                brief=brief,
                step_title=phase_title,
                phase_context=phase_title,
                project_name=project_name,
            )
            self._write_text(prompt_path, prompt_text)

            prompt_file_rel = os.path.join("prompts", prompt_filename).replace("\\", "/")
            step_payload: Dict[str, Any] = {
                "id": f"step_{index:02d}_{slug}",
                "target": assignment.target,
                "assignment_reason": assignment.reason,
                "prompt_file": prompt_file_rel,
                "press_enter": True,
                "wait": 4,
                "max_retries": 2,
                "output_file": f"outputs/{index:02d}_{slug}.md",
                "validator": {"type": "exists"},
            }

            adapter_name = self._worker_adapter_for_target(assignment.target) if prefer_worker_contract else None
            if adapter_name:
                step_payload["type"] = "worker_contract"
                step_payload["worker"] = {"adapter": adapter_name}
                if self._is_vscode_chat_adapter(adapter_name):
                    step_payload["capture"] = {"source": "bridge"}
            else:
                step_payload["type"] = "text"
                step_payload["capture"] = {"source": "bridge"}

            steps.append(step_payload)

        plan = {
            "name": project_name,
            "created_at": datetime.now().isoformat(),
            "source": {
                "brief": os.path.basename(brief_path),
                "design": os.path.basename(design_path) if design_path else None,
            },
            "assignment_policy": assignment_policy,
            "steps": steps,
        }

        self._write_json(plan_path, plan)
        return plan
