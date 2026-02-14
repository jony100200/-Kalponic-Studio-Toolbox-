# Troubleshooting Matrix

This guide covers the most common failure modes when orchestrating VS Code extension workers (Copilot, Codex, Cline, Gemini, Kilo).

## Quick Triage

1. Run `python cli.py health-check --names copilot`.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python scripts/sync_roadmap.py --check`.

If step 1 fails, fix runtime targeting/focus first.  
If step 2 fails, fix code-level regressions first.  
If step 3 fails, roadmap state is stale and needs sync/apply.

## Failure Matrix

| Symptom | Likely Cause | Verification | Fix |
|---|---|---|---|
| `test-target` or `health-check` fails to type in chat | Wrong target panel, wrong click point, VS Code not focused | `python cli.py self-test-targets --names copilot` | Recalibrate click (`record-target-click`), verify `window_title`, retry |
| `run-job` fails with validation error | Output file missing or capture produced empty output | Check `jobs/<job>/artifacts/<step>/attempt_*` files | Fix prompt contract markers, capture source, or validator |
| `run-job` exits with failure code | Step failed after retries | Confirm `status.json` has `state: failed` | Read `log.txt`, fix step data/prompt/target, rerun |
| `materialize-app` raises unsafe path error | Generated output contains absolute/path-traversal `FILE:` paths | Inspect source markdown `FILE:` lines | Keep only workspace-relative paths in generated output |
| `test-sequence` seems inconsistent across runs | Safe mode skips strict cross-target verification unless open commands enabled | Check logs for `[SEQUENCE] SKIP` lines | Use `--open-commands` when you intentionally need strict cross-target checks |
| Roadmap checkboxes become inaccurate | Work completed but sync not run | `python scripts/sync_roadmap.py --check` | Run `python scripts/sync_roadmap.py --apply` |

## High-Value Commands

```powershell
python cli.py targets
python cli.py health-check --names copilot
python cli.py self-test-targets --names copilot
python cli.py run-job --dir jobs/ks_pdf_studio_v2
python -m unittest discover -s tests -v
python scripts/sync_roadmap.py --apply
```

## Escalation Rule

If runtime worker targeting is unstable, do not continue multi-target runs.  
Use Copilot-first single-target flow until `health-check` and tests are green.
