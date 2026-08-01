"""collect_facts: the graph document's one and only walk into trace Facts."""

from __future__ import annotations

from aspark_insights.metrics.collectors import collect_facts
from aspark_insights.model.fact import SubjectKind


def test_empty_document_yields_no_facts():
    assert collect_facts({}) == []
    assert collect_facts({"nodes": [], "edges": []}) == []


def test_story_fact_reflects_incoming_maps_to():
    graph_doc = {
        "nodes": [
            {"id": "story:f:US-1", "type": "Story"},
            {"id": "story:f:US-2", "type": "Story"},  # orphan — no task maps to it
            {"id": "task:f:T1", "type": "Task"},
        ],
        "edges": [
            {"source": "task:f:T1", "target": "story:f:US-1", "type": "maps_to", "confidence": "declared"},
        ],
    }
    facts = {f.subject_id: f for f in collect_facts(graph_doc)}
    assert facts["story:f:US-1"].value == {"mapped": True, "confidence_tier": None}
    assert facts["story:f:US-2"].value == {"mapped": False, "confidence_tier": None}
    assert facts["story:f:US-1"].subject_kind == SubjectKind.CODE_ARTIFACT
    assert facts["story:f:US-1"].predicate == "story"


def test_task_fact_reflects_outgoing_maps_to_and_implements_independently():
    graph_doc = {
        "nodes": [
            {"id": "story:f:US-1", "type": "Story"},
            {"id": "file:f/x.py", "type": "File"},
            {"id": "task:f:T1", "type": "Task"},  # mapped + implements
            {"id": "task:f:T2", "type": "Task"},  # mapped only
            {"id": "task:f:T3", "type": "Task"},  # orphan — neither
        ],
        "edges": [
            {"source": "task:f:T1", "target": "story:f:US-1", "type": "maps_to", "confidence": "declared"},
            {"source": "task:f:T1", "target": "file:f/x.py", "type": "implements", "confidence": "declared"},
            {"source": "task:f:T2", "target": "story:f:US-1", "type": "maps_to", "confidence": "declared"},
        ],
    }
    facts = {f.subject_id: f for f in collect_facts(graph_doc)}
    assert facts["task:f:T1"].value == {"mapped": True, "implements": True}
    assert facts["task:f:T2"].value == {"mapped": True, "implements": False}
    assert facts["task:f:T3"].value == {"mapped": False, "implements": False}


def test_ac_fact_requires_a_passing_qacheck_not_just_any_verifies_edge():
    graph_doc = {
        "nodes": [
            {"id": "ac:f:AC-1.1", "type": "AcceptanceCriterion"},
            {"id": "ac:f:AC-1.2", "type": "AcceptanceCriterion"},
            {"id": "ac:f:AC-1.3", "type": "AcceptanceCriterion"},  # no QACheck at all
            {"id": "qa:f:AC-1.1#0", "type": "QACheck", "result": "pass"},
            {"id": "qa:f:AC-1.2#0", "type": "QACheck", "result": "fail"},
        ],
        "edges": [
            {"source": "qa:f:AC-1.1#0", "target": "ac:f:AC-1.1", "type": "verifies", "confidence": "declared"},
            {"source": "qa:f:AC-1.2#0", "target": "ac:f:AC-1.2", "type": "verifies", "confidence": "declared"},
        ],
    }
    facts = {f.subject_id: f for f in collect_facts(graph_doc)}
    assert facts["ac:f:AC-1.1"].value == {"verified_pass": True}
    assert facts["ac:f:AC-1.2"].value == {"verified_pass": False}
    assert facts["ac:f:AC-1.3"].value == {"verified_pass": False}


def test_facts_are_in_stable_sorted_order():
    graph_doc = {
        "nodes": [
            {"id": "story:f:US-2", "type": "Story"},
            {"id": "story:f:US-1", "type": "Story"},
        ],
        "edges": [],
    }
    facts = collect_facts(graph_doc)
    assert [f.subject_id for f in facts] == ["story:f:US-1", "story:f:US-2"]


def test_story_confidence_tier_is_the_weakest_link_on_its_full_trace():
    graph_doc = {
        "nodes": [
            {"id": "story:f:US-1", "type": "Story"},  # declared task + declared implements
            {"id": "story:f:US-2", "type": "Story"},  # declared task + inferred implements (weaker)
            {"id": "story:f:US-3", "type": "Story"},  # mapped, but its task has no implements at all
            {"id": "file:f/x.py", "type": "File"},
            {"id": "file:f/y.py", "type": "File"},
            {"id": "task:f:T1", "type": "Task"},
            {"id": "task:f:T2", "type": "Task"},
            {"id": "task:f:T3", "type": "Task"},
        ],
        "edges": [
            {"source": "task:f:T1", "target": "story:f:US-1", "type": "maps_to", "confidence": "declared"},
            {"source": "task:f:T1", "target": "file:f/x.py", "type": "implements", "confidence": "declared"},
            {"source": "task:f:T2", "target": "story:f:US-2", "type": "maps_to", "confidence": "declared"},
            {"source": "task:f:T2", "target": "file:f/y.py", "type": "implements", "confidence": "inferred"},
            {"source": "task:f:T3", "target": "story:f:US-3", "type": "maps_to", "confidence": "declared"},
        ],
    }
    facts = {f.subject_id: f for f in collect_facts(graph_doc)}
    assert facts["story:f:US-1"].value["confidence_tier"] == "declared"
    assert facts["story:f:US-2"].value["confidence_tier"] == "inferred"
    assert facts["story:f:US-3"].value["confidence_tier"] is None  # no full trace to code


def test_non_traceability_node_types_are_ignored():
    graph_doc = {
        "nodes": [
            {"id": "file:f/x.py", "type": "File"},
            {"id": "def:f/x.py::foo", "type": "Function"},
            {"id": "feature:f", "type": "Feature"},
        ],
        "edges": [],
    }
    assert collect_facts(graph_doc) == []
