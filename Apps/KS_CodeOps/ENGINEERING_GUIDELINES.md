# KS CodeOps Engineering Guidelines

This file defines how we keep KS CodeOps easy to debug, easy to extend, and aligned with KISS + SOLID.

## Core principles

- KISS first: prefer simple, explicit flow over clever orchestration.
- Single responsibility: each module owns one concern.
- Config over hardcode: targets and behavior should be policy-driven.
- Deterministic fallback: always keep a safe single-lane path.
- Observable behavior: every major step logs clear state transitions.

## Module boundaries

- `src/automation/*`
  - Only window/input control primitives.
  - No job logic, no planning logic.
- `src/core/sequencer.py`
  - Orchestration facade for send/probe/sequence flows.
  - Delegates activation and input verification to dedicated services.
  - No long-term scheduling policy.
- `src/core/target_activation.py`
  - Target activation and window-focus retry behavior.
  - No prompt sequencing or capture logic.
- `src/core/input_verifier.py`
  - Input focus verification and fallback click calibration updates.
  - No planning, scheduling, or run lifecycle logic.
- `src/core/job_runner.py`
  - Step lifecycle, retry, status, capture, validation.
  - No direct UI details.
- `src/core/capture_runtime.py`
  - Capture source reading, completion polling, extraction, artifact persistence.
  - No step dispatch decisions.
- `src/core/step_validator.py`
  - Output artifact validation rules (`exists`, `json`, `sections`).
  - No capture or dispatch behavior.
- `src/core/plan_builder.py`
  - Plan scaffolding only.
- `src/core/assignment_policy.py`
  - Target assignment strategy only.
  - No prompt generation, file IO, or execution logic.
- `src/core/materializer.py`
  - File extraction/materialization only.
- `src/gui/main_window.py`
  - User interactions and display.
  - No business-rule branching beyond input validation.

## Debuggability rules

- Log with short tags for critical paths (examples: `[ACTIVATE]`, `[VERIFY]`, `[CAPTURE]`).
- Keep retries centralized in helper methods to avoid divergence.
- Never duplicate fallback loops in multiple places.
- Record outcome and reason on every failed step.
- Persist artifacts for each attempt when capture is enabled.

## Change policy (for new features)

Before adding a feature, answer:

1. Which module owns this behavior?
2. Can this be config-driven?
3. How does this fail safely?
4. How is this observed in logs/status?
5. Can we test this path in `--test-mode` without sending?

If any answer is unclear, stop and simplify design first.

## Multi-lane readiness (next)

When adding scheduler/lanes, keep this split:

- Scheduling policy service: selects lane/target by rules.
- Execution service: runs assigned steps.
- Health service: tracks reliability and triggers fallback.

Do not merge scheduler policy into `job_runner` or automation classes.

## UI standards

- Primary blue only for main action and active tab.
- Secondary/utility controls stay neutral.
- Status strip must always expose: target, backend, job state.
- Keep spacing/radius tokens consistent (`8/12/16/24`, radius `10/12`).

## Definition of done (engineering)

A change is done only if:

- Behavior is in the correct module.
- Logs are sufficient to debug failures.
- Config defaults remain safe.
- Existing CLI flows still run.
- `py_compile`/diagnostics pass for touched files.
