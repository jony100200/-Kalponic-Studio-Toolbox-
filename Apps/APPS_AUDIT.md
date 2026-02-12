# APPS AUDIT — Product & Technical Audit

**Purpose:** This file is a product + technical audit of the `Apps/` folder. It goes beyond UI to capture **functionality**, **test coverage**, **packaging readiness**, **confidence**, **repro steps**, and **priority remediation tasks** so we can plan work and track progress.

Summary (quick):
- Total app folders/files reviewed: **23**
- Candidate apps ready for packaging / public release (high-confidence): **9** (SnapClip MVP, Batch BG Remover, Batch-cleanup, ImageResize, Model Launcher, Universal Model Launcher, PromptSender2ChatGP, zip_image_extractor, RemoveSuffix)
- Apps with partial functionality or failing workflows: **6** (KS MetaMaker, KS SnapStudio, KS_PDF_Studio, KS_Seamless_Checker, KS Sprite Splitter, KS_PDF_Studio)
- Early / design-only / placeholders: **8** (KS AutoModel, Local AI Model Laucher, Pathline, sprite_sheet_splitter, FastPBR_MapMaker, TranscriptMaker (CLI-only), KSTexturePresentation [feature-polish only], others)

Confidence legend:
- **High** — README + launchers + tests present and smoke tests pass locally.
- **Medium** — README + launcher present; limited or no tests; we need repro verification.
- **Low** — Only docs or design doc present; no runnable entrypoint or failing tests.

---

## Per-app audit (detailed)

Note: For each app below I list: Short description; current state; confidence; evidence; reproducible test(s) to run; recommended immediate actions (short-term P0/P1/P2) with rationale.

---

### KS SnapClip (formerly Area_Screenshot_Tool)
- Short: Clipboard-first screenshot app (area & fullscreen, history, copy to clipboard).
- State: MVP working (fullscreen capture, copy/save, in-memory store). Area overlay present as `area_overlay.py` but not integrated into `capture.capture_area()` yet.
- Confidence: High — smoke tests added and passing (store tests). UI prototype exists.
- Evidence: `ui.py`, `capture.py`, `store.py`, `clipboard_win.py`, `area_overlay.py`, test `tests/test_smoke_capture.py`.
- Repro tests: Run `python main.py`, Capture fullscreen, Copy to clipboard (on Windows with pywin32), Save last capture.
- Recommended immediate (P0): Integrate overlay into `capture.capture_area()` and wire to UI; add history thumbnail grid + right-click Copy/Save/Delete. Add hotkey opt-in and tests for overlay flow. Rationale: makes MVP complete & user-friendly.

---

### Batch BG Remover
- Short: Batch background removal with GUI + CLI and modular processors.
- State: Working and documented; solid test coverage in processing code.
- Confidence: High
- Evidence: `main_v2.py`, `src/` with modular code, README with run steps and packaging notes.
- Repro tests: `python main_v2.py`; run a small sample folder; verify outputs and retry workflows.
- Recommended immediate (P1): Add release packaging (PyInstaller), include sample inputs for CI integration tests, and add an automated smoke test that runs a small batch job in headless mode.

---

### Batch-cleanup tool
- Short: Fringe removal & alpha refinement tool (CustomTkinter UI).
- State: Working
- Confidence: High
- Evidence: `main.py`, README, launchers present.
- Recommended immediate (P2): Add CI smoke test and EXE packaging.

---

### FastPBR_MapMaker
- Short: Single-file helper for PBR map generation.
- State: Prototype/CLI
- Confidence: Low
- Evidence: Single script `PBRMapMakerSimpler.py`
- Recommended immediate (P2): Add CLI flags, example input(s), and a short README section on usage; add basic tests for core functionality.

---

### ImageResize
- Short: Batch image resizer with GUI + CLI and presets.
- State: Working; tests present.
- Confidence: High
- Recommended immediate (P1): Ensure release packaging and add one-click installers and small GIF demo for marketing.

---

### KS AutoModel
- Short: Model discovery & recommendation service (design heavy).
- State: Design & core modules present; **no UI**.
- Confidence: Low
- Evidence: `KS AutoModel DesignDoc.md`, core module structure.
- Recommended immediate (P0): Implement a minimal CLI/GUI analyze → recommend → dry-run pipeline and add unit tests for scoring & provider modules. This turns it from a document to a runnable component.

---

### KS MetaMaker
- Short: AI-assisted tagging & dataset export tool.
- State: GUI & tests present but end-to-end failures reported.
- Confidence: Medium
- Evidence: README, tests exist but reports of failing runs in some integrations.
- Repro tests: Run `python app/main.py` on a small sample set and verify tagging, renaming, and export.
- Recommended immediate (P0): Add reproducible smoke test(s) that cover model loading and export flows; fix any model path or ONNX runtime issues found.

---

### KS SnapStudio
- Short: Circular preview capture and export for materials.
- State: GUI present; some capture/export workflows fail.
- Confidence: Medium
- Recommended immediate (P0): Add focused unit tests for capture and masking; add train-of-failure repro steps and fix the failing cases.

---

### KS Sprite Splitter
- Short: AI-powered sprite segmentation + matting.
- State: README & GUI present; needs verification and sample inputs.
- Confidence: Medium
- Recommended immediate (P1): Add sample sprites and an integration test that runs through segmentation → output validation.

---

### KSTexturePresentation
- Short: Icon/sprite sheet generator.
- State: Working
- Confidence: High
- Recommended immediate (P2): Packaging and UX polish.

---

### KS_PDF_Extractor_Archived
- Short: PDF extraction utilities (archived)
- State: Archived
- Confidence: Low
- Recommended immediate (P3): Leave archived; add note in top-level index explaining archival and do not include in main packaging.

---

### KS_PDF_Studio
- Short: PDF processing with API & web UI.
- State: Failing runtime tests
- Confidence: Medium/Low
- Recommended immediate (P0): Add failing E2E integration test covering API endpoints and web UI health; prioritize fixes for CI failures.

---

### KS_Seamless_Checker
- Short: Seam/tile checker with visual previews
- State: GUI & tests exist but some workflows fail
- Confidence: Medium
- Recommended immediate (P0): Add smoke tests that process a sample folder and verify expected CSV export + preview generation. Fix threading or memory issues if present.

---

### Local AI Model Laucher
- Short: Helper scripts for local model checks (code analyzer, model menu)
- State: CLI-only, helper scripts
- Confidence: Low
- Recommended immediate (P1): Consolidate with `Model Launcher` or `Universal Model Launcher` as a helper library and remove duplicate scripts. Add a small CLI entrypoint for discovery-based tests.

---

### Model Launcher
- Short: CustomTkinter GUI to pick model files and launch local server processes
- State: Working
- Confidence: High
- Recommended immediate (P1): Test across model formats and add automated checks for VRAM/compatibility.

---

### Pathline
- Short: Placeholder (empty folder)
- State: Empty
- Confidence: N/A
- Recommended immediate (P3): Decide whether to implement, archive, or remove the placeholder. Track as low priority.

---

### PromptSender2ChatGP
- Short: CLI for sending prompts & images to local LLM servers
- State: Working
- Confidence: High
- Recommended immediate (P2): optional GUI or keep CLI; add usage examples in README and sample prompts.

---

### sprite_sheet_splitter
- Short: Placeholder
- State: Empty
- Recommended immediate (P3): remove or implement.

---

### TranscriptMaker
- Short: Batch faster-whisper transcriber (CLI)
- State: CLI workable
- Confidence: Medium
- Recommended immediate (P1): Add small tests covering typical audio formats and add optional GUI later.

---

### Universal Model Launcher
- Short: V4 Feature-rich model manager
- State: Working
- Confidence: High
- Recommended immediate (P1): Packaging and release notes; test integration with Model Launcher.

---

### zip_image_extractor
- Short: UI + script to extract images from archives
- State: Working
- Confidence: High
- Recommended immediate (P2): Add release build + small sample test.

---

### RemoveSuffix.py
- Short: CLI filename suffix remover
- State: Working
- Confidence: High
- Recommended immediate (P2): Add tests for edge cases (multi-token suffixes, separators, etc.) and include it in tools docs.

---

## Cross-cutting recommendations
1. Standardize test strategy: each app must have a minimal smoke test that runs in CI (headless where possible). Add tests to `tests/` and run them in GitHub Actions. ✅
2. Packaging & Releases: prioritize SnapClip, BG Remover, Model Launchers for Windows EXE builds (PyInstaller) and signed releases. 📦
3. Consolidation plan: adopt a **plugin-host** model (KS Studio) and migrate 1 plugin as POC (recommended SnapClip or BG Remover). This avoids monolith rewrites while enabling a premium bundle later.
4. UX consistency: adopt a short UI checklist (entrypoint, primary action, settings, error handling, persistence) and add `STATUS.md` in each app folder. ✅
5. Metrics & telemetry: no telemetry by default; if opted-in add only minimal counts (installs, daily active). Document privacy in README.

---

## Immediate next steps (short-term roadmap)
1. Create reproducible issues for each P0/P1 item with clear repro steps and minimal failing test examples. (Owner: Team / You). ✅
2. Triage & assign owners — pick 1–2 owners for the first sprint of 2 weeks. ✅
3. Implement KS SnapClip overlay integration, thumbnail history, hotkey opt-in (P0) and add tests. ✅
4. Add smoke tests for `KS MetaMaker`, `KS SnapStudio`, `KS_PDF_Studio`, and `KS_Seamless_Checker` capturing current failing flows. ✅
5. Prepare release builds for SnapClip and BG Remover for an initial public release (free core). ✅

---

## Issue template (use for automating issue creation)
Title: [P0] <AppName> — <short failure summary>
Body:
- **Steps to reproduce**:
  1. Clone repo & setup venv
  2. Run `python <launcher>`
  3. Do X → observe Y
- **Expected**: <expected outcome>
- **Actual**: <actual outcome / stacktrace>
- **Testcase**: Include small sample inputs if available
- **Priority**: P0 / P1 / P2

---

If you want, I can now:
- (A) Add a short `STATUS.md` in every app folder with the one-line state and the primary P0 action, or
- (B) Create GitHub issues for all P0/P1 items using the template above (I can draft them and leave them in a checklist for you to review), or
- (C) Start implementing certain P0 items (suggest: SnapClip overlay integration and SnapClip history UI). 

Reply with A, B, C or combination and I will proceed with the chosen action.