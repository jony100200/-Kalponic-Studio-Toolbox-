from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "00_inbox",
    "01_briefs",
    "02_workers",
    "03_workflows",
    "04_projects",
    "05_assets",
    "06_outputs",
    "07_reviews",
    "08_archive",
    "09_docs",
    "10_logs",
    "config",
    "scripts",
]

REQUIRED_FILES = [
    "config/.env.example",
    "config/worker_registry.json",
    "09_docs/templates/job_card_template.json",
    "09_docs/templates/task_brief_template.md",
    "09_docs/templates/review_checklist.md",
]


def parse_env(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_http(url: str, timeout: float = 2.5) -> tuple[bool, str]:
    if not url:
        return False, "missing"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        return True, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - diagnostic utility
        return False, str(exc)


def main() -> int:
    print("=== AI-Studio Health Check ===")
    print(f"Root: {ROOT}")
    print()

    missing_items = 0

    print("[1/4] Required directories")
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        ok = path.exists() and path.is_dir()
        print(f"  {'OK' if ok else 'MISS'}  {rel}")
        if not ok:
            missing_items += 1
    print()

    print("[2/4] Required files")
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        ok = path.exists() and path.is_file()
        print(f"  {'OK' if ok else 'MISS'}  {rel}")
        if not ok:
            missing_items += 1
    print()

    print("[3/4] Registry sanity")
    registry_path = ROOT / "config/worker_registry.json"
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            roles = sorted((registry.get("roles") or {}).keys())
            print(f"  OK    roles: {', '.join(roles) if roles else '(none)'}")
        except Exception as exc:  # noqa: BLE001 - diagnostic utility
            missing_items += 1
            print(f"  MISS  invalid JSON: {exc}")
    else:
        missing_items += 1
        print("  MISS  config/worker_registry.json not found")
    print()

    print("[4/4] Service endpoints (.env preferred, fallback .env.example)")
    env_values = parse_env(ROOT / "config/.env")
    if not env_values:
        env_values = parse_env(ROOT / "config/.env.example")

    service_keys = ["OLLAMA_BASE_URL", "N8N_BASE_URL", "COMFYUI_BASE_URL"]
    for key in service_keys:
        url = env_values.get(key, "")
        ok, detail = check_http(url) if url else (False, "not configured")
        status = "UP" if ok else "DOWN"
        print(f"  {status:<5} {key}: {url or '(empty)'}  [{detail}]")

    api_key = env_values.get("OPENAI_API_KEY", "")
    print(f"  {'SET' if api_key else 'EMPTY'} OPENAI_API_KEY")
    print()

    if missing_items:
        print(f"Health check finished with {missing_items} missing/invalid item(s).")
        return 1

    print("Health check passed: core studio scaffold is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
