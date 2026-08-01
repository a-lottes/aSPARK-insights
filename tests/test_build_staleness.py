"""MTA-002: graph staleness disclosure via a second GraphPort (AC-6.1, AC-6.2)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import GraphNotBuiltError

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


class _StubStalenessPort:
    access_mode = "cli"

    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self._result = result
        self._error = error

    def read_graph(self, repo_root):
        raise NotImplementedError

    def query(self, name, *args, repo_root="."):
        if self._error is not None:
            raise self._error
        return self._result


def test_fresh_staleness_is_recorded(built_repo: Path):
    stub = _StubStalenessPort({"stale": False, "files_checked": 3, "changed": [], "missing": []})
    snap = build_snapshot(built_repo, as_of="2026-07-29", staleness_port=stub)
    assert snap.provenance.graph_staleness == {
        "available": True, "stale": False, "files_checked": 3, "changed": [], "missing": [],
    }


def test_stale_result_still_lets_metrics_compute(built_repo: Path):
    stub = _StubStalenessPort({"stale": True, "files_checked": 3, "changed": ["a.py"], "missing": []})
    snap = build_snapshot(built_repo, as_of="2026-07-29", staleness_port=stub)
    assert snap.provenance.graph_staleness["available"] is True
    assert snap.provenance.graph_staleness["stale"] is True
    assert len(snap.metrics) >= 1  # build never refuses on a stale graph


def test_unavailable_staleness_is_null_with_reason_and_build_still_succeeds(built_repo: Path):
    stub = _StubStalenessPort(error=GraphNotBuiltError("aspark-graph CLI not found on PATH"))
    snap = build_snapshot(built_repo, as_of="2026-07-29", staleness_port=stub)
    assert snap.provenance.graph_staleness["available"] is False
    assert "not found" in snap.provenance.graph_staleness["reason"]
    assert len(snap.metrics) >= 1  # build never refuses when staleness is unavailable
