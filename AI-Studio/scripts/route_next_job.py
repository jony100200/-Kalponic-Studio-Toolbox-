from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = ROOT / "00_inbox"
WORKERS_DIR = ROOT / "02_workers"
REGISTRY_PATH = ROOT / "config/worker_registry.json"

ELIGIBLE_STATUSES = {"inbox", "brief_ready"}


def load_roles() -> set[str]:
    if not REGISTRY_PATH.exists():
        return {"writer", "artist_comfyui", "programmer", "youtube", "qa"}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return set((data.get("roles") or {}).keys())


def load_job(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def select_job(job_id: str | None) -> tuple[Path, dict] | tuple[None, None]:
    for path in sorted(INBOX_DIR.glob("JOB-*.json")):
        try:
            data = load_job(path)
        except Exception:  # noqa: BLE001 - utility script
            continue

        current_id = data.get("job_id") or path.stem
        if job_id and current_id != job_id and path.stem != job_id:
            continue

        if job_id:
            return path, data

        status = str(data.get("status", "")).strip().lower()
        if status in ELIGIBLE_STATUSES:
            return path, data

    return None, None


def unique_dispatch_path(role: str, job_id: str) -> Path:
    inbox = WORKERS_DIR / role / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    base = inbox / f"{job_id}.json"
    if not base.exists():
        return base

    idx = 2
    while True:
        candidate = inbox / f"{job_id}_r{idx}.json"
        if not candidate.exists():
            return candidate
        idx += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Route the next pending job card to the worker queue.")
    parser.add_argument("--job-id", help="Optional explicit job ID to route")
    parser.add_argument("--dry-run", action="store_true", help="Preview routing action only")
    args = parser.parse_args()

    roles = load_roles()
    job_path, job = select_job(args.job_id)
    if not job_path or not job:
        target = args.job_id or "(next eligible)"
        print(f"No routable job found for {target}.")
        return 1

    job_id = str(job.get("job_id") or job_path.stem)
    role = str(job.get("role", "")).strip()
    if role not in roles:
        print(f"ERROR: Job {job_id} has unknown role '{role}'.")
        print(f"Known roles: {', '.join(sorted(roles))}")
        return 2

    dispatch_path = unique_dispatch_path(role, job_id)
    dispatched_at = datetime.now().isoformat(timespec="seconds")

    dispatch_payload = dict(job)
    dispatch_payload["dispatch"] = {
        "source_job_card": job_path.relative_to(ROOT).as_posix(),
        "worker_role": role,
        "dispatched_at": dispatched_at,
    }

    if args.dry_run:
        print("Dry run: route plan")
        print(f"- Job: {job_id}")
        print(f"- Role: {role}")
        print(f"- Source: {job_path.relative_to(ROOT)}")
        print(f"- Target queue file: {dispatch_path.relative_to(ROOT)}")
        return 0

    write_json(dispatch_path, dispatch_payload)

    job["status"] = "processing"
    job["routed_at"] = dispatched_at
    job["worker_queue_file"] = dispatch_path.relative_to(ROOT).as_posix()
    write_json(job_path, job)

    print("Routed job successfully:")
    print(f"- Job: {job_id}")
    print(f"- Role: {role}")
    print(f"- Updated source: {job_path.relative_to(ROOT)}")
    print(f"- Worker queue file: {dispatch_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
