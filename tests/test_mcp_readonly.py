"""T4: the `query` tool never writes and never constructs a GraphPort (AC-1.5, NFR-2).

Complements the structural boundary guard (test_boundary.py) with a
behavioural check: repeated calls against a real built-snapshot fixture leave
`.aspark-insights/` untouched, and instantiating a GraphPort during a call
would raise (proving the read path never reaches it, not just that it
currently doesn't import it).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aspark_insights import server
from aspark_insights.build import build_snapshot
from aspark_insights.store import write_snapshot

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    snapshot = build_snapshot(tmp_path, as_of="2026-07-29")
    write_snapshot(tmp_path, snapshot)
    return tmp_path


def _listing(store_dir: Path) -> set[tuple[str, float]]:
    return {
        (str(p.relative_to(store_dir)), p.stat().st_mtime)
        for p in store_dir.rglob("*")
        if p.is_file()
    }


def test_repeated_query_calls_never_write_to_aspark_insights(built_repo: Path):
    store_dir = built_repo / ".aspark-insights"
    before = _listing(store_dir)

    server._location = str(built_repo)
    for _ in range(3):
        result = server.query()
        assert "found" not in result  # a successful read, not an error dict

    after = _listing(store_dir)
    assert after == before


def test_query_never_constructs_a_graph_port(built_repo: Path, monkeypatch: pytest.MonkeyPatch):
    from aspark_insights.ports import graph as graph_port_module

    def _refuse_construction(self, *args, **kwargs):
        raise AssertionError("query() must never construct a GraphPort")

    monkeypatch.setattr(graph_port_module.LibraryInterimGraphPort, "__init__", _refuse_construction)
    monkeypatch.setattr(graph_port_module.CLIGraphPort, "__init__", _refuse_construction)

    server._location = str(built_repo)
    result = server.query()
    assert "found" not in result
