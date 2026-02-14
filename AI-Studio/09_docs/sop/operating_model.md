# AI-Studio Operating Model (KISS + SOLID)

## Principles

1. **Single Responsibility per worker**: each role does one type of job well.
2. **Structured inputs/outputs**: every task starts with a job card.
3. **Human approval before publish**: QA gate is mandatory.
4. **Short feedback loops**: draft fast, review, iterate.

## Standard Lifecycle

1. Drop/create job card in `00_inbox/`.
2. Move working brief to `01_briefs/`.
3. Route job by `role` using `config/worker_registry.json`.
4. Worker produces output in target folder.
5. QA reviews using `09_docs/templates/review_checklist.md`.
6. If pass -> `06_outputs/approved/`; if fail -> back to worker with notes.
7. Archive completed package to `08_archive/`.

## Status Conventions

- `inbox`
- `brief_ready`
- `processing`
- `review`
- `approved`
- `archived`

## Naming Conventions

- Job IDs: `JOB-YYYYMMDD-###`
- Review note files: `JOB-..._review.md`
- Outputs: `JOB-..._output_v#.ext`
