"""TRC-*/MTA-* — the first real metric definitions, registered on import.

Each function is a pure `(facts, *, as_of) -> MetricValue` (I1's `MetricFn`
Protocol) — no ambient clock, no I/O, no re-derivation of graph structure.
`registry.register(...)` calls execute once, at module import time: an
explicit call you can grep for, not a decorator hiding registration as a
side effect of unrelated imports (per `metrics/registry.py`'s own rationale).
"""

from __future__ import annotations

from aspark_insights.model.fact import Fact
from aspark_insights.model.value import MetricValue
from aspark_insights.metrics.registry import registry


def _trc_001_story_task_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    stories = [f for f in facts if f.predicate == "story"]
    n = len(stories)
    if n == 0:
        return MetricValue(
            metric_id="TRC-001", metric_version="1.0.0", value=None,
            reason="no Story nodes found in graph", n=0,
        )
    mapped = sum(1 for f in stories if f.value.get("mapped"))
    return MetricValue(metric_id="TRC-001", metric_version="1.0.0", value=mapped / n, n=n)


registry.register("TRC-001", "1.0.0", _trc_001_story_task_coverage)


def _trc_002_ac_qa_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    acs = [f for f in facts if f.predicate == "acceptance_criterion"]
    n = len(acs)
    if n == 0:
        return MetricValue(
            metric_id="TRC-002", metric_version="1.0.0", value=None,
            reason="no AcceptanceCriterion nodes found in graph", n=0,
        )
    verified = sum(1 for f in acs if f.value.get("verified_pass"))
    return MetricValue(metric_id="TRC-002", metric_version="1.0.0", value=verified / n, n=n)


registry.register("TRC-002", "1.0.0", _trc_002_ac_qa_coverage)


def _trc_003_task_code_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    tasks = [f for f in facts if f.predicate == "task"]
    n = len(tasks)
    if n == 0:
        return MetricValue(
            metric_id="TRC-003", metric_version="1.0.0", value=None,
            reason="no Task nodes found in graph", n=0,
        )
    implemented = sum(1 for f in tasks if f.value.get("implements"))
    return MetricValue(metric_id="TRC-003", metric_version="1.0.0", value=implemented / n, n=n)


registry.register("TRC-003", "1.0.0", _trc_003_task_code_coverage)


def _trc_004_orphan_tasks(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    """Tasks with no outgoing `maps_to` — never reads `open_findings` (A3: the graph's
    artifact parser only populates Finding nodes for legacy filenames)."""
    tasks = [f for f in facts if f.predicate == "task"]
    n = len(tasks)
    if n == 0:
        return MetricValue(
            metric_id="TRC-004-orphan-tasks", metric_version="1.0.0", value=None,
            reason="no Task nodes found in graph", n=0,
        )
    orphans = sum(1 for f in tasks if not f.value.get("mapped"))
    return MetricValue(metric_id="TRC-004-orphan-tasks", metric_version="1.0.0", value=orphans, n=n)


registry.register("TRC-004-orphan-tasks", "1.0.0", _trc_004_orphan_tasks)


def _trc_004_unverified_acs(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    """AcceptanceCriteria with no incoming `verifies` edge whose QACheck `result` is
    `"pass"`. A distinct denominator from orphan-tasks, so a distinct entry — never
    blended into one ratio that would hide which predicate drove it."""
    acs = [f for f in facts if f.predicate == "acceptance_criterion"]
    n = len(acs)
    if n == 0:
        return MetricValue(
            metric_id="TRC-004-unverified-acs", metric_version="1.0.0", value=None,
            reason="no AcceptanceCriterion nodes found in graph", n=0,
        )
    unverified = sum(1 for f in acs if not f.value.get("verified_pass"))
    return MetricValue(metric_id="TRC-004-unverified-acs", metric_version="1.0.0", value=unverified, n=n)


registry.register("TRC-004-unverified-acs", "1.0.0", _trc_004_unverified_acs)


def _stories_with_a_trace(facts: tuple[Fact, ...]) -> list[Fact]:
    return [
        f for f in facts
        if f.predicate == "story" and f.value.get("confidence_tier") is not None
    ]


def _trc_005_confidence_tier(tier: str):
    """Returns a pure metric function for one confidence tier's share of Stories
    with a full trace to code. Three registry entries, not one dict-valued
    MetricValue — `value` is a scalar (float | int | None) by model design, so a
    3-way breakdown ships as three entries, the same shape TRC-004 already
    established for a distinct-denominator split."""

    def _fn(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
        traced = _stories_with_a_trace(facts)
        n = len(traced)
        metric_id = f"TRC-005-{tier}"
        if n == 0:
            return MetricValue(
                metric_id=metric_id, metric_version="1.0.0", value=None,
                reason="no Story has a full trace to code", n=0,
            )
        share = sum(1 for f in traced if f.value.get("confidence_tier") == tier) / n
        return MetricValue(metric_id=metric_id, metric_version="1.0.0", value=share, n=n)

    return _fn


for _tier in ("declared", "extracted", "inferred"):
    registry.register(f"TRC-005-{_tier}", "1.0.0", _trc_005_confidence_tier(_tier))
