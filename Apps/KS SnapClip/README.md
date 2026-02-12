# KS SnapClip (MVP)

Lightweight, privacy-first screenshot app with clipboard-first workflow, in-memory history, and quick save.

## Features (MVP)
- Capture modes: Fullscreen, Area (placeholder for now)
- In-memory history (recent N captures)
- Copy to clipboard (Windows via pywin32 if available; fallback saves to temp)
- Save last capture to `captures/` folder
- Simple GUI (CustomTkinter)

## Run

1. Create and activate virtualenv
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app (from folder):

```powershell
python main.py
```

Or use the Windows launcher:

```powershell
run_ks_snapclip.bat
```

## Next steps / TODO
- Implement real area selection overlay for `capture_area()`
- Add hotkey support (opt-in)
- Add thumbnail gallery and history UI
- Add tests for clipboard behavior with pywin32 mocked

## Privacy
- Works offline; no telemetry by default

## Files
- `main.py` - launcher
- `ui.py` - UI and glue code
- `capture.py` - screenshot helpers
- `clipboard_win.py` - clipboard helper (Windows)
- `store.py` - in-memory history store
- `requirements.txt` - python deps
- `tests/` - smoke tests
