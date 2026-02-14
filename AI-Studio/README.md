## AI-Studio (Local Worker Studio)

This is a clean workspace to run your local “AI employees” (writer, artist, programmer, YouTube producer, QA) with a simple pipeline.

## Pipeline

`00_inbox -> 01_briefs -> 02_workers -> 07_reviews -> 06_outputs -> 08_archive`

## Folder Guide

- `00_inbox/` raw incoming jobs (JSON cards)
- `01_briefs/` cleaned project briefs
- `02_workers/` role-specific worker spaces
  - `writer/`
  - `artist_comfyui/`
  - `programmer/`
  - `youtube/`
  - `qa/`
- `03_workflows/` automation definitions and stubs
  - `n8n/`
  - `comfyui/`
- `04_projects/` active project folders
- `05_assets/` source assets
- `06_outputs/` generated results (`drafts/`, `approved/`)
- `07_reviews/` QA review artifacts
- `08_archive/` completed jobs
- `09_docs/` prompts, SOP, and templates
- `10_logs/` execution logs
- `config/` runtime settings and worker registry
- `scripts/` utility scripts

---

## 60-Second Quick Start (Windows)

1. Create your local env file:

```bat
copy config\.env.example config\.env
```

2. Run health check:

```bat
python scripts\health_check.py
```

3. Create first job (example: Writer):

```bat
python scripts\new_job.py --role writer --title "Homepage copy draft" --priority high
```

4. Route it to the role queue:

```bat
python scripts\route_next_job.py --dry-run
python scripts\route_next_job.py
```

5. Edit the generated brief in `01_briefs/` and execute the selected worker process.
6. Run QA checklist in `07_reviews/`.
7. Move final output to `06_outputs/approved/`.

---

## Key Files

- `config/worker_registry.json` role routing and output defaults
- `09_docs/templates/task_brief_template.md` brief template
- `09_docs/templates/job_card_template.json` job schema template
- `09_docs/templates/review_checklist.md` QA gate checklist
- `09_docs/prompts/` worker prompt templates
- `09_docs/sop/` operating model and daily runbook
- `scripts/README.md` script usage guide

## Automation Next Step

When ready, import `03_workflows/n8n/studio_pipeline_stub.json` into n8n and connect:
- inbox parser
- role router
- worker execution
- review and archive moves
