# Prompt Sequencer

Prompt Sequencer automates sending text prompts and image+text prompts to AI apps (for example ChatGPT desktop/web or Groq clients).

It is designed for long batch runs with safety controls, retries, queue management, and resumable processing.

## Core Features

- Two run modes:
  - Text Mode: process `.txt` files containing one or many prompts.
  - Image + Text Mode: process image folders with optional prompt text.
- Queue Mode for image folders:
  - Add multiple folders.
  - Reorder, remove, clear.
  - Dynamic enqueue while running.
- Reliability and safety:
  - Keyboard-based focus strategies.
  - Retry tuning for paste/focus actions.
  - Manual intervention and resume.
  - Dry-run mode.
  - Duplicate detection and skip.
  - Error screenshot capture.
- Planning and observability:
  - Preflight checks with item/time estimate.
  - Activity log panel.
  - Run summaries (`JSON` + rolling `CSV`).
- Recovery:
  - Queue snapshots.
  - Resume queue from latest snapshot.
- Reuse:
  - Prompt variables (`{{filename}}`, `{{index}}`, `{{date}}`, etc.).
  - Save/load named profiles.

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
# or
run.bat
```

## GUI Usage

### 1. Global Controls

- Set `Target Window`.
- Use `Find Windows` and `Test Focus`.
- Set `Initial Delay`.

### 2. Execution Safety (GUI)

Available in the Global Controls section:

- `Dry Run`
- `Skip Duplicates`
- `Prompt Variables`
- `Queue Snapshots`
- `Auto Resume Queue`
- `Error Screenshots`

### 3. Reliability Tuning (GUI)

Available in the Global Controls section:

- `Paste Retries`
- `Retry Delay`
- `Focus Retries`

### 4. Profiles (GUI)

Available in the Global Controls section:

- Save current settings to a profile name.
- Load selected profile.
- Refresh profile list.

### 5. Utility Actions (GUI)

Available in the Global Controls section:

- `Preflight Check`
- `Resume Snapshot`
- `Open Last Summary`

### 6. Risk Indicator (GUI)

Global Controls includes a small risk badge that reflects current safety settings:

- `Safe (Dry Run)`
- `Guarded`
- `Normal`
- `Elevated`

## Modes

### Text Mode

- Select folder with `.txt` files.
- Prompt parsing supports:
  - Numbered sections (`1. Title ...`).
  - `---` separators.
  - Double-newline separation.
- On successful live runs, sent prompts/files are organized into `sent_prompts`.

### Image + Text Mode (Single Folder)

- Select image folder (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.webp`).
- Optionally select a global prompt file.
- Images are pasted first, then text (if enabled).

### Image + Text Mode (Queue)

- Add multiple image folders, each with optional prompt file.
- Items have unique IDs and are removed deterministically when completed.
- Removing queue items during run is supported:
  - Not-yet-started items are skipped.
  - In-progress folder cancellation is cooperative (stops remaining images in that folder).

## Preflight and Dry Run

- `Preflight` validates selected inputs and reports:
  - window availability,
  - path validity,
  - estimated item count,
  - estimated duration.
- `Dry Run` simulates actions without sending paste events or moving source files.

## Prompt Variables

When enabled, placeholders in prompt text are replaced at runtime, for example:

- `{{filename}}`
- `{{file_stem}}`
- `{{file_ext}}`
- `{{folder}}`
- `{{index}}`
- `{{date}}`
- `{{time}}`
- `{{datetime}}`
- `{{mode}}`
- `{{title}}`

## Configuration

Settings persist in `settings.json`.

Important advanced keys:

- `dry_run`
- `paste_max_retries`
- `paste_retry_delay`
- `focus_retries`
- `skip_duplicates`
- `prompt_variables_enabled`
- `queue_snapshot_enabled`
- `queue_snapshot_file`
- `auto_resume_queue_from_snapshot`
- `enable_error_screenshots`
- `error_screenshot_dir`
- `profiles`

## Output and Artifacts

- Processed text files: `sent_prompts/`
- Processed images: `sent_images/`
- Failed items:
  - `sent_prompts/failed/`
  - `sent_images/failed/`
- Daily app log: `logs/prompt_sequencer_YYYYMMDD.log`
- Run summaries:
  - `logs/run_summary_*.json`
  - `logs/run_summary_history.csv`
- Queue snapshot: `logs/queue_snapshot.json`
- Duplicate history: `logs/processed_history.json`
- Error screenshots: `logs/error_screenshots/`

## CLI

```bash
# Basics
python cli.py deps
python cli.py windows
python cli.py focus --window "ChatGPT"
python cli.py strategies --window "Firefox"
python cli.py config
python cli.py sample_prompts
python cli.py test_parse --file "test_prompts\\nature.txt"

# Preflight
python cli.py preflight --mode text --folder "C:\\prompts"
python cli.py preflight --mode image --folder "C:\\images" --prompt-file "C:\\prompt.txt"
python cli.py preflight --mode queue

# Run
python cli.py run --mode text --folder "C:\\prompts" --preflight
python cli.py run --mode image --folder "C:\\images" --prompt-file "C:\\prompt.txt"
python cli.py run --mode queue --resume-snapshot

# Optional run flags
# --dry-run --skip-duplicates --profile NAME --window "ChatGPT" --start-at "2026-02-24 01:30"

# Watch mode
python cli.py watch --mode text --folder "C:\\prompts" --interval 10
python cli.py watch --mode image --folder "C:\\images" --prompt-file "C:\\prompt.txt"

# Quick test (single item; dry-run by default)
python cli.py quick_test --mode text --folder "C:\\prompts"
python cli.py quick_test --mode image --folder "C:\\images" --prompt-file "C:\\prompt.txt"
python cli.py quick_test --mode text --folder "C:\\prompts" --live

# Profiles
python cli.py profile_list
python cli.py profile_save --name "chatgpt_slow_network"
python cli.py profile_apply --name "chatgpt_slow_network"

# Resume queue snapshot
python cli.py resume_snapshot
```

## Testing

```bash
pytest -q
```

## Keyboard Safety

`pyautogui` failsafe is enabled: move mouse to top-left corner to emergency-stop automation.
