# RefRepos Sync System

This toolset keeps `RefRepos` ZIP snapshots up to date, inspects ZIP content without full extraction, and discovers new repos to collect.

## Files
- `Tools/RefRepoSync/refrepos_sync.py`: Main sync/inspect/discover CLI.
- `Tools/RefRepoSync/refrepos_manifest.json`: Source mapping and category routing.
- `Tools/RefRepoSync/run_refrepos_sync.bat`: One-click launcher.

## Quick Start
Run from terminal:

```powershell
python Tools/RefRepoSync/refrepos_sync.py sync --dry-run
python Tools/RefRepoSync/refrepos_sync.py sync
```

Or use BAT:

```cmd
Tools\RefRepoSync\run_refrepos_sync.bat sync --dry-run
Tools\RefRepoSync\run_refrepos_sync.bat sync
```

## Commands

### 1) `sync`
Resolves latest versions online (PyPI/GitHub), downloads ZIP snapshot/release, places it in the configured category, and removes older versions with the same filename prefix.

```powershell
python Tools/RefRepoSync/refrepos_sync.py sync --dry-run
python Tools/RefRepoSync/refrepos_sync.py sync --json-out Tools/RefRepoSync/reports/last_sync.json
```

Useful flags:
- `--dry-run`: Resolve only, no file changes.
- `--keep-old`: Keep older versions instead of deleting.
- `--ref-root "E:\__Kalponic Studio Repositories\RefRepos"`: Override root path.

### 2) `inspect`
Reads ZIP metadata and optionally README text directly from the ZIP (no full extraction by default).

```powershell
python Tools/RefRepoSync/refrepos_sync.py inspect --include-readme --json-out Tools/RefRepoSync/reports/inspect.json
```

Useful flags:
- `--include-readme`: Add README snippet and detected GitHub URLs.
- `--extract-fallback`: Use temp extraction only if README lookup fails.
- `--limit N`: Inspect first `N` ZIP files only.

### 3) `discover`
Runs GitHub repo search queries and returns candidate repos for future reference collection.

```powershell
python Tools/RefRepoSync/refrepos_sync.py discover --json-out Tools/RefRepoSync/reports/discover.json
python Tools/RefRepoSync/refrepos_sync.py discover --queries "youtube transcript pipeline python" "faster-whisper batch transcription"
```

Useful flags:
- `--per-query 12`
- `--min-stars 200`

## Manifest Notes
- `ref_root`: Absolute path to your `RefRepos` folder.
- `entries[]`: Each tracked reference source.
- `discovery_queries[]`: Default GitHub search terms.

To add a new tracked reference, append a new `entries[]` object with:
- `id`
- `category`
- `filename_prefix`
- `source` object (`pypi`, `github_release`, or `github_tag`)

## GitHub API Limits
- If you hit rate limits, set `GITHUB_TOKEN` in environment.

```powershell
$env:GITHUB_TOKEN="your_token_here"
```

