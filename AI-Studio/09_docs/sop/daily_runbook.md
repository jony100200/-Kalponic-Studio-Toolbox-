# Daily Runbook (Operator)

## Start of Day (5 minutes)

1. Pull latest repo changes (if using git).
2. Run health check:

```bat
python scripts\health_check.py
```

3. Confirm service status (Ollama, n8n, ComfyUI).

## New Work Intake

1. Create job:

```bat
python scripts\new_job.py --role writer --title "<task title>" --priority medium
```

2. Fill in generated brief in `01_briefs/`.
3. Route next job:

```bat
python scripts\route_next_job.py
```

## Worker Execution

- Open role prompt template from `09_docs/prompts/`
- Run the assigned worker flow/tool
- Save outputs to `06_outputs/drafts/` (or configured folder)

## QA Gate

1. Use `09_docs/templates/review_checklist.md`
2. Record review note in `07_reviews/`
3. PASS -> move to `06_outputs/approved/`
4. FAIL -> send revision notes to worker

## End of Day

- Archive completed jobs into `08_archive/`
- Keep logs in `10_logs/`
- Note blockers for tomorrow
