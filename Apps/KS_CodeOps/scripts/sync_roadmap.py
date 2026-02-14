import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


CHECKBOX_RE = re.compile(r"^(?P<prefix>\s*-\s*\[)(?P<state>[ xX])(?P<suffix>\]\s+)(?P<item>.+)$")


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_command(command: str, cwd: Path, verbose: bool) -> bool:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        capture_output=not verbose,
    )
    if verbose:
        return result.returncode == 0
    if result.returncode == 0:
        return True
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    print(f"[CHECK FAIL] {command}")
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return False


def evaluate_check(check: Dict, base_dir: Path, verbose: bool) -> bool:
    passed = True

    for command in check.get("commands", []):
        if not run_command(command=command, cwd=base_dir, verbose=verbose):
            passed = False

    for rel in check.get("paths_all_exist", []):
        if not (base_dir / rel).resolve().exists():
            passed = False
            if verbose:
                print(f"[CHECK FAIL] missing path: {rel}")

    return passed


def apply_states_to_roadmap(roadmap_text: str, state_map: Dict[str, bool]) -> Tuple[str, List[str], List[str]]:
    changed_items: List[str] = []
    missing_items: List[str] = []
    seen_items = set()
    new_lines: List[str] = []

    for raw_line in roadmap_text.splitlines(keepends=True):
        line_ending = ""
        line_body = raw_line
        if raw_line.endswith("\r\n"):
            line_ending = "\r\n"
            line_body = raw_line[:-2]
        elif raw_line.endswith("\n"):
            line_ending = "\n"
            line_body = raw_line[:-1]

        match = CHECKBOX_RE.match(line_body)
        if not match:
            new_lines.append(raw_line)
            continue

        item = match.group("item")
        if item not in state_map:
            new_lines.append(raw_line)
            continue

        seen_items.add(item)
        desired_state = "x" if state_map[item] else " "
        current_state = match.group("state").lower()
        if current_state != desired_state:
            changed_items.append(item)
        updated_line = f"{match.group('prefix')}{desired_state}{match.group('suffix')}{item}{line_ending}"
        new_lines.append(updated_line)

    for item in state_map:
        if item not in seen_items:
            missing_items.append(item)

    return "".join(new_lines), changed_items, missing_items


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ROADMAP.md checkboxes from machine-checkable rules.")
    parser.add_argument("--config", default="scripts/roadmap_sync_checks.json", help="Path to roadmap sync config JSON")
    parser.add_argument("--apply", action="store_true", help="Write updated checkbox states to roadmap file")
    parser.add_argument("--check", action="store_true", help="Fail if roadmap is out of sync")
    parser.add_argument("--verbose", action="store_true", help="Print command-level execution details")
    args = parser.parse_args()

    if not args.apply and not args.check:
        args.apply = True

    base_dir = Path(__file__).resolve().parents[1]
    config_path = (base_dir / args.config).resolve()
    config = load_config(config_path)

    roadmap_path = (base_dir / config.get("roadmap_file", "ROADMAP.md")).resolve()
    roadmap_before = roadmap_path.read_text(encoding="utf-8")

    checks = config.get("checks", [])
    state_map: Dict[str, bool] = {}
    for check in checks:
        item = check.get("item")
        if not item:
            continue
        state_map[item] = evaluate_check(check=check, base_dir=base_dir, verbose=args.verbose)

    roadmap_after, changed_items, missing_items = apply_states_to_roadmap(roadmap_before, state_map)

    if missing_items:
        print("Warning: the following mapped roadmap items were not found in ROADMAP.md:")
        for item in missing_items:
            print(f"- {item}")

    if changed_items:
        print("Updated checkbox state for:")
        for item in changed_items:
            print(f"- {item}")
    else:
        print("ROADMAP.md already in sync.")

    if args.apply and roadmap_after != roadmap_before:
        roadmap_path.write_text(roadmap_after, encoding="utf-8")
        print(f"Wrote updates to {roadmap_path}")

    if args.check and roadmap_after != roadmap_before:
        print("ROADMAP.md is out of sync. Run: python scripts/sync_roadmap.py --apply")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
