# APPS Audit Verified Findings

Generated: 2026-02-12
Scope: `Apps/` root and app subfolders in this workspace.
Method: file structure review + targeted `pytest` runs + packaging/syntax checks.

## Executive Verdict

The current apps collection is not yet ready as a fully commercial-grade suite.
There are working pieces, but quality gates are inconsistent across apps (test coverage, packaging integrity, runtime stability).

## High-Impact Findings

1. `KS SnapStudio` is currently blocked.
- `KS SnapStudio/pyproject.toml` is invalid and has injected trailing content.
- Multiple source files contain injected `</content>` and `<parameter name="filePath">` text, causing syntax failures.

2. `KS_PDF_Studio` is not currently release-ready.
- Test collection fails due import-path issue in `KS_PDF_Studio/src/test_integration.py`.
- Root report statements are internally contradictory ("working" vs "not functioning").

3. `KS SnapClip` report is outdated in one key area.
- Overlay integration already exists in `KS SnapClip/capture.py`.
- But test suite is not fully green (`test_capture_area` fails), so "high confidence" is overstated right now.

4. `Batch BG Remover` "solid test coverage" claim is not supported by repo tests.
- App has requirements including pytest, but no discovered/runnable tests in current folder.

5. `KS AutoModel` "no UI" claim is inaccurate.
- UI modules exist under `KS AutoModel/src/ks_automodel/ui/desktop/`.

## Verified Test Snapshot

- `ImageResize`: passed (`26 passed`).
- `KS SnapClip`: partial (`1 failed, 2 passed`).
- `KS_Seamless_Checker`: passed with weak-test warnings (`6 passed`).
- `KS MetaMaker`: passed with warning (`5 passed`).
- `KS SnapStudio`: cannot run pytest due invalid `pyproject.toml`.
- `KS_PDF_Studio`: test collection error (`ModuleNotFoundError: core` path issue).
- `KS Sprite Splitter`: partial (`1 failed, 22 passed`).
- `PromptSender2ChatGP`: passed (`1 passed`).
- `KS_PDF_Extractor_Archived`: partial (`3 failed, 16 passed`).
- `Batch BG Remover`: no tests ran.
- `Batch-cleanup tool`: no tests ran.
- `KSTexturePresentation`: no tests ran.
- `Universal Model Launcher/Version4`: sampled tests passed (`3 passed` for selected files).

## Report Quality Findings

### `APPS_AUDIT.md`

- Useful directionally, but contains factual drift:
  - SnapClip overlay claim is outdated.
  - Duplicate listing in failing-app summary (`KS_PDF_Studio` repeated).
  - "solid test coverage" claim for Batch BG Remover is not evidenced by tests.

### `READ ME.md`

- Contains contradictory status for multiple apps:
  - Declares some apps as "Working" and later marks same apps as "WIP (Not functioning)".
- Contains duplicated WIP lines.

## App Status (Current Practical View)

- Verified working:
  - `ImageResize` (strongest evidence in this pass)

- Partially working / needs hardening:
  - `KS SnapClip`
  - `KS MetaMaker`
  - `KS_Seamless_Checker`
  - `KS Sprite Splitter`
  - `PromptSender2ChatGP`
  - `Universal Model Launcher` (sampled tests only)
  - `zip_image_extractor`
  - `Batch-cleanup tool`
  - `Batch BG Remover`
  - `Model Launcher`
  - `KSTexturePresentation`
  - `TranscriptMaker`
  - `RemoveSuffix.py`

- Blocked / failing:
  - `KS SnapStudio` (file corruption + syntax/packaging failure)
  - `KS_PDF_Studio` (test import-path failure)
  - `KS_PDF_Extractor_Archived` (has failing tests; archived anyway)

- Early / placeholder:
  - `KS AutoModel` (has UI pieces, but low verification maturity)
  - `Local AI Model Laucher`
  - `Pathline`
  - `sprite_sheet_splitter`
  - `FastPBR_MapMaker`

## Immediate Commercialization Priorities

1. Repair `KS SnapStudio` file corruption first (blocking defect).
2. Fix `KS_PDF_Studio` test/import path and establish runnable smoke tests.
3. Make all "working" apps pass at least one CI smoke test each.
4. Normalize root docs (`APPS_AUDIT.md`, `READ ME.md`) to remove contradictions.

