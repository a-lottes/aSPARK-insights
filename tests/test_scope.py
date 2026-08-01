"""ScopeFilter: excludes noise nodes and discloses what was dropped (MTA-003, NFR-3)."""

from __future__ import annotations

from aspark_insights.metrics.scope import apply_scope_filter
from aspark_insights.model.provenance import ScopeFilterResult


def test_excludes_worktree_duplicate_file_and_its_edges():
    graph_doc = {
        "nodes": [
            {"id": "file:src/foo.py", "type": "File"},
            {"id": "file:.claude/worktrees/wt1/src/foo.py", "type": "File"},
            {"id": "def:.claude/worktrees/wt1/src/foo.py::bar", "type": "Function"},
        ],
        "edges": [
            {
                "source": "file:.claude/worktrees/wt1/src/foo.py",
                "target": "def:.claude/worktrees/wt1/src/foo.py::bar",
                "type": "contains",
                "confidence": "extracted",
            },
        ],
    }
    filtered, result = apply_scope_filter(graph_doc)
    kept_ids = {n["id"] for n in filtered["nodes"]}
    assert kept_ids == {"file:src/foo.py"}
    assert filtered["edges"] == []
    assert result.excluded_count == 2
    assert result.patterns == (".claude/worktrees/**",)


def test_result_is_disclosed_even_when_nothing_is_excluded():
    graph_doc = {"nodes": [{"id": "file:src/foo.py", "type": "File"}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert filtered["nodes"] == graph_doc["nodes"]
    assert result.excluded_count == 0
    assert isinstance(result, ScopeFilterResult)


def test_non_path_nodes_are_never_excluded():
    graph_doc = {
        "nodes": [
            {"id": "story:f:US-1", "type": "Story"},
            {"id": "ac:f:AC-1.1", "type": "AcceptanceCriterion"},
        ],
        "edges": [],
    }
    filtered, result = apply_scope_filter(graph_doc)
    assert len(filtered["nodes"]) == 2
    assert result.excluded_count == 0


# --- hostile-input checklist (NFR-3): never a raw traceback ------------------


def test_empty_string_node_id_does_not_crash():
    graph_doc = {"nodes": [{"id": ""}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert result.excluded_count == 0
    assert filtered["nodes"] == [{"id": ""}]


def test_path_traversal_in_node_id_does_not_crash_or_falsely_match():
    graph_doc = {"nodes": [{"id": "file:../../etc/passwd"}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert result.excluded_count == 0  # doesn't match .claude/worktrees/**
    assert filtered["nodes"] == graph_doc["nodes"]


def test_absolute_path_node_id_does_not_crash():
    graph_doc = {"nodes": [{"id": "file:/etc/passwd"}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert result.excluded_count == 0
    assert filtered["nodes"] == graph_doc["nodes"]


def test_non_string_node_id_does_not_crash():
    graph_doc = {"nodes": [{"id": 12345}, {"id": None}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert result.excluded_count == 0
    assert len(filtered["nodes"]) == 2


def test_missing_id_key_does_not_crash():
    graph_doc = {"nodes": [{"type": "File"}], "edges": []}
    filtered, result = apply_scope_filter(graph_doc)
    assert result.excluded_count == 0
    assert filtered["nodes"] == graph_doc["nodes"]


def test_empty_document_does_not_crash():
    filtered, result = apply_scope_filter({})
    assert filtered == {"nodes": [], "edges": []}
    assert result.excluded_count == 0
