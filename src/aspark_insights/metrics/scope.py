"""ScopeFilter — excludes noise nodes (e.g. worktree duplicates) before any
TRC-* metric sees them, and discloses exactly what was dropped (MTA-003).

Applied once, before the Collector, so every metric inherits the same scoped
view and the exclusion result is recorded once rather than recomputed per
metric. Pure string matching (`fnmatch`) — never touches the filesystem, so a
hostile path (`../..`, an absolute path, a non-string id) is just a string
that fails to match, never a crash.
"""

from __future__ import annotations

import fnmatch

from aspark_insights.model.provenance import ScopeFilterResult

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (".claude/worktrees/**",)


def _node_path(node_id: object) -> str | None:
    """The filesystem path a `file:`/`def:` node id encodes, or None for node
    kinds that carry no path (Story/AcceptanceCriterion/Task/...)."""
    if not isinstance(node_id, str):
        return None
    if node_id.startswith("file:"):
        return node_id[len("file:"):]
    if node_id.startswith("def:"):
        return node_id[len("def:"):].split("::", 1)[0]
    return None


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    # fnmatchcase, not fnmatch: fnmatch case-normalizes via os.path.normcase,
    # which is case-insensitive on macOS/Windows and case-sensitive on Linux —
    # the same graph filtered on two platforms could then drop different nodes,
    # breaking byte-identical reproducibility (NFR-1). Node ids are exact-case,
    # so a case-sensitive match is both correct and platform-stable.
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def apply_scope_filter(
    graph_doc: dict,
    patterns: tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS,
) -> tuple[dict, ScopeFilterResult]:
    """Drops nodes whose path matches `patterns`, plus every edge touching one."""
    nodes = graph_doc.get("nodes", [])
    edges = graph_doc.get("edges", [])

    excluded_ids: set[str] = set()
    kept_nodes = []
    for node in nodes:
        path = _node_path(node.get("id"))
        if path is not None and _matches_any(path, patterns):
            excluded_ids.add(node["id"])
        else:
            kept_nodes.append(node)

    kept_edges = [
        edge
        for edge in edges
        if edge.get("source") not in excluded_ids and edge.get("target") not in excluded_ids
    ]

    filtered_doc = {"nodes": kept_nodes, "edges": kept_edges}
    result = ScopeFilterResult(patterns=tuple(patterns), excluded_count=len(excluded_ids))
    return filtered_doc, result
