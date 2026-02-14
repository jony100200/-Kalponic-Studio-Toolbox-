# Scripts Reference

## `health_check.py`

Checks:
- required folder/file scaffold
- worker registry validity
- configured service endpoint reachability

Run:

```bat
python scripts\health_check.py
```

## `new_job.py`

Creates a new job card in `00_inbox/` and a paired brief in `01_briefs/`.

Run:

```bat
python scripts\new_job.py --role writer --title "Homepage copy" --priority high --owner ahme0
```

## `route_next_job.py`

Routes the next eligible inbox job (`inbox` or `brief_ready`) into the selected role queue under `02_workers/<role>/inbox/` and updates job status to `processing`.

Run:

```bat
python scripts\route_next_job.py
python scripts\route_next_job.py --dry-run
python scripts\route_next_job.py --job-id JOB-YYYYMMDD-001
```
