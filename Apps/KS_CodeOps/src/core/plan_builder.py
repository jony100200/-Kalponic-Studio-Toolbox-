import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class PlanBuilder:
    def __init__(self, config):
        self.config = config

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

        target = target_name or self.config.active_target
        steps: List[Dict[str, Any]] = []

        os.makedirs(prompts_dir, exist_ok=True)

        for index, phase_title in enumerate(phases, start=1):
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

            steps.append(
                {
                    "id": f"step_{index:02d}_{slug}",
                    "type": "text",
                    "target": target,
                    "prompt_file": os.path.join("prompts", prompt_filename).replace("\\", "/"),
                    "press_enter": True,
                    "wait": 4,
                    "max_retries": 2,
                    "capture": {"source": "bridge"},
                    "output_file": f"outputs/{index:02d}_{slug}.md",
                    "validator": {"type": "exists"},
                }
            )

        plan = {
            "name": project_name,
            "created_at": datetime.now().isoformat(),
            "source": {
                "brief": os.path.basename(brief_path),
                "design": os.path.basename(design_path) if design_path else None,
            },
            "steps": steps,
        }

        self._write_json(plan_path, plan)
        return plan
