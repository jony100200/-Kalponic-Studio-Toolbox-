# Roadmap (Checklist)

This file tracks what is done and what is next for KS CodeOps.

## Completed

- [x] VS Code window focus and input focus verification
- [x] Text send via clipboard
- [x] Image send via clipboard
- [x] Per-target presets (Copilot, Gemini, Codex, Kilo, Cline)
- [x] Target selection in GUI
- [x] GUI target checkbox matrix (`enabled_targets`) for explicit multi-target selection
- [x] Test target activation in GUI/CLI
- [x] Per-step target routing in sequence JSON
- [x] Single-lane job runner, status, retries, validators
- [x] Phase 1: Output capture, extraction, and step artifacts
- [x] Phase 2: Optional UIA backend with pyautogui fallback
- [x] Phase 3: Companion VS Code bridge extension scaffold
- [x] Modernized dark UI visual system and action hierarchy
- [x] Status strip chips + ordered activity logging in GUI
- [x] Professional font fallback stack for cross-machine consistency

## Reliability hardening first (required before multi-lane default)

- [x] Block absolute/escaping paths in materialization output handling
- [x] Return non-zero CLI exit code when `run-job` fails
- [x] Re-validate outputs when skipping previously completed steps
- [x] Prevent diagnostic commands (`test-sequence`/`health-check`) from mutating persistent config by default
- [x] Fail fast on unknown validator type (or add explicit strict mode default)
- [x] Add troubleshooting matrix and pre-run regression checklist
- [x] Add automated tests (unit + CLI integration)
- [x] Add CI gates for automated tests

## After reliability gates

- [x] Rule-based scheduler for task-to-target assignment (fit/speed/reliability)
- [x] Multi-lane dispatcher skeleton with safe fallback to single-lane
- [x] Lane/worktree isolation and health-based rerouting
- [x] Lane-level status/lock files and post-run summary metrics

## Commercial execution track

- [x] Worker adapter contract execution with request/response artifact standard
- [x] Copilot built-in worker adapter (`copilot_vscode`) with bridge-capture contract flow
- [x] Cline built-in worker adapter (`cline_vscode`) with bridge-capture contract flow
- [x] Gemini built-in worker adapter (`gemini_vscode`) with bridge-capture contract flow
- [x] Codex built-in worker adapter (`codex_vscode`) with bridge-capture contract flow
- [x] Kilo built-in worker adapter (`kilo_vscode`) with bridge-capture contract flow
- [x] Contract-first job bootstrapping from `init-job` (defaults to `worker_contract`; legacy text mode optional)
- [x] True parallel lane execution for contract-safe workloads
- [x] Release hardening: packaged build metadata, semantic versioning, smoke-run command
