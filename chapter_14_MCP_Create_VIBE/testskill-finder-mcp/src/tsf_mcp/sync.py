"""Download the upstream skill catalog from GitHub into the local skills folder.

Only files under the upstream skills path are written. Local skills that do not exist
upstream are never touched or deleted. Downloaded files are stored as data and never run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

from tsf_mcp import config


@dataclass
class SyncReport:
    repo: str
    ref: str
    commit: str
    dry_run: bool
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "ref": self.ref,
            "commit": self.commit,
            "dry_run": self.dry_run,
            "counts": {"added": len(self.added), "updated": len(self.updated), "unchanged": len(self.unchanged), "skipped": len(self.skipped)},
            "added": self.added,
            "updated": self.updated,
            "skipped": self.skipped,
        }


def _safe_relative(path: str) -> PurePosixPath | None:
    rel = PurePosixPath(path)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
        return None
    return rel


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "testskill-finder-mcp"}
    token = config.github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def sync_from_github(
    target: Path,
    *,
    repo: str = config.UPSTREAM_REPO,
    ref: str = config.UPSTREAM_REF,
    upstream_path: str = config.UPSTREAM_PATH,
    dry_run: bool = False,
    client: httpx.Client | None = None,
) -> SyncReport:
    own_client = client is None
    http = client or httpx.Client(timeout=30.0, follow_redirects=True)
    try:
        commit_resp = http.get(f"https://api.github.com/repos/{repo}/commits/{ref}", headers=_headers())
        commit_resp.raise_for_status()
        commit = commit_resp.json()["sha"]

        tree_resp = http.get(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1", headers=_headers())
        tree_resp.raise_for_status()
        prefix = upstream_path.rstrip("/") + "/"
        blobs = [item for item in tree_resp.json()["tree"] if item["type"] == "blob" and item["path"].startswith(prefix)]
        if len(blobs) > config.SYNC_MAX_FILES:
            raise RuntimeError(f"Upstream has {len(blobs)} files; refusing to sync more than {config.SYNC_MAX_FILES}.")

        report = SyncReport(repo=repo, ref=ref, commit=commit, dry_run=dry_run)
        written: list[str] = []
        target = target.resolve()
        for item in blobs:
            rel = _safe_relative(item["path"][len(prefix):])
            if rel is None or rel.name == config.MANIFEST_NAME:
                report.skipped.append(item["path"])
                continue
            if item.get("size", 0) > config.SYNC_MAX_FILE_BYTES:
                report.skipped.append(f"{rel} (too large)")
                continue
            destination = (target / rel).resolve()
            if target not in destination.parents:
                report.skipped.append(f"{rel} (outside target)")
                continue

            raw = http.get(f"https://raw.githubusercontent.com/{repo}/{commit}/{item['path']}", headers={"User-Agent": "testskill-finder-mcp"})
            raw.raise_for_status()
            content = raw.content
            if destination.exists():
                if destination.read_bytes() == content:
                    report.unchanged.append(str(rel))
                    written.append(str(rel))
                    continue
                report.updated.append(str(rel))
            else:
                report.added.append(str(rel))
            written.append(str(rel))
            if not dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)

        if not dry_run:
            manifest = {
                "repo": repo,
                "ref": ref,
                "commit": commit,
                "upstream_path": upstream_path,
                "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "files": sorted(written),
            }
            (target / config.MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        if own_client:
            http.close()


def read_manifest(target: Path) -> dict[str, Any] | None:
    path = target / config.MANIFEST_NAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
