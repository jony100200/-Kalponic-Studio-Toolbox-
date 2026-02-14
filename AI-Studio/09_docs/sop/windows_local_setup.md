# Windows Local Setup (AI-Studio)

Use this once to turn your PC into a local multi-worker studio.

## 1) Core Tools

- Python 3.11+
- Git
- Node.js LTS (for n8n if running with npm)
- Optional GPU tooling (NVIDIA drivers/CUDA where needed)

## 2) AI Services (recommended)

- **Ollama** (local text model serving)
- **ComfyUI** (image generation worker backend)
- **n8n** (workflow automation/orchestrator)

You can use cloud APIs in parallel (OpenAI) while still running local services for bulk work.

## 3) Project Bootstrap

From the AI-Studio root:

```bat
copy config\.env.example config\.env
python scripts\health_check.py
```

Edit `config\.env` and set endpoints/API key as needed.

## 4) Service Start Order (manual)

1. Start Ollama service (`OLLAMA_BASE_URL`)
2. Start ComfyUI (`COMFYUI_BASE_URL`)
3. Start n8n (`N8N_BASE_URL`)
4. Run health check again

```bat
python scripts\health_check.py
```

## 5) First Job Smoke Test

```bat
python scripts\new_job.py --role writer --title "Studio setup smoke test" --priority medium
python scripts\route_next_job.py --dry-run
python scripts\route_next_job.py
```

Then check:
- `00_inbox/JOB-...json` status becomes `processing`
- `02_workers/<role>/inbox/JOB-...json` exists

## 6) Keep It Stable (KISS)

- One job card format for all workers
- One QA gate before approval
- Keep each worker role single-purpose
- Version outputs with `v1`, `v2`, etc.
