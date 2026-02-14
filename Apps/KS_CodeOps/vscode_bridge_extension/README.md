# KS CodeOps Bridge Extension

Minimal VS Code companion extension for KS CodeOps.

## Commands

- `KS CodeOps: Write Clipboard to Bridge`
  - Reads clipboard text and writes it to `.ks_codeops/bridge/latest_response.txt` in the current workspace.
- `KS CodeOps: Open Bridge Response File`
  - Opens the bridge response file for inspection.

## Usage with KS CodeOps

1. Copy AI response text from the chat panel.
2. Run `KS CodeOps: Write Clipboard to Bridge`.
3. In KS CodeOps step config, use capture:

```json
{
  "capture": { "source": "bridge" },
  "output_file": "outputs/step_01.md"
}
```

4. Run `python cli.py run-job --dir <job_dir>`.
