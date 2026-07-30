"""store.read_snapshot_dict: a missing or corrupt snapshot raises a named error (F1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aspark_insights.errors import SnapshotUnreadableError
from aspark_insights.store import latest_snapshot_path, read_snapshot_dict, require_snapshot_shape, snapshots_dir


def test_read_snapshot_dict_raises_named_error_on_missing_file(tmp_path: Path):
    with pytest.raises(SnapshotUnreadableError):
        read_snapshot_dict(tmp_path / "does-not-exist.json")


def test_read_snapshot_dict_raises_named_error_on_invalid_json(tmp_path: Path):
    path = tmp_path / "corrupt.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SnapshotUnreadableError):
        read_snapshot_dict(path)


def test_require_snapshot_shape_raises_named_error_on_wrong_shape_json(tmp_path: Path):
    """F5: valid JSON that isn't a snapshot must raise a named error, not a KeyError."""
    with pytest.raises(SnapshotUnreadableError):
        require_snapshot_shape({}, tmp_path / "not-a-snapshot.json")
    with pytest.raises(SnapshotUnreadableError):
        require_snapshot_shape({"facts": [], "metrics": [], "provenance": {}}, tmp_path / "x.json")


def test_require_snapshot_shape_accepts_a_real_snapshot_dict(tmp_path: Path):
    require_snapshot_shape(
        {"facts": [], "metrics": [], "provenance": {"as_of": "2026-07-29"}},
        tmp_path / "ok.json",
    )


def test_latest_snapshot_path_ignores_non_date_shaped_filenames(tmp_path: Path):
    """B3: a stray/bogus filename must never outrank a real snapshot lexicographically."""
    d = snapshots_dir(tmp_path)
    d.mkdir(parents=True)
    (d / "2026-07-15.json").write_text("{}", encoding="utf-8")
    (d / "2026-08-01.json").write_text("{}", encoding="utf-8")
    # "not-a-date" and "2099-01-01" both sort after "2026-08-01" lexicographically,
    # but neither is a real snapshot this tool wrote under the current --as-of contract.
    (d / "not-a-date.json").write_text("{}", encoding="utf-8")
    (d / "2099-01-01.json").write_text("{}", encoding="utf-8")

    latest = latest_snapshot_path(tmp_path)
    assert latest is not None
    assert latest.name == "2099-01-01.json"  # real date-shaped names still compare correctly


def test_latest_snapshot_path_with_only_bogus_filenames_returns_none(tmp_path: Path):
    d = snapshots_dir(tmp_path)
    d.mkdir(parents=True)
    (d / "not-a-date.json").write_text("{}", encoding="utf-8")
    assert latest_snapshot_path(tmp_path) is None
