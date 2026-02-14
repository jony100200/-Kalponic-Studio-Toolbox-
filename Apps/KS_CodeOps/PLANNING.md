# KS CodeOps — Planning

(Formerly PromptSender2VSCode) This folder contains current planning state for KS CodeOps.

This folder contains the KS CodeOps app: single-lane runner and multi-target orchestration prototypes.

Use these docs together:

- `ROADMAP.md` for completion checklist
- `STRATEGY_V4_APPLICATION.md` for phase-by-phase doctrine application

## Current state snapshot

- Core pipeline is functional for single-lane jobs (prompt send, capture, artifacts, validation).
- Multi-target dispatch exists, but assignment is manual and sequential by default.
- UI now has modern hierarchy and status visibility suitable for daily operator use.

## Near-term priorities (KISS + SOLID)

1. Add GUI target checkbox matrix backed by `enabled_targets`.
2. Introduce a small rule-based scheduler service (separate from sequencer) for task assignment.
3. Add dual-lane execution skeleton with explicit dependency-safe rules.
4. Keep deterministic fallback path to single-lane on focus/activation instability.
5. Add a lightweight regression checklist for pre-run readiness.

## Refactor guidance

- Keep `job_runner` focused on step lifecycle/state.
- Keep automation backends focused on UI control primitives.
- Move scheduling/policy logic out of `sequencer` into dedicated services.
- Preserve config-driven target profiles for easy extension without code churn.
