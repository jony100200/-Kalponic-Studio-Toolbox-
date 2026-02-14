$ErrorActionPreference = "Stop"

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python scripts/sync_roadmap.py --apply
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python scripts/sync_roadmap.py --check
exit $LASTEXITCODE
