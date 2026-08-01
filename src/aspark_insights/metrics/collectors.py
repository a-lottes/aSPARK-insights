"""Collector — the graph document's one and only walk into trace Facts.

Reads the plain `{"nodes": [...], "edges": [...]}` dict GraphPort already
returned (the sibling graph library's own internals stay confined to
`ports/graph.py`, AC-2.4/NFR-4). Every TRC-*/MTA-* metric filters these Facts
by predicate and counts; none re-derives graph structure itself (I1's
`MetricFn(facts, *, as_of)` Protocol only ever sees Facts, never the raw
document).

A `verifies` edge itself carries no `result` — that lives on the source
`QACheck` node (the graph's own artifact parser only stamps `result` on the
node, not the edge) — so "passing" is resolved by looking up the edge's
source node, not the edge's own attributes.
"""

from __future__ import annotations

from aspark_insights.model.fact import Fact, SubjectKind

# Mirrors the graph library's own Confidence.rank() as plain strings —
# duplicated, not imported, since only ports/graph.py may import the sibling's
# internals (AC-2.4).
_CONFIDENCE_RANK = {"inferred": 0, "extracted": 1, "declared": 2}


def collect_facts(graph_doc: dict) -> list[Fact]:
    nodes = {n["id"]: n for n in graph_doc.get("nodes", [])}
    edges = graph_doc.get("edges", [])

    story_mapped: set[str] = set()
    task_mapped: set[str] = set()
    task_implements: set[str] = set()
    ac_verified_pass: set[str] = set()

    # TRC-005: per Task, the confidence of its maps_to edge (to a Story) and
    # of each of its implements edges (to a File) — used below to find each
    # Story's weakest confidence tier across its full trace to code.
    task_maps_to_story: dict[str, tuple[str, str]] = {}  # task_id -> (story_id, confidence)
    task_implements_confidences: dict[str, list[str]] = {}  # task_id -> [confidence, ...]

    for edge in edges:
        etype = edge.get("type")
        source = edge.get("source")
        target = edge.get("target")
        confidence = edge.get("confidence")
        if etype == "maps_to":  # Task -> Story
            task_mapped.add(source)
            story_mapped.add(target)
            task_maps_to_story[source] = (target, confidence)
        elif etype == "implements":  # Task -> File
            task_implements.add(source)
            task_implements_confidences.setdefault(source, []).append(confidence)
        elif etype == "verifies":  # QACheck -> AcceptanceCriterion
            if nodes.get(source, {}).get("result") == "pass":
                ac_verified_pass.add(target)

    story_weakest_tier = _weakest_confidence_per_story(task_maps_to_story, task_implements_confidences)

    facts: list[Fact] = []
    for node_id in sorted(nodes):
        node = nodes[node_id]
        node_type = node.get("type")
        if node_type == "Story":
            facts.append(
                Fact(
                    SubjectKind.CODE_ARTIFACT,
                    node_id,
                    "story",
                    {
                        "mapped": node_id in story_mapped,
                        "confidence_tier": story_weakest_tier.get(node_id),
                    },
                )
            )
        elif node_type == "AcceptanceCriterion":
            facts.append(
                Fact(
                    SubjectKind.CODE_ARTIFACT,
                    node_id,
                    "acceptance_criterion",
                    {"verified_pass": node_id in ac_verified_pass},
                )
            )
        elif node_type == "Task":
            facts.append(
                Fact(
                    SubjectKind.CODE_ARTIFACT,
                    node_id,
                    "task",
                    {"mapped": node_id in task_mapped, "implements": node_id in task_implements},
                )
            )

    return facts


def _weakest_confidence_per_story(
    task_maps_to_story: dict[str, tuple[str, str]],
    task_implements_confidences: dict[str, list[str]],
) -> dict[str, str]:
    """Story -> weakest confidence tier across every (maps_to, implements) pair
    on a full trace to a File. A Story with no mapped task that also implements
    code has no entry — it has no trace to rate, not a `declared`-tier one."""
    weakest: dict[str, str] = {}
    for task_id, (story_id, maps_confidence) in task_maps_to_story.items():
        for impl_confidence in task_implements_confidences.get(task_id, []):
            pair_tier = min(maps_confidence, impl_confidence, key=_CONFIDENCE_RANK.__getitem__)
            current = weakest.get(story_id)
            if current is None or _CONFIDENCE_RANK[pair_tier] < _CONFIDENCE_RANK[current]:
                weakest[story_id] = pair_tier
    return weakest
