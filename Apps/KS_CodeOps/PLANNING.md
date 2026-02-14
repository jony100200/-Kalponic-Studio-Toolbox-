# KS CodeOps - Planning

(Formerly PromptSender2VSCode) This folder contains current planning state for KS CodeOps.

Use these docs together:

- `ROADMAP.md` for completion checklist and release priorities
- `STRATEGY_V4_APPLICATION.md` for phase-by-phase doctrine application
- `ENGINEERING_GUIDELINES.md` for module boundaries and quality guardrails

## Current state snapshot

- Core pipeline is functional for single-lane jobs (prompt send, capture, artifacts, validation).
- Multi-target dispatch exists; assignment policy exists and remains deterministic.
- GUI includes target worker enablement (`enabled_targets`) and status visibility for daily operation.
- Worker adapter contract runtime is available (`worker_contract` step type).
- Parallel lane execution is available for contract-safe workloads (`multi_lane_parallel: true`).
- Release baseline now includes package metadata, semantic versioning, and CLI smoke run.

## Near-term priorities (KISS + SOLID)

1. Expand adapter coverage for real extension workers (Copilot/Cline/Codex/Kilo/Gemini wrappers).
2. Add dependency-aware scheduling for cross-lane step prerequisites.
3. Add lane throughput and retry trend dashboards from `lane_summary.json`.
4. Keep deterministic fallback path to single-lane on focus/activation instability.
5. Harden release packaging workflow (signing/changelog/release notes automation).

## Commercial readiness gates

- `v0.3 Beta` target date: March 15, 2026
  - critical blockers fixed
  - non-zero failure signaling verified in CLI
- `v0.4 Hardening` target date: April 30, 2026
  - CI regression suite active
  - troubleshooting matrix + release checklist complete
- `v1.0` target date: June 30, 2026
  - reliability metrics stable over multiple release cycles
  - multi-lane optional with explicit fallback

## Refactor guidance

- Keep `job_runner` focused on step lifecycle/state.
- Keep automation backends focused on UI control primitives.
- Keep scheduling/policy logic outside `sequencer` in dedicated services.
- Preserve config-driven target profiles for easy extension without code churn.
