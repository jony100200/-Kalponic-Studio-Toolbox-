from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = ROOT / "00_inbox"
BRIEFS_DIR = ROOT / "01_briefs"
REGISTRY_PATH = ROOT / "config/worker_registry.json"


def load_roles() -> set[str]:
    if not REGISTRY_PATH.exists():
        return {"writer", "artist_comfyui", "programmer", "youtube", "qa"}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return set((data.get("roles") or {}).keys())


def sanitize_title(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r"[^a-z0-9]+", "-", title)
    return title.strip("-") or "task"


def next_job_id(now: datetime) -> str:
    date_part = now.strftime("%Y%m%d")
    existing = sorted(INBOX_DIR.glob(f"JOB-{date_part}-*.json"))
    if not existing:
        seq = 1
    else:
        last = existing[-1].stem
        seq = int(last.split("-")[-1]) + 1
    return f"JOB-{date_part}-{seq:03d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new AI-Studio job card and brief.")
    parser.add_argument("--role", required=True, help="Worker role (writer, artist_comfyui, programmer, youtube, qa)")
    parser.add_argument("--title", required=True, help="Short job title")
    parser.add_argument("--priority", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--owner", default="local_user")
    args = parser.parse_args()

    roles = load_roles()
    if args.role not in roles:
        print(f"ERROR: Unknown role '{args.role}'. Available roles: {', '.join(sorted(roles))}")
        return 2

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    job_id = next_job_id(now)
    title_slug = sanitize_title(args.title)

    job_card = {
        "job_id": job_id,
        "created_at": now.isoformat(timespec="seconds"),
        "owner": args.owner,
        "priority": args.priority,
        "role": args.role,
        "title": args.title,
        "objective": "",
        "inputs": [],
        "constraints": [],
        "output": {
            "format": "md",
            "destination": "06_outputs/drafts",
            "naming": f"{job_id}_{title_slug}_output_v1.md",
        },
        "definition_of_done": [
            "Requirement 1",
            "Requirement 2",
            "QA reviewed",
        ],
        "status": "inbox",
    }

    job_card_path = INBOX_DIR / f"{job_id}.json"
    job_card_path.write_text(json.dumps(job_card, indent=2), encoding="utf-8")

    brief_path = BRIEFS_DIR / f"{job_id}_{title_slug}_brief.md"
    brief_content = f"""# Brief: {args.title}

- Job ID: {job_id}
- Role: {args.role}
- Priority: {args.priority}
- Owner: {args.owner}

## Objective

<!-- Fill in objective -->

## Inputs

- 

## Constraints

- 

## Definition of Done

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] QA reviewed
"""
    brief_path.write_text(brief_content, encoding="utf-8")

    print("Created job files:")
    print(f"- {job_card_path.relative_to(ROOT)}")
    print(f"- {brief_path.relative_to(ROOT)}")
    print("Next: complete the brief, then route to the worker role.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
