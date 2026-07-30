"""US-2: integration test against a real, pinned aspark-graph install (AC-2.1, AC-2.2, C4).

Mocking only would defer validation of the riskiest coupling — the interim library
adapter's direct import of aspark_graph internals — to I2. This test runs against
the actual sibling repo (a uv path dependency, checked out alongside this one),
not a fixture, so that coupling is proven now.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aspark_insights.errors import GraphNotBuiltError
from aspark_insights.ports.graph import CLIGraphPort, LibraryInterimGraphPort

REPO_ROOT = Path(__file__).resolve().parent.parent
SIBLING_GRAPH_REPO = REPO_ROOT.parent / "aSPARK-graph"
SIBLING_GRAPH_JSON = SIBLING_GRAPH_REPO / ".aspark-graph" / "graph.json"

pytestmark = pytest.mark.skipif(
    not SIBLING_GRAPH_JSON.exists(),
    reason=(
        f"no built graph at {SIBLING_GRAPH_JSON} — run `aspark-graph build .` in "
        "the sibling repo first (CI does this explicitly; see .github/workflows/ci.yml)"
    ),
)


def test_library_adapter_matches_the_graphs_own_canonical_document():
    port = LibraryInterimGraphPort()
    result = port.read_graph(SIBLING_GRAPH_REPO)

    expected = json.loads(SIBLING_GRAPH_JSON.read_text(encoding="utf-8"))
    assert result == expected
    assert result["nodes"], "expected at least one real node from the family's own graph"


def test_cli_adapter_returns_the_graphs_contract_json():
    port = CLIGraphPort()
    result = port.query("staleness", repo_root=str(SIBLING_GRAPH_REPO))
    assert "files_checked" in result
    assert "stale" in result


def test_library_adapter_raises_named_error_against_a_truly_unbuilt_graph(tmp_path: Path):
    port = LibraryInterimGraphPort()
    with pytest.raises(GraphNotBuiltError):
        port.read_graph(tmp_path)
