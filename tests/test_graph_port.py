"""US-2: GraphPort — the only seam to aspark-graph (AC-2.1, AC-2.2, AC-2.3)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aspark_insights.errors import GraphNotBuiltError, GraphUnreadableError, GraphVersionMismatchError
from aspark_insights.ports.graph import CLIGraphPort, LibraryInterimGraphPort

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def test_library_adapter_reads_canonical_nodes_and_edges(built_repo: Path):
    port = LibraryInterimGraphPort()
    result = port.read_graph(built_repo)
    expected = json.loads(FIXTURE_GRAPH.read_text())
    assert result == expected
    assert port.access_mode == "library-interim"


def test_library_adapter_raises_named_error_on_unbuilt_graph(tmp_path: Path):
    port = LibraryInterimGraphPort()
    with pytest.raises(GraphNotBuiltError):
        port.read_graph(tmp_path)


def test_library_adapter_raises_named_error_on_malformed_json(tmp_path: Path):
    """B2: a realistic state (interrupted build, disk full) must not raw-traceback."""
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text("{not valid json!!", encoding="utf-8")

    port = LibraryInterimGraphPort()
    with pytest.raises(GraphUnreadableError):
        port.read_graph(tmp_path)


def test_library_adapter_raises_named_error_on_empty_file(tmp_path: Path):
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text("", encoding="utf-8")

    port = LibraryInterimGraphPort()
    with pytest.raises(GraphUnreadableError):
        port.read_graph(tmp_path)


@pytest.mark.parametrize("content", ["[1, 2, 3]", '"hello"', "null", "42"])
def test_library_adapter_raises_named_error_on_valid_json_non_dict_shapes(tmp_path: Path, content: str):
    """B2 re-test: Graph.load's internal `data.get(...)` raises AttributeError,
    not JSONDecodeError/KeyError/ValueError, on a top-level list/str/null/number."""
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text(content, encoding="utf-8")

    port = LibraryInterimGraphPort()
    with pytest.raises(GraphUnreadableError):
        port.read_graph(tmp_path)


def test_library_adapter_raises_named_error_on_wrong_shape_json(tmp_path: Path):
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text('{"nodes": [{"id": "x"}], "edges": []}', encoding="utf-8")

    port = LibraryInterimGraphPort()
    with pytest.raises(GraphUnreadableError):
        port.read_graph(tmp_path)


def test_library_adapter_refuses_on_version_mismatch(built_repo: Path, monkeypatch):
    port = LibraryInterimGraphPort(pinned_version="0.7.0")
    monkeypatch.setattr(
        "importlib.metadata.version", lambda name: "9.9.9" if name == "aspark-graph" else None
    )
    with pytest.raises(GraphVersionMismatchError):
        port.read_graph(built_repo)


def test_cli_adapter_returns_parsed_json_on_success(monkeypatch):
    port = CLIGraphPort()
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout='{"found": true}\n', stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    result = port.query("staleness", repo_root=".")
    assert result == {"found": True}
    assert port.access_mode == "cli"


def test_cli_adapter_raises_named_error_on_nonzero_exit(monkeypatch):
    port = CLIGraphPort()
    fake = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="graph not built\n")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    with pytest.raises(GraphNotBuiltError):
        port.query("staleness", repo_root=".")
