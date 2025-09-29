# KS BG Eraser — Enhanced (Batch Background Remover) v2.0

Polished, maintainable, and user-friendly batch background removal tool. This repo contains
an enhanced version of the Batch Background Remover with a modular architecture (processing,
UI and configuration separated), robust error handling, progress reporting and easy integration
points for pipelines (for example the KS Auto Pipeline orchestrator).

This README explains what the app does, how to run it, how to integrate it into a pipeline, and
how to contribute.

---

## Quick overview

- Purpose: Batch remove image backgrounds (producing PNGs with transparency) from folders.
- Modes: GUI (CustomTkinter) and CLI entrypoints are available (see `main_v2.py`).
- Output: PNG with alpha channel; keeps relative folder structure when used in pipelines.
- Design: SOLID + KISS — the implementation is modular so removers, processors and the UI are
  separated and testable.

## Features

- Batch processing of PNG / JPG / WebP files
- GUI with progress bar, live preview, and folder queue
- CLI-friendly for automation and pipelines
- Collects processing stats and failed-file lists for retries
- Configurable threshold and JIT options via `config` module
- Safe defaults and sensible minimum window size, responsive layout

## Directory layout (high-level)

```
Apps/Batch BG Remover/
├─ main_v2.py            # GUI/entrypoint for the enhanced app
├─ run_main_v2.bat       # Windows launcher (uses system Python)
├─ README_v2.md          # This file
└─ src/
   ├─ config/            # configuration management
   ├─ core/              # processing engine, remover factory, removers
   └─ ui/                # controller and main window
```

## Installation

Prerequisites: Python 3.10+ and pip. On Windows, the repository includes `run_main_v2.bat` for
convenient launching using the system Python.

Recommended: install the required packages (you may already have some installed):

```powershell
python -m pip install -r "Apps/Batch BG Remover/requirements.txt"
```

If you prefer not to install globally, create a virtual environment (optional):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r "Apps/Batch BG Remover/requirements.txt"
```

## Run the GUI (quick)

From the `Apps/Batch BG Remover` folder:

```powershell
python main_v2.py
```

Or double-click `run_main_v2.bat` (uses system Python by default).

## Run from CLI (headless usage)

The application exposes a `main_v2.py` entrypoint that the GUI uses. If you want to run
headless operations or wire the app into a pipeline, prefer the `ks_auto_pipeline.py`
or the simple CLI-style wrappers (see `Apps/KS-Auto-Pipeline` if added).

Usage example (pipeline-level orchestrator recommended):

```powershell
# Example: run the GUI app (interactive)
python main_v2.py

# The orchestrator (ks_auto_pipeline.py) is recommended for end-to-end automation
python ..\KS-Auto-Pipeline\ks_auto_pipeline.py --in "D:\Assets\Raw" --work "D:\Assets\_temp" --out "D:\Assets\Final" --threads 4
```

## Configuration

Configuration is stored and managed by the `src/config` module. The app will create a
`config.json` (or similar) the first time it runs — you can change thresholds, UI defaults,
and processing options via the GUI or by editing the configuration file.

Default configuration values include:

```json
{
  "removal": { "threshold": 0.5, "use_jit": false },
  "ui": { "theme": "dark", "show_preview": false, "window_geometry": "1200x700" },
  "processing": { "output_format": "PNG", "suffix": "_cleaned", "max_workers": 1 }
}
```

## Integration & Orchestration

This app is intentionally modular so it can be used from the KS Auto Pipeline orchestrator
(recommended for paid workflow packaging). Integration options, in preferred order:

1. Call a dedicated file-level wrapper that accepts `src_path` and `dst_path` and returns
   a status code (best: implement small wrappers if not present).
2. Import and call the processor from Python directly (if you need tighter integration).
3. Subprocess call to `python main_v2.py <src> <dst>` (fallback).

If you plan to build a paid pipeline product, keep the orchestrator UI small and let it call
the pieces here — avoid duplicating core logic.

## Troubleshooting

- If the GUI exits immediately: check for missing dependencies (e.g., `transparent-background`) and
  run `pip install -r requirements.txt`.
- If processing stalls on certain images: check logs (GUI shows errors) and try `--sample 5` to
  reproduce locally.
- If you see torch-related warnings about meshgrid/indexing, they’re warnings only — ensure
  your installed `torch` version is compatible with other optional libs.

## Logs, Failed Files & Retry

The app and orchestrator (if used) collect processing statistics and failed-file lists. Use the
UI to export failed lists and retry them; the orchestrator writes a CSV manifest for auditing.

## Contributing

- Keep changes small and focused: follow the KISS & SOLID intent in code reviews.
- Add tests for the core `src/core/processor.py` flow where possible (unit test the engine with
  a dummy remover implementation).
- If adding a new remover implementation, implement the `BackgroundRemover` interface and
  register it in the factory.

## Packaging & Distribution

For distribution of a paid orchestrator, recommended packaging approach:

- Build a Windows executable using PyInstaller for the orchestrator UI and include this
  app as a dependency in the release zip.
- Deliver through Gumroad/Itch/Gumroad for instant downloads and license handling.

## License

This repository includes components that you can license however you wish. If you plan to
distribute the orchestrator as a paid product, consider shipping the core tools as free
and the orchestrator as the paid convenience wrapper.

---

If you want, I can:

- Add a small `ks_pipeline_tab` in the KS BG Eraser UI that calls the orchestrator in the
  background and shows per-file progress (quick integration).
- Create lightweight file-level wrapper scripts for the remover and cleanup tools so the
  pipeline can call them simply as `bg_wrapper.py <src> <dst>` and `cleanup_wrapper.py <src> <dst>`.
- Draft a short `RELEASE.md` with packaging/pyinstaller steps for Windows builds.

Tell me which of those you'd like me to implement next and I will proceed.