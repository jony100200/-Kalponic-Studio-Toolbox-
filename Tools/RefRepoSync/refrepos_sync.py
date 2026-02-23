#!/usr/bin/env python3
"""
RefRepos sync and discovery utility.

Main capabilities:
1) Sync ZIP snapshots from online sources (manifest-driven).
2) Inspect ZIP files and read README content without full extraction.
3) Discover useful GitHub repos for future reference collection.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ARCHIVE_EXTENSIONS = (".zip", ".tar.gz", ".whl")
README_NAME_RE = re.compile(r"(^|/)(readme)(\.[a-z0-9]+)?$", re.IGNORECASE)
GITHUB_URL_RE = re.compile(r"https?://github\.com/[^\s)>\"]+", re.IGNORECASE)


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(msg: str) -> None:
    print(msg)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def github_headers() -> Dict[str, str]:
    headers = {"User-Agent": "RefRepoSync/1.0"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_get_bytes(url: str, timeout: int = 60, headers: Optional[Dict[str, str]] = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "RefRepoSync/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_json(url: str, timeout: int = 60, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    raw = http_get_bytes(url=url, timeout=timeout, headers=headers)
    return json.loads(raw.decode("utf-8"))


def http_head_ok(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers=headers or {"User-Agent": "RefRepoSync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def sanitize_version(version: str) -> str:
    out = version.strip()
    out = out[1:] if out.lower().startswith("v") else out
    out = re.sub(r"[^A-Za-z0-9._-]+", ".", out)
    out = re.sub(r"\.+", ".", out).strip(".")
    return out or "unknown"


def archive_ext_from_url(url: str, default_ext: str = ".zip") -> str:
    lower = url.lower()
    for ext in ARCHIVE_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    return default_ext


def atomic_download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="refsync_", suffix=".part", dir=str(destination.parent))
    os.close(tmp_fd)
    tmp_file = Path(tmp_path)
    try:
        data = http_get_bytes(url, timeout=180, headers=github_headers())
        with tmp_file.open("wb") as f:
            f.write(data)
        tmp_file.replace(destination)
    finally:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError:
                pass


def delete_old_archives(category_dir: Path, filename_prefix: str, keep_name: str) -> List[str]:
    deleted: List[str] = []
    prefix = filename_prefix.lower() + "-"
    for f in category_dir.iterdir():
        if not f.is_file():
            continue
        lname = f.name.lower()
        if not lname.startswith(prefix):
            continue
        if f.name == keep_name:
            continue
        if not lname.endswith(ARCHIVE_EXTENSIONS):
            continue
        try:
            f.unlink()
            deleted.append(f.name)
        except OSError:
            pass
    return deleted


def find_exact_github_tag(repo: str, version: str) -> Optional[str]:
    version = sanitize_version(version)
    candidates = [f"v{version}", version]
    for tag in candidates:
        url = f"https://codeload.github.com/{repo}/zip/refs/tags/{tag}"
        if http_head_ok(url, headers=github_headers()):
            return tag
    return None


def github_latest_release(repo: str, include_prerelease: bool = False) -> Optional[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo}/releases?per_page=30"
    releases = http_get_json(url, headers=github_headers())
    if not isinstance(releases, list):
        return None
    for rel in releases:
        if not isinstance(rel, dict):
            continue
        if rel.get("draft"):
            continue
        if not include_prerelease and rel.get("prerelease"):
            continue
        return rel
    return None


def choose_release_asset(release: Dict[str, Any], asset_regex: str = "") -> Optional[str]:
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        assets = []
    rex = re.compile(asset_regex, re.IGNORECASE) if asset_regex else None

    if rex:
        for a in assets:
            name = str(a.get("name", ""))
            if rex.search(name):
                return str(a.get("browser_download_url", ""))

    for a in assets:
        name = str(a.get("name", "")).lower()
        if name.endswith(".zip"):
            return str(a.get("browser_download_url", ""))

    zipball = str(release.get("zipball_url", "")).strip()
    return zipball or None


def pypi_project(pkg: str) -> Dict[str, Any]:
    return http_get_json(f"https://pypi.org/pypi/{pkg}/json", headers={"User-Agent": "RefRepoSync/1.0"})


def choose_pypi_file_url(pypi_payload: Dict[str, Any]) -> Optional[str]:
    info = pypi_payload.get("info", {}) if isinstance(pypi_payload, dict) else {}
    version = str(info.get("version", "")).strip()
    releases = pypi_payload.get("releases", {}) if isinstance(pypi_payload, dict) else {}
    files = releases.get(version, []) if isinstance(releases, dict) else []
    if not isinstance(files, list):
        return None

    # Prefer .zip source, then tar.gz, then wheel
    preferred_order = (".zip", ".tar.gz", ".whl")
    for ext in preferred_order:
        for file_entry in files:
            filename = str(file_entry.get("filename", "")).lower()
            if filename.endswith(ext):
                return str(file_entry.get("url", "")).strip()
    return None


@dataclass
class SyncResult:
    entry_id: str
    status: str
    detail: str
    file_path: str = ""
    deleted_files: Optional[List[str]] = None


def resolve_source(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Returns tuple: (version, download_url, extension)
    Raises ValueError on resolution failure.
    """
    source = entry.get("source", {})
    stype = str(source.get("type", "")).strip().lower()

    if stype == "pypi":
        pkg = str(source.get("package", "")).strip()
        if not pkg:
            raise ValueError("source.package is required for pypi type")

        payload = pypi_project(pkg)
        version = sanitize_version(str(payload.get("info", {}).get("version", "")))
        if not version:
            raise ValueError("could not resolve pypi version")

        download_mode = str(source.get("download", "github_tag_zip")).strip().lower()
        repo = str(source.get("repo", "")).strip()

        if download_mode == "github_tag_zip" and repo:
            strict = bool(source.get("strict_version_tag", True))
            tag = find_exact_github_tag(repo=repo, version=version)
            if not tag and strict:
                raise ValueError(f"no exact github tag found for version {version}")
            if tag:
                url = f"https://codeload.github.com/{repo}/zip/refs/tags/{tag}"
                return version, url, ".zip"

        pypi_url = choose_pypi_file_url(payload)
        if not pypi_url:
            raise ValueError("no downloadable pypi file found")
        return version, pypi_url, archive_ext_from_url(pypi_url, default_ext=".zip")

    if stype == "github_release":
        repo = str(source.get("repo", "")).strip()
        if not repo:
            raise ValueError("source.repo is required for github_release type")
        include_pr = bool(source.get("include_prerelease", False))
        release = github_latest_release(repo=repo, include_prerelease=include_pr)
        if not release:
            raise ValueError("no github release found")
        tag_name = str(release.get("tag_name", "")).strip()
        version = sanitize_version(tag_name or "latest")
        asset_regex = str(source.get("asset_regex", "")).strip()
        url = choose_release_asset(release=release, asset_regex=asset_regex)
        if not url:
            raise ValueError("no downloadable github release asset/zipball found")
        return version, url, archive_ext_from_url(url, default_ext=".zip")

    if stype == "github_tag":
        repo = str(source.get("repo", "")).strip()
        tag = str(source.get("tag", "")).strip()
        if not repo:
            raise ValueError("source.repo is required for github_tag type")
        if not tag:
            raise ValueError("source.tag is required for github_tag type")
        version = sanitize_version(tag)
        url = f"https://codeload.github.com/{repo}/zip/refs/tags/{tag}"
        if not http_head_ok(url, headers=github_headers()):
            raise ValueError(f"tag archive not found: {tag}")
        return version, url, ".zip"

    if stype == "github_latest_tag":
        repo = str(source.get("repo", "")).strip()
        if not repo:
            raise ValueError("source.repo is required for github_latest_tag type")
        tag_regex = str(source.get("tag_regex", "")).strip()
        rex = re.compile(tag_regex) if tag_regex else None

        tags = http_get_json(
            f"https://api.github.com/repos/{repo}/tags?per_page=100",
            headers=github_headers(),
        )
        if not isinstance(tags, list) or not tags:
            raise ValueError("no github tags found")

        selected_tag = ""
        for tag_item in tags:
            if not isinstance(tag_item, dict):
                continue
            name = str(tag_item.get("name", "")).strip()
            if not name:
                continue
            if rex and not rex.search(name):
                continue
            selected_tag = name
            break

        if not selected_tag:
            raise ValueError("no github tag matched tag_regex")

        version = sanitize_version(selected_tag)
        url = f"https://codeload.github.com/{repo}/zip/refs/tags/{selected_tag}"
        if not http_head_ok(url, headers=github_headers()):
            raise ValueError(f"selected tag archive not reachable: {selected_tag}")
        return version, url, ".zip"

    raise ValueError(f"unsupported source.type: {stype}")


def sync_entries(
    manifest: Dict[str, Any],
    ref_root: Path,
    dry_run: bool,
    keep_old: bool,
) -> List[SyncResult]:
    results: List[SyncResult] = []
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        return [SyncResult(entry_id="manifest", status="error", detail="manifest entries must be a list")]

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("enabled", True) is False:
            continue

        entry_id = str(entry.get("id", "unnamed")).strip() or "unnamed"
        category = str(entry.get("category", "")).strip()
        prefix = str(entry.get("filename_prefix", entry_id)).strip()
        if not category:
            results.append(SyncResult(entry_id=entry_id, status="error", detail="missing category"))
            continue
        if not prefix:
            results.append(SyncResult(entry_id=entry_id, status="error", detail="missing filename_prefix"))
            continue

        category_dir = ref_root / category
        category_dir.mkdir(parents=True, exist_ok=True)

        try:
            version, url, ext = resolve_source(entry)
            ext = ext if ext.startswith(".") else "." + ext
            target_name = f"{prefix}-{version}{ext}"
            target_path = category_dir / target_name

            if dry_run:
                deleted = [] if keep_old else [f.name for f in category_dir.glob(f"{prefix}-*") if f.name != target_name]
                results.append(
                    SyncResult(
                        entry_id=entry_id,
                        status="dry_run",
                        detail=f"would download {url}",
                        file_path=str(target_path),
                        deleted_files=deleted,
                    )
                )
                continue

            if not target_path.exists() or target_path.stat().st_size == 0:
                atomic_download(url=url, destination=target_path)

            deleted = [] if keep_old else delete_old_archives(category_dir=category_dir, filename_prefix=prefix, keep_name=target_name)
            results.append(
                SyncResult(
                    entry_id=entry_id,
                    status="updated",
                    detail=f"resolved version {version}",
                    file_path=str(target_path),
                    deleted_files=deleted,
                )
            )
        except Exception as exc:
            results.append(SyncResult(entry_id=entry_id, status="error", detail=str(exc)))

    return results


def read_readme_from_zip(zip_path: Path, max_chars: int = 3000, extract_fallback: bool = False) -> Tuple[str, str]:
    """
    Returns tuple: (readme_path_inside_zip, readme_text_snippet)
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            candidates = [n for n in names if README_NAME_RE.search(n)]
            candidates.sort(key=lambda n: (n.count("/"), len(n)))
            if candidates:
                target = candidates[0]
                raw = zf.read(target)
                for enc in ("utf-8", "utf-16", "latin-1"):
                    try:
                        txt = raw.decode(enc, errors="ignore")
                        return target, txt[:max_chars]
                    except Exception:
                        continue
                return target, raw[:max_chars].decode("utf-8", errors="ignore")
    except Exception:
        pass

    if not extract_fallback:
        return "", ""

    with tempfile.TemporaryDirectory(prefix="refrepo_inspect_") as td:
        tmp = Path(td)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)
            for cand in sorted(tmp.rglob("*")):
                if cand.is_file() and cand.name.lower().startswith("readme"):
                    text = cand.read_text(encoding="utf-8", errors="ignore")
                    rel = str(cand.relative_to(tmp)).replace("\\", "/")
                    return rel, text[:max_chars]
        except Exception:
            return "", ""
    return "", ""


def inspect_zips(
    ref_root: Path,
    include_readme: bool,
    extract_fallback: bool,
    limit: int,
) -> Dict[str, Any]:
    zips = sorted(ref_root.rglob("*.zip"))
    if limit > 0:
        zips = zips[:limit]

    items: List[Dict[str, Any]] = []
    for zp in zips:
        rel = str(zp.relative_to(ref_root)).replace("\\", "/")
        item: Dict[str, Any] = {
            "file": rel,
            "size_bytes": zp.stat().st_size,
            "modified": dt.datetime.fromtimestamp(zp.stat().st_mtime).isoformat(),
        }
        if include_readme:
            readme_path, snippet = read_readme_from_zip(zp, max_chars=2500, extract_fallback=extract_fallback)
            urls = sorted(set(GITHUB_URL_RE.findall(snippet)))
            item["readme_path"] = readme_path
            item["readme_snippet"] = snippet
            item["github_urls"] = urls
        items.append(item)

    return {
        "generated_at": utc_now_iso(),
        "ref_root": str(ref_root),
        "zip_count": len(items),
        "items": items,
    }


def discover_github_repos(
    queries: Iterable[str],
    per_query: int,
    min_stars: int,
) -> Dict[str, Any]:
    out: List[Dict[str, Any]] = []
    headers = github_headers()
    for q in queries:
        q = q.strip()
        if not q:
            continue
        encoded = urllib.parse.quote(q)
        url = (
            "https://api.github.com/search/repositories"
            f"?q={encoded}&sort=stars&order=desc&per_page={max(1, min(per_query, 50))}"
        )
        try:
            payload = http_get_json(url, headers=headers)
        except urllib.error.HTTPError as exc:
            out.append({"query": q, "error": f"http {exc.code}"})
            continue
        except Exception as exc:
            out.append({"query": q, "error": str(exc)})
            continue

        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            items = []

        results = []
        for it in items:
            if not isinstance(it, dict):
                continue
            stars = int(it.get("stargazers_count", 0))
            if stars < min_stars:
                continue
            if it.get("archived"):
                continue
            results.append(
                {
                    "name": it.get("full_name"),
                    "url": it.get("html_url"),
                    "description": it.get("description"),
                    "stars": stars,
                    "updated_at": it.get("updated_at"),
                    "topics": it.get("topics", []),
                }
            )
        out.append({"query": q, "results": results})

    return {"generated_at": utc_now_iso(), "queries": out}


def build_parser() -> argparse.ArgumentParser:
    script_dir = Path(__file__).resolve().parent
    default_manifest = script_dir / "refrepos_manifest.json"

    parser = argparse.ArgumentParser(description="RefRepos updater and discovery system")
    parser.add_argument("--manifest", default=str(default_manifest), help="Path to manifest JSON")
    parser.add_argument("--ref-root", default="", help="Override reference root directory")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="Sync references from manifest")
    p_sync.add_argument("--dry-run", action="store_true", help="Resolve versions/URLs without writing files")
    p_sync.add_argument("--keep-old", action="store_true", help="Do not delete older archives")
    p_sync.add_argument("--json-out", default="", help="Optional JSON report output path")

    p_inspect = sub.add_parser("inspect", help="Inspect ZIPs and read README snippets")
    p_inspect.add_argument("--include-readme", action="store_true", help="Include README snippet from each ZIP")
    p_inspect.add_argument("--extract-fallback", action="store_true", help="Use temp extraction if ZIP readme detection fails")
    p_inspect.add_argument("--limit", type=int, default=0, help="Limit number of ZIPs inspected (0 = all)")
    p_inspect.add_argument("--json-out", default="", help="Optional JSON report output path")

    p_discover = sub.add_parser("discover", help="Discover useful repos from GitHub search")
    p_discover.add_argument("--queries", nargs="*", default=[], help="Discovery queries (fallback to manifest queries)")
    p_discover.add_argument("--per-query", type=int, default=12, help="Max repos per query (<=50)")
    p_discover.add_argument("--min-stars", type=int, default=200, help="Minimum stars filter")
    p_discover.add_argument("--json-out", default="", help="Optional JSON report output path")

    return parser


def resolve_ref_root(manifest: Dict[str, Any], arg_ref_root: str) -> Path:
    if arg_ref_root.strip():
        return Path(arg_ref_root).expanduser().resolve()
    env = os.environ.get("REF_REPOS_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    from_manifest = str(manifest.get("ref_root", "")).strip()
    if from_manifest:
        return Path(from_manifest).expanduser().resolve()
    raise ValueError("Ref root is not set. Use --ref-root, REF_REPOS_ROOT env, or manifest ref_root.")


def print_sync_summary(results: List[SyncResult]) -> None:
    ok = sum(1 for r in results if r.status in {"updated", "dry_run"})
    err = sum(1 for r in results if r.status == "error")
    log(f"[sync] completed: ok={ok}, errors={err}, total={len(results)}")
    for r in results:
        line = f" - {r.entry_id}: {r.status} | {r.detail}"
        if r.file_path:
            line += f" | file={r.file_path}"
        if r.deleted_files is not None:
            line += f" | deleted={r.deleted_files}"
        log(line)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    if not manifest_path.exists():
        log(f"[error] manifest not found: {manifest_path}")
        return 2

    manifest = read_json(manifest_path)
    try:
        ref_root = resolve_ref_root(manifest=manifest, arg_ref_root=args.ref_root)
    except Exception as exc:
        log(f"[error] {exc}")
        return 2

    if args.cmd == "sync":
        dry_run = bool(args.dry_run)
        keep_old = bool(args.keep_old) or bool(manifest.get("default_keep_old_versions", False))
        results = sync_entries(manifest=manifest, ref_root=ref_root, dry_run=dry_run, keep_old=keep_old)
        print_sync_summary(results)
        payload = {
            "generated_at": utc_now_iso(),
            "manifest": str(manifest_path),
            "ref_root": str(ref_root),
            "dry_run": dry_run,
            "keep_old": keep_old,
            "results": [r.__dict__ for r in results],
        }
        json_out = str(args.json_out).strip()
        if json_out:
            write_json(Path(json_out).expanduser().resolve(), payload)
            log(f"[sync] report: {json_out}")
        return 0 if not any(r.status == "error" for r in results) else 1

    if args.cmd == "inspect":
        payload = inspect_zips(
            ref_root=ref_root,
            include_readme=bool(args.include_readme),
            extract_fallback=bool(args.extract_fallback),
            limit=max(0, int(args.limit)),
        )
        log(f"[inspect] zip_count={payload.get('zip_count', 0)} ref_root={ref_root}")
        json_out = str(args.json_out).strip()
        if json_out:
            write_json(Path(json_out).expanduser().resolve(), payload)
            log(f"[inspect] report: {json_out}")
        return 0

    if args.cmd == "discover":
        queries = [q for q in args.queries if q.strip()]
        if not queries:
            q_from_manifest = manifest.get("discovery_queries", [])
            if isinstance(q_from_manifest, list):
                queries = [str(q).strip() for q in q_from_manifest if str(q).strip()]

        if not queries:
            log("[discover] no queries provided (use --queries or manifest.discovery_queries)")
            return 2

        payload = discover_github_repos(
            queries=queries,
            per_query=max(1, min(int(args.per_query), 50)),
            min_stars=max(0, int(args.min_stars)),
        )
        log(f"[discover] queries={len(payload.get('queries', []))}")
        json_out = str(args.json_out).strip()
        if json_out:
            write_json(Path(json_out).expanduser().resolve(), payload)
            log(f"[discover] report: {json_out}")
        return 0

    log("[error] unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
