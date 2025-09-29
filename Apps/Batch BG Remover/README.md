---

# KS BG Eraser — Enhanced (Batch Background Remover) v2.0

🚀 Polished, maintainable, and user-friendly batch background removal tool. This folder
contains an enhanced version of the Batch Background Remover with a modular architecture
(processing, UI and configuration separated), robust error handling, progress reporting,
and a responsive GUI for interactive batch jobs.

---

## Table of contents 📚

- [Quick overview](#quick-overview)
- [Features](#features)
- [Directory layout](#directory-layout-high-level)
- [Installation](#installation)
- [Run (GUI / CLI)](#run-gui--cli)
- [Configuration](#configuration)
- [Integration & Orchestration](#integration--orchestration)
- [Troubleshooting](#troubleshooting)
- [Logs, Failed Files & Retry](#logs-failed-files--retry)
- [Contributing](#contributing)
- [Packaging & Distribution](#packaging--distribution)
- [License](#license)

---

## Quick overview ✨

- **Purpose:** Batch remove image backgrounds and output PNGs with transparency.
- **Modes:** GUI (CustomTkinter) and CLI-friendly entrypoints (see `main_v2.py`).
- **Output:** Clean PNGs (alpha channel preserved); relative folder structure is preserved when scripting batch runs.
- **Design:** SOLID + KISS — modular so removers, processors and the UI are separated and testable.

## Features ✅

- Batch processing: PNG / JPG / WebP input
- Responsive GUI: progress bar, current file status, and live preview (optional)
- CLI-friendly: designed to be called from scripts/orchestrators
- Retry and manifest: failed-file lists and CSV manifest for auditing
- Configurable: threshold, JIT and other options via `src/config`
- Safe defaults: sensible window size, minimum dimensions, and responsive layout

## Directory layout (high-level) 📁

```
Apps/Batch BG Remover/
├─ main_v2.py            # GUI/entrypoint for the enhanced app
├─ run_main_v2.bat       # Windows launcher (uses system Python)
├─ README.md             # User-friendly README (this file)
└─ src/
  ├─ config/            # configuration management
  ├─ core/              # processing engine, remover factory, removers
  └─ ui/                # controller and main window
```

## Installation ⚙️

Prerequisites: Python 3.10+ and pip.

Recommended: install the required packages (you may already have some installed):

```powershell
python -m pip install -r "Apps/Batch BG Remover/requirements.txt"
```

Optional: use a virtual environment (recommended for clean installs):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r "Apps/Batch BG Remover/requirements.txt"
```

## Run (GUI / CLI) ▶️

### GUI (quick)

From the `Apps/Batch BG Remover` folder:

```powershell
python main_v2.py
```

Or double-click `run_main_v2.bat` (invokes system Python).

### CLI / Headless

The app exposes a `main_v2.py` entrypoint for interactive use. For scripted or headless
workflows you can either call `main_v2.py` from a script or import the processing engine from
`src/core/processor.py` and call it directly. Importing the processor gives the cleanest API for
automation and lets you handle manifests, retries and other workflow features in your own script.

Example: simple invocation (interactive)

```powershell
python main_v2.py
```

## Configuration 🧭

Configuration is handled by `src/config`. The app will create a `config.json` the first time it runs.
You can change thresholds, UI defaults, and processing options via the GUI (preferred) or by editing
the config file directly.

Sample configuration:

```json
{
  "removal": { "threshold": 0.5, "use_jit": false },
  "ui": { "theme": "dark", "show_preview": false, "window_geometry": "1200x700" },
  "processing": { "output_format": "PNG", "suffix": "_cleaned", "max_workers": 1 }
}
```

## Automation notes �

This repository provides the core background removal application and a GUI entrypoint. It does not
include a folder-level orchestrator. If you want end-to-end automation (manifests, resume/retry,
sampling), implement that separately and call this app's processor or `main_v2.py` as needed.

Recommended: import and use `src/core/processor.py` from your automation script for best control.

## Troubleshooting 🐞

- GUI exits immediately: missing dependencies. Run `pip install -r requirements.txt`.
- Stuck processing: inspect logs in the UI or run with `--sample 5` to reproduce locally.
- Torch warnings (meshgrid/indexing): informational. If necessary, align `torch` version with other libs.

## Logs, Failed Files & Retry 🔁

The system writes a CSV manifest (when used with the orchestrator) and collects failed-file lists.
Use the UI to export failed lists and retry them. Files left in the `work` folder indicate
`NEEDS_REVIEW` status after cleanup failure.

## Contributing 🤝

- Follow KISS & SOLID: keep changes small and focused.
- Add unit tests for `src/core/processor.py` flow when possible (use dummy removers).
- New remover? Implement the `BackgroundRemover` interface and register it with the factory.

## Packaging & Distribution 📦

To distribute this app as a standalone executable on Windows, use PyInstaller to build an EXE.
Include the executable, a short README, and the LICENSE in the release ZIP. If you'd like, I can
provide a `RELEASE.md` with PyInstaller steps and a sample spec file.

## License 📜

The KS BG Eraser code in this folder is released under the **MIT License**. You can find the
full license text in the repository `LICENSE` file at the project root.

Summary: you are free to use, modify, and redistribute this code under the terms of the MIT
license. If you later build other tools or paid wrappers that call this code, keep those
distributions separate — the core project here remains MIT.

---

## Want me to help further? 💡

I can help with any of the following as separate, optional tasks:

- Draft a `RELEASE.md` with PyInstaller steps to build a distributable EXE on Windows.
- Add small file-level wrapper scripts if you want simple `<src> <dst>` command-line calls.
- Help write automated scripts that import `src/core/processor.py` for folder processing.

Reply with which item you want next and I'll implement it.