# KS CodeOps

KS CodeOps — VS Code multi-agent coding orchestrator (formerly PromptSender2VSCode).

This app automates sending prompts and images to VS Code extension chat panels (Copilot, Gemini, Codex, etc.) and runs job pipelines using a single-lane or multi-lane execution model.

See `PLANNING.md` and `ROADMAP.md` for details.
Strategy alignment for this app is documented in `STRATEGY_V4_APPLICATION.md`.

## Install
```powershell
pip install -r requirements.txt
```

## Run (GUI)
```powershell
python main.py
```

## CLI examples
```powershell
python cli.py targets
python cli.py set-target --name copilot
python cli.py test-target --name copilot
python cli.py init-job --dir jobs/ks_pdf_studio_v2 --design design.md --name KS_PDF_Studio_v2
python cli.py run-job --dir jobs/ks_pdf_studio_v2
python cli.py dispatch-multi --file dispatch.sample.json
python cli.py dispatch-multi --file dispatch.sample.json --test-mode
python cli.py materialize-app --source jobs/simple_app_test/outputs/app_spec.md --out generated_apps/tiny_app
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
```

`--test-mode` types into the target chat input but does not press Enter.

Automated target-input probe test:

```powershell
python cli.py set-enabled-targets --names copilot gemini codex kilo cline
python cli.py self-test-targets
python cli.py set-enabled-targets --names copilot
```

`self-test-targets` verifies each selected target by activating it, applying settle delay, focusing input, typing a probe marker, and clearing it (no send).

## UI checkbox mapping (for your app UI)

- UI checkboxes map directly to `enabled_targets` in config.
- Task routing uses those enabled targets (single target or multi-target dispatch).
- Safe default remains Copilot-only.

Configuration and usage match the previous app; this folder is the new canonical name.

## Job bootstrap

- If a job folder has `brief.md` but no `plan.json`, `run-job` auto-generates `plan.json` + prompt files.
- You can also generate manually with `init-job` for review before execution.
- A design-aware sample job is included at `jobs/ks_pdf_studio_v2`.

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
