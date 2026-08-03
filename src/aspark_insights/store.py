"""Snapshot storage under `.aspark-insights/` — derived state, deletable, rebuildable."""

from __future__ import annotations

import json
import re
from pathlib import Path

from aspark_insights.errors import SnapshotUnreadableError
from aspark_insights.model.snapshot import Snapshot
from aspark_insights.serialization import canonical_json

STORE_DIRNAME = ".aspark-insights"

# Matches build_snapshot's validated `as_of` shape exactly — a file that doesn't
# match isn't one this tool wrote as a real snapshot, and must never be able to
# outrank a real one when resolving "the last snapshot" (B3).
_SNAPSHOT_FILENAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def snapshots_dir(repo_root: str | Path) -> Path:
    return Path(repo_root) / STORE_DIRNAME / "snapshots"


def snapshot_path(repo_root: str | Path, as_of: str) -> Path:
    return snapshots_dir(repo_root) / f"{as_of}.json"


def write_snapshot(repo_root: str | Path, snapshot: Snapshot) -> Path:
    path = snapshot_path(repo_root, snapshot.provenance.as_of)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(snapshot.to_dict()), encoding="utf-8")
    return path


def read_snapshot_dict(path: str | Path) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8")
        return json.loads(text)
    except OSError as exc:
        raise SnapshotUnreadableError(f"cannot read snapshot at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotUnreadableError(f"snapshot at {path} is not valid JSON: {exc}") from exc


REQUIRED_SNAPSHOT_KEYS = ("facts", "metrics", "provenance")


def require_snapshot_shape(data: dict, path: str | Path) -> None:
    """A file can be valid JSON and still not be a snapshot — callers that index
    `data` directly (query, verify) must check this first, or a wrong-shape file
    raises a raw `KeyError`/`TypeError` instead of the named error NFR-3 requires."""
    if not isinstance(data, dict):
        raise SnapshotUnreadableError(
            f"snapshot at {path} is not a JSON object (got {type(data).__name__})"
        )
    missing = [key for key in REQUIRED_SNAPSHOT_KEYS if key not in data]
    if missing:
        raise SnapshotUnreadableError(
            f"snapshot at {path} is missing required field(s): {', '.join(missing)}"
        )
    if "as_of" not in data.get("provenance", {}):
        raise SnapshotUnreadableError(f"snapshot at {path} provenance is missing 'as_of'")


def latest_snapshot_path(repo_root: str | Path) -> Path | None:
    """The snapshot with the lexicographically greatest `as_of` filename.

    Sorted by filename, not filesystem mtime — mtime would smuggle wall-clock
    ordering into a derivation-adjacent decision (ADR-4). Only real
    `YYYY-MM-DD.json` names are considered, so a stray or malformed file in the
    store can't silently outrank an actual snapshot (B3).
    """
    d = snapshots_dir(repo_root)
    if not d.exists():
        return None
    paths = sorted(p for p in d.glob("*.json") if _SNAPSHOT_FILENAME_PATTERN.match(p.name))
    return paths[-1] if paths else None
