"""Walking skeleton: build_snapshot computes TRC-001 end to end (AC-1.1, AC-1.5, NFR-1)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aspark_graph.graph import Graph
from aspark_graph.model import Confidence, EdgeType, NodeType

from aspark_insights.build import build_snapshot
from aspark_insights.serialization import canonical_json
from aspark_insights.store import snapshot_path


@pytest.fixture
def trace_repo(tmp_path: Path) -> Path:
    """A real, aspark_graph-built graph with one mapped Story and one orphan Story."""
    g = Graph()
    g.add_node("story:f:US-1", NodeType.STORY, story="US-1", title="Mapped", feature="f")
    g.add_node("story:f:US-2", NodeType.STORY, story="US-2", title="Orphan", feature="f")
    g.add_node("task:f:T1", NodeType.TASK, task="T1", feature="f")
    g.add_edge("task:f:T1", "story:f:US-1", EdgeType.MAPS_TO, Confidence.DECLARED)
    g.save(tmp_path / ".aspark-graph" / "graph.json")
    return tmp_path


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_build_snapshot_computes_trc_001_from_a_real_graph(trace_repo: Path):
    snap = build_snapshot(trace_repo, as_of="2026-07-29")
    trc_001 = next(m for m in snap.metrics if m.metric_id == "TRC-001")
    assert trc_001.value == 0.5  # 1 of 2 stories mapped
    assert trc_001.n == 2
    assert len(snap.facts) == 3  # 2 stories + 1 task


def test_build_twice_with_real_metrics_is_byte_identical(trace_repo: Path):
    snap_1 = build_snapshot(trace_repo, as_of="2026-07-29")
    snap_2 = build_snapshot(trace_repo, as_of="2026-07-29")
    assert canonical_json(snap_1.to_dict()) == canonical_json(snap_2.to_dict())


def test_cli_query_prints_metrics_alongside_facts_and_provenance(trace_repo: Path):
    build = _run_cli(trace_repo, "build", "--as-of", "2026-07-29")
    assert build.returncode == 0, build.stderr

    import json

    query = _run_cli(trace_repo, "query")
    assert query.returncode == 0, query.stderr
    data = json.loads(query.stdout)
    assert set(data.keys()) == {"facts", "metrics", "provenance"}
    trc_001 = next(m for m in data["metrics"] if m["metric_id"] == "TRC-001")
    assert trc_001["value"] == 0.5
    assert trc_001["n"] == 2


def test_cli_build_output_matches_stored_snapshot(trace_repo: Path):
    result = _run_cli(trace_repo, "build", "--as-of", "2026-07-29")
    assert result.returncode == 0, result.stderr
    stored = snapshot_path(trace_repo, "2026-07-29").read_text(encoding="utf-8")
    assert stored == result.stdout
