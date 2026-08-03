"""T3: the `query` tool returns a clean, named error dict — never a raised
exception through the stdio transport (AC-1.4, NFR-3).

Parity with the CLI's own behaviour: `insights query` exits 1 with a named
error on stderr; the MCP tool must reach the same two reasons without ever
raising.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aspark_insights import server


def test_query_tool_no_snapshot_returns_clean_error(tmp_path: Path):
    server._location = str(tmp_path)
    result = server.query()
    assert result["found"] is False
    assert result["reason"] == "no_snapshot"
    assert "message" in result


def test_query_tool_corrupt_snapshot_returns_clean_error(tmp_path: Path):
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{not valid json", encoding="utf-8")

    server._location = str(tmp_path)
    result = server.query()
    assert result["found"] is False
    assert result["reason"] == "snapshot_unreadable"
    assert "message" in result


@pytest.mark.parametrize("payload", ["5", "null", "3.14"])
def test_query_tool_scalar_json_returns_clean_error(tmp_path: Path, payload: str):
    """Hostile-input checklist: a snapshot file that is valid JSON but a bare
    scalar must return the named error dict, never leak a TypeError through the
    transport (AC-1.4, NFR-3, constitution 'never a raw traceback')."""
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text(payload, encoding="utf-8")

    server._location = str(tmp_path)
    result = server.query()
    assert result["found"] is False
    assert result["reason"] == "snapshot_unreadable"


def test_query_tool_wrong_shape_json_returns_clean_error(tmp_path: Path):
    """F5 precedent: valid JSON that isn't snapshot-shaped must not crash."""
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{}", encoding="utf-8")

    server._location = str(tmp_path)
    result = server.query()
    assert result["found"] is False
    assert result["reason"] == "snapshot_unreadable"
