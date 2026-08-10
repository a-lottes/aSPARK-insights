"""TRC-*/MTA-* — the first real metric definitions, registered on import.

Each function is a pure `(facts, *, as_of) -> MetricValue` (I1's `MetricFn`
Protocol) — no ambient clock, no I/O, no re-derivation of graph structure.
`registry.register(...)` calls execute once, at module import time: an
explicit call you can grep for, not a decorator hiding registration as a
side effect of unrelated imports (per `metrics/registry.py`'s own rationale).
"""

from __future__ import annotations

from aspark_insights.metrics.evidence import IMPLEMENTS_EVIDENCE, MAPS_TO_EVIDENCE, QA_EVIDENCE
from aspark_insights.model.fact import Fact
from aspark_insights.model.value import MetricValue
from aspark_insights.metrics.registry import registry


def _trc_001_story_task_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    stories = [f for f in facts if f.predicate == "story"]
    n = len(stories)
    if n == 0:
        return MetricValue(
            metric_id="TRC-001", metric_version="2.0.0", value=None,
            reason="no Story nodes found in graph", n=0,
        )
    mapped = sum(1 for f in stories if f.value.get("mapped"))
    return MetricValue(metric_id="TRC-001", metric_version="2.0.0", value=mapped / n, n=n)


# v2.0.0 (measurement-honesty): a repo-wide absence of maps_to evidence now
# nulls this metric instead of reporting a fabricated 0%/100% (US-1/US-5) —
# never merely a version-string change; the value contract itself changed.
registry.register("TRC-001", "2.0.0", _trc_001_story_task_coverage, evidence_kind=MAPS_TO_EVIDENCE)


def _trc_002_ac_qa_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    acs = [f for f in facts if f.predicate == "acceptance_criterion"]
    n = len(acs)
    if n == 0:
        return MetricValue(
            metric_id="TRC-002", metric_version="2.0.0", value=None,
            reason="no AcceptanceCriterion nodes found in graph", n=0,
        )
    verified = sum(1 for f in acs if f.value.get("verified_pass"))
    return MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=verified / n, n=n)


# v2.0.0: this is the metric measurement-honesty exists for — A3's fabricated
# 0.0/n=41 on this repo's own graph now nulls with a reason instead (US-1).
registry.register("TRC-002", "2.0.0", _trc_002_ac_qa_coverage, evidence_kind=QA_EVIDENCE)


def _trc_003_task_code_coverage(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    tasks = [f for f in facts if f.predicate == "task"]
    n = len(tasks)
    if n == 0:
        return MetricValue(
            metric_id="TRC-003", metric_version="2.0.0", value=None,
            reason="no Task nodes found in graph", n=0,
        )
    implemented = sum(1 for f in tasks if f.value.get("implements"))
    return MetricValue(metric_id="TRC-003", metric_version="2.0.0", value=implemented / n, n=n)


# v2.0.0: same fabricated-zero risk as TRC-002, structurally — a repo-wide
# absence of `implements` evidence now nulls rather than reporting 0% (US-1).
registry.register("TRC-003", "2.0.0", _trc_003_task_code_coverage, evidence_kind=IMPLEMENTS_EVIDENCE)


def _trc_004_orphan_tasks(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    """Tasks with no outgoing `maps_to` — never reads `open_findings` (A3: the graph's
    artifact parser only populates Finding nodes for legacy filenames)."""
    tasks = [f for f in facts if f.predicate == "task"]
    n = len(tasks)
    if n == 0:
        return MetricValue(
            metric_id="TRC-004-orphan-tasks", metric_version="2.0.0", value=None,
            reason="no Task nodes found in graph", n=0,
        )
    orphans = sum(1 for f in tasks if not f.value.get("mapped"))
    return MetricValue(metric_id="TRC-004-orphan-tasks", metric_version="2.0.0", value=orphans, n=n)


# v2.0.0: this metric's own numerator (orphans) is the *inverse* of
# MAPS_TO_EVIDENCE's count — gating on the same evidence kind as TRC-001 is
# still correct, since a repo-wide zero of *any* maps_to edge means "100%
# orphan" would be an extraction-failure artifact, not a real finding (US-1).
registry.register(
    "TRC-004-orphan-tasks", "2.0.0", _trc_004_orphan_tasks, evidence_kind=MAPS_TO_EVIDENCE,
)


def _trc_004_unverified_acs(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    """AcceptanceCriteria with no incoming `verifies` edge whose QACheck `result` is
    `"pass"`. A distinct denominator from orphan-tasks, so a distinct entry — never
    blended into one ratio that would hide which predicate drove it."""
    acs = [f for f in facts if f.predicate == "acceptance_criterion"]
    n = len(acs)
    if n == 0:
        return MetricValue(
            metric_id="TRC-004-unverified-acs", metric_version="2.0.0", value=None,
            reason="no AcceptanceCriterion nodes found in graph", n=0,
        )
    unverified = sum(1 for f in acs if not f.value.get("verified_pass"))
    return MetricValue(metric_id="TRC-004-unverified-acs", metric_version="2.0.0", value=unverified, n=n)


# v2.0.0: same QA_EVIDENCE kind as TRC-002 (its own numerator, "unverified",
# is QA_EVIDENCE's inverse — gating on presence, not absence, is correct) —
# this is the second metric A3's fabricated-zero risk actually hits (US-1).
registry.register(
    "TRC-004-unverified-acs", "2.0.0", _trc_004_unverified_acs, evidence_kind=QA_EVIDENCE,
)


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
