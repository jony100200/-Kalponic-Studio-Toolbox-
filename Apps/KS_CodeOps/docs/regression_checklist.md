# Pre-Run Regression Checklist

Run this checklist before marking a part complete or starting a high-value job run.

## A) Code Health

- [ ] `python -m py_compile cli.py src/core/job_runner.py src/core/materializer.py src/core/sequencer.py src/core/step_validator.py`
- [ ] `python -m unittest discover -s tests -v`

## B) Runtime Targeting Health

- [ ] `python cli.py targets`
- [ ] `python cli.py health-check --names copilot`
- [ ] If testing multiple workers: `python cli.py health-check --names copilot gemini codex kilo cline --open-commands`

## C) Job Pipeline Smoke

- [ ] `python cli.py run-job --dir jobs/simple_app_test`
- [ ] `python cli.py materialize-app --source jobs/simple_app_test/outputs/app_spec.md --out generated_apps/tiny_app`
- [ ] Confirm generated files exist and open cleanly

## D) Roadmap + Release Hygiene

- [ ] `python scripts/sync_roadmap.py --apply`
- [ ] `python scripts/sync_roadmap.py --check`

## One-Command Shortcut

```powershell
.\scripts\part_done.ps1
```

or

```cmd
scripts\part_done.bat
```

## Stop Conditions

Stop release progress and fix immediately if any of these occur:

- Runtime health-check fails for the intended worker set.
- Unit/integration tests fail.
- Roadmap sync check fails.
- `run-job` returns non-zero for baseline smoke jobs.
