"""US-3 (Should): PolicyPort — null adapter for now (AC-3.1, AC-3.2)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import PolicyUnavailable
from aspark_insights.ports.policy import NullPolicyPort

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


def test_null_adapter_returns_unavailable_never_raises():
    port = NullPolicyPort()
    result = port.resolve(".")
    assert isinstance(result, PolicyUnavailable)
    d = result.to_dict()
    assert d["error"] == "policy_unavailable"
    assert "resolver" in d["message"] or "P1" in d["message"]


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def test_snapshot_built_through_null_adapter_has_explicit_null_policy_versions(built_repo: Path):
    snap = build_snapshot(built_repo, as_of="2026-07-29", policy_port=NullPolicyPort())
    assert snap.provenance.policy_versions is None
    assert "policy_versions" in snap.provenance.to_dict()
