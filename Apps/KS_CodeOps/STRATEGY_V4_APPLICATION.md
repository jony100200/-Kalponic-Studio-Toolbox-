# KS CodeOps — Strategy v4 Application

This document applies `KS Creation & Development Strategy Guide (Final v4.0)` to the current KS CodeOps application.

## Phase 0 — Foundation

**Goal in KS CodeOps:** Build a reusable orchestration core for AI-assisted production work.

**Applied:**
- Reused existing PromptSender architecture and refactored into layered modules.
- Preserved clipboard-based fallback for compatibility.
- Added configurable targets and backend abstraction to avoid lock-in.

**Exit Criteria:**
- Stable layered architecture exists (`core`, `automation`, `gui`).
- Config-driven behavior and target profiles are in place.

## Phase 1 — Research & Audit

**Goal in KS CodeOps:** Validate whether VS Code can be automated reliably enough for job orchestration.

**Applied:**
- Confirmed command-palette-first activation with click fallback.
- Audited limitations: UI automation in unattended/headless contexts is brittle.
- Audited alternatives: UIA backend and companion extension bridge.

**Exit Criteria:**
- Known constraints documented.
- At least one fallback path exists for each critical action.

## Phase 2 — Design & Structure

**Goal in KS CodeOps:** Keep orchestration modular and evolvable.

**Applied:**
- `VSCodeSequencer` handles target routing and execution semantics.
- `JobRunner` handles retries/status/log/validation.
- `PlanBuilder` handles `brief.md` + `design.md` to `plan.json` generation.
- Automation backend is now selectable (`pyautogui` or `uia`).

**Exit Criteria:**
- No single module owns all responsibilities.
- Backend or target changes do not require runner rewrite.

## Phase 3 — Prototype Fast

**Goal in KS CodeOps:** Prove the end-to-end core loop quickly.

**Applied:**
- Single-lane job execution works with retries and persisted status.
- Capture pipeline proved with extraction markers and artifact writes.
- Bridge extension scaffold added for deterministic manual capture handoff.

**Exit Criteria:**
- A sample job can run from plan to validated output artifact.

## Phase 4 — UX & Polish

**Goal in KS CodeOps:** Keep operation simple for daily usage.

**Applied:**
- GUI supports active target selection, test target, and click recording.
- CLI supports `init-job`, `run-job`, target management, and sequence runs.

**Next Improvements:**
- Add GUI panel for capture source (`clipboard`, `file`, `bridge`).
- Add one-click “open bridge file” helper from app UI.

**Exit Criteria:**
- Main flows are executable without editing JSON manually.

## Phase 5 — Profit / Effort Balance

**Goal in KS CodeOps:** Prioritize high-ROI reliability work.

**Applied Priorities:**
1. Output capture + validation.
2. UIA fallback backend.
3. Bridge extension scaffold.

**Next Priority:**
- Multi-lane scheduler only after capture reliability is stable.

**Exit Criteria:**
- Failure recovery cost per job decreases over time.

## Phase 6 — Package + Teach

**Goal in KS CodeOps:** Make operation repeatable for you and collaborators.

**Applied:**
- README updated with phase features and usage patterns.
- Bridge extension includes usage docs.

**Next Improvements:**
- Add short tutorial job templates (`docs-only`, `codegen`, `review`).
- Add troubleshooting table by failure mode.

**Exit Criteria:**
- New user can execute one sample job without custom setup beyond dependencies.

## Phase 7 — Market + Expand

**Goal in KS CodeOps:** Turn internal tool into ecosystem utility.

**Near-Term Expansion:**
- Add marketplace-quality VS Code bridge extension packaging.
- Add reusable job packs for other Kalponic apps.

**Exit Criteria:**
- At least one reusable pack works across multiple projects.

## Phase 8 — Maintain + Reflect

**Goal in KS CodeOps:** Continuous reliability gains.

**Operational Cadence:**
- Weekly: Review failed-step logs and top 3 root causes.
- Monthly: Update target presets and fallback profiles.
- Per release: Regression run on sample jobs.

**Exit Criteria:**
- Failure categories trend down release-over-release.

## Immediate Next Execution Plan (In Order)

1. Implement multi-lane scheduler skeleton with lane metadata and queued steps.
2. Add lane-level status files and lock files.
3. Add health scoring and automatic lane fallback to single-lane.
4. Add post-run summary generator (`success rate`, `step retries`, `failure reasons`).

---

This strategy application is additive and does not replace your master doctrine; it operationalizes it for KS CodeOps implementation decisions.
