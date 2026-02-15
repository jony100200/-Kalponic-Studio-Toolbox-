# KS CodeOps

KS CodeOps — VS Code multi-agent coding orchestrator (formerly PromptSender2VSCode).

## What this app is for

KS CodeOps exists to turn your idea/blueprint into a repeatable build pipeline using VS Code AI extensions as coordinated "programmer workers."

At a high level, it does this:

1. Take your blueprint, prompts, images, and job steps.
2. Send each step to selected VS Code chat extensions (Copilot, Gemini, Codex, Kilo, Cline).
3. Capture and validate outputs (`BEGIN_OUTPUT` / `END_OUTPUT` workflow).
4. Save artifacts and generated docs/files for each step.
5. Run iterative job flows so you can move from concept -> documents -> generated app with less manual copy/paste.

Current stable mode is single-lane execution with strong capture/validation.
Multi-lane orchestration remains planned, but reliability hardening is prioritized first.

See `PLANNING.md` and `ROADMAP.md` for details.
Strategy alignment for this app is documented in `STRATEGY_V4_APPLICATION.md`.
Implementation guardrails are documented in `ENGINEERING_GUIDELINES.md`.

## Install
```powershell
pip install -r requirements.txt
```

## Test
```powershell
python -m unittest discover -s tests -v
```

## Roadmap Sync (Run After Each Completed Part)
```powershell
python scripts/sync_roadmap.py --apply
```

Strict verification (fails if roadmap is outdated):

```powershell
python scripts/sync_roadmap.py --check
```

One-command part completion flow:

```powershell
.\scripts\part_done.ps1
```

or

```cmd
scripts\part_done.bat
```

## Operations Docs

- Troubleshooting matrix: `docs/troubleshooting.md`
- Pre-run regression checklist: `docs/regression_checklist.md`

## Run (GUI)
```powershell
python main.py
```

## UI status (current)

The GUI now uses a modern dark control-room layout focused on action hierarchy and operational clarity:

- Dense settings card with aligned fields
- Action hierarchy (primary run/send, secondary test, separate calibration)
- Status strip chips (`Target`, `Backend`, `Job State`)
- Left-aligned slim tabs and dominant text workspace
- Ordered activity logs with timestamp + session log file under `logs/`

### Visual tokens

- `bg`: `#171A1F`
- `surface-1`: `#1F242C`
- `surface-2`: `#272E38`
- `border`: `#343D4A`
- `text-primary`: `#E6EBF2`
- `text-secondary`: `#A8B2C3`
- `primary`: `#6FA8FF`
- `primary-hover`: `#86B6FF`

Blue is reserved for primary actions and active tab state.

### Font stack

The UI selects a professional sans-serif stack with runtime fallback:

`Inter` -> `Segoe UI` -> `Roboto` -> `Arial` -> `Helvetica`

## CLI examples
```powershell
python cli.py version
python cli.py smoke-run
python cli.py targets
python cli.py set-target --name copilot
python cli.py test-target --name copilot
python cli.py init-job --dir jobs/ks_pdf_studio_v2 --design design.md --name KS_PDF_Studio_v2
python cli.py run-job --dir jobs/ks_pdf_studio_v2
python cli.py dispatch-multi --file dispatch.sample.json
python cli.py dispatch-multi --file dispatch.sample.json --test-mode
python cli.py materialize-app --source jobs/simple_app_test/outputs/app_spec.md --out generated_apps/tiny_app
python cli.py health-check --names copilot gemini codex kilo cline
```

## Worker Adapter Contract

`run-job` supports `worker_contract` steps for file-based adapter execution.

Per attempt, artifacts are written to:

- `artifacts/<step_id>/attempt_<n>_worker_contract/request.json`
- `artifacts/<step_id>/attempt_<n>_worker_contract/response.json`
- `artifacts/<step_id>/attempt_<n>_worker_contract/notes.md` (optional)
- `artifacts/<step_id>/attempt_<n>_worker_contract/diff.patch` (optional)

Example step:

```json
{
  "id": "build_api",
  "type": "worker_contract",
  "target": "copilot",
  "content": "Implement API endpoint",
  "worker": { "adapter": "copilot_vscode" },
  "output_file": "outputs/build_api.md",
  "validator": { "type": "exists" }
}
```

Adapter configuration is stored in `config.json` under `worker_adapters`.

Built-in adapters enabled by default in config:

- `copilot_vscode`
  - `mode: "vscode_chat"`
  - `target: "copilot"`
  - `capture.source: "bridge"` (from `bridge_response_file`)
  - `allow_command_open: false` (safe default)
- `gemini_vscode`
  - `mode: "vscode_chat"`
  - `target: "gemini"`
  - `capture.source: "bridge"` (from `bridge_response_file`)
  - `allow_command_open: true`
- `codex_vscode`
  - `mode: "vscode_chat"`
  - `target: "codex"`
  - `capture.source: "bridge"` (from `bridge_response_file`)
  - `allow_command_open: true`
- `kilo_vscode`
  - `mode: "vscode_chat"`
  - `target: "kilo"`
  - `capture.source: "bridge"` (from `bridge_response_file`)
  - `allow_command_open: true`
- `cline_vscode`
  - `mode: "vscode_chat"`
  - `target: "cline"`
  - `capture.source: "bridge"` (from `bridge_response_file`)
  - `allow_command_open: true` (uses Cline open command path)

Copilot step example:

```json
{
  "id": "copilot_plan",
  "type": "worker_contract",
  "content": "Produce implementation plan with risks",
  "worker": { "adapter": "copilot_vscode" },
  "output_file": "outputs/copilot_plan.md",
  "validator": { "type": "sections", "required": ["# Plan"] }
}
```

Cline step example:

```json
{
  "id": "cline_review",
  "type": "worker_contract",
  "content": "Review architecture and identify risks",
  "worker": { "adapter": "cline_vscode" },
  "output_file": "outputs/cline_review.md",
  "validator": { "type": "sections", "required": ["# Risks"] }
}
```

### Target behavior (Copilot-first safe mode)

- `enabled_targets` controls which extension chats can run.
- Default safe setup is Copilot-only (`enabled_targets: ["copilot"]`).
- Copilot uses `assume_open: true` by default, so KS CodeOps does not run an open-chat command; it focuses VS Code and types into the configured right-side chat input.
- Other targets use extension open commands and include a settle delay (`settle_delay_s`) before typing.

Testing without sending:

```powershell
python cli.py dispatch-multi --file dispatch.sample.json --test-mode
python cli.py run-sequence --file sequence.sample.json --test-mode
python cli.py self-test-targets
python cli.py test-sequence --names copilot gemini codex kilo cline
```

`--test-mode` types into the target chat input but does not press Enter.

Automated target-input probe test:

```powershell
python cli.py set-enabled-targets --names copilot gemini codex kilo cline
python cli.py self-test-targets
python cli.py set-enabled-targets --names copilot
```

`self-test-targets` verifies each selected target by activating it, applying settle delay, focusing input, typing a probe marker, and clearing it (no send).

One-command health check:

```powershell
python cli.py health-check --names copilot gemini codex kilo cline
```

This runs focus pre-check, per-target probe check, and no-send sequence validation with a final PASS/FAIL summary.
It also writes a machine-readable health snapshot to `target_health.json` for runtime rerouting decisions.

Safety note: `health-check` and `test-sequence` default to **no extension open commands** to avoid command text leaking into chat inputs during test mode.
In this safe mode, strict cross-target switching cannot be guaranteed; only the first target is strictly verifiable.
Use `--open-commands` only when you explicitly want command-based panel opening during tests.

## UI checkbox mapping (for your app UI)

- UI checkboxes map directly to `enabled_targets` in config.
- Task routing uses those enabled targets (single target or multi-target dispatch).
- Safe default remains Copilot-only.

Configuration and usage match the previous app; this folder is the new canonical name.

## Job bootstrap

- If a job folder has `brief.md` but no `plan.json`, `run-job` auto-generates `plan.json` + prompt files.
- You can also generate manually with `init-job` for review before execution.
- A design-aware sample job is included at `jobs/ks_pdf_studio_v2`.
- `init-job` now supports auto target assignment when `--target` is omitted:
	- uses enabled worker targets from config (`enabled_targets`)
	- applies a simple deterministic policy (`auto_enabled_targets_v1`)
	- stores assignment reason per step in `plan.json`

## Phase 1: Output capture pipeline

`run-job` now supports per-step capture and artifact persistence.

- Raw capture is stored in `artifacts/<step_id>/attempt_<n>_raw.txt`
- Extracted capture is stored in `artifacts/<step_id>/attempt_<n>_extracted.txt`
- If `output_file` is provided, extracted content is written there.

Capture config example:

```json
{
	"id": "outline",
	"type": "text",
	"prompt_file": "prompts/01_outline.md",
	"target": "copilot",
	"press_enter": true,
	"wait": 4,
	"capture": { "source": "bridge" },
	"output_file": "outputs/outline.md",
	"validator": { "type": "sections", "required": ["# Architecture", "# Tasks"] }
}
```

Supported capture sources:

- `none` (default)
- `clipboard`
- `file` (requires `capture.path`)
- `bridge` (uses `.ks_codeops/bridge/latest_response.txt` by default)

Extraction uses `BEGIN_OUTPUT` and `END_OUTPUT` markers from config. If markers are absent, full captured text is used.

If `send_text` / `send_image` fails but a capture source is configured (`bridge`, `file`, or `clipboard`), job execution continues in capture-fallback mode for that step.

Prompt completion detection is enabled via capture polling with timeout/freshness checks.
By default, fresh-capture is enforced for dynamic chat captures (`bridge`, `clipboard`) and disabled for static capture contexts (`file` source or `validate` steps).

Lane runtime artifacts are written per run:

- `lanes/<lane_id>/worktree/` isolated lane workspace
- `lanes/<lane_id>/status.json` lane state + metrics
- `lanes/<lane_id>/lock.json` transient lane step lock
- `lane_summary.json` post-run lane summary and dispatch metadata

Parallel lane execution is now available when both are enabled in config:

```json
{
  "multi_lane_enabled": true,
  "multi_lane_parallel": true
}
```

Current safe scope for parallel execution is contract-driven steps (`worker_contract`) and `validate` steps.
Unsupported step types automatically fall back to single-lane executor.

Step-level completion override example:

```json
{
	"completion": {
		"timeout_s": 120,
		"poll_interval_s": 2,
		"require_fresh_capture": true
	}
}
```

## Phase 2: Automation backend

Config supports selecting backend:

```json
{
	"automation_backend": "pyautogui"
}
```

or

```json
{
	"automation_backend": "uia"
}
```

`uia` mode uses UI Automation backend when available and falls back to pyautogui if unavailable.

## Phase 3: VS Code bridge extension

A minimal companion extension is available at `vscode_bridge_extension`.

- `KS CodeOps: Write Clipboard to Bridge`
- `KS CodeOps: Open Bridge Response File`

This enables deterministic capture flow: copy chat response -> write bridge -> `run-job` captures and validates.

## Tiny app automation test

Use `jobs/simple_app_test` to validate output-to-app automation:

1. `python cli.py run-job --dir jobs/simple_app_test`
2. `python cli.py materialize-app --source jobs/simple_app_test/outputs/app_spec.md --out generated_apps/tiny_app`
3. `python generated_apps/tiny_app/main.py`

## Engineering guardrails

KS CodeOps follows KISS and SOLID by policy:

- KISS: prefer simple, explicit flows over complex hidden orchestration.
- Single responsibility: runner, sequencer, automation, and materializer are kept separate.
- Open/closed: new automation backends and targets are config-driven.
- Dependency inversion: job logic depends on abstraction-level services (sequencer/config), not UI details.

## Product release gates (2026)

Reliability and safety gates are required before multi-lane becomes a default workflow:

- `v0.3 Beta` target date: March 15, 2026
  - fix critical blockers (safe materialization path handling, non-zero exit on failed `run-job`, resume validation, no unintended config mutation in diagnostics)
- `v0.4 Hardening` target date: April 30, 2026
  - automated test suite + CI gates for core CLI and job lifecycle paths
  - regression checklist and troubleshooting matrix included in docs
- `v1.0` target date: June 30, 2026
  - reliability gates sustained across releases
  - multi-lane available with explicit safe fallback to single-lane

## Packaging

Build package artifacts:

```powershell
python -m pip install build
python -m build
```

Version source of truth: `src/version.py` (exposed via `python cli.py version`).
