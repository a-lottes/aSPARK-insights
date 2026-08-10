"""Provenance — every field an input, none read from an ambient clock (ADR-4).

`as_of` is supplied by the caller of `insights build`, never `datetime.now()`.
Building with the same inputs (including the same `as_of`) must always produce
the same Provenance, which is what makes the determinism canary meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphSource:
    access: str  # "library-interim" | "cli" — surfaces the interim coupling's sunset (G6)
    sealed: bool

    def to_dict(self) -> dict:
        return {"access": self.access, "sealed": self.sealed}


@dataclass(frozen=True, slots=True)
class ScopeFilterResult:
    """Which exclusion patterns applied and how many nodes they dropped (MTA-003).

    Always present in provenance, even when nothing was excluded — an absent
    field would be indistinguishable from "filtering was never considered".
    """

    patterns: tuple[str, ...]
    excluded_count: int

    def to_dict(self) -> dict:
        return {"patterns": list(self.patterns), "excluded_count": self.excluded_count}


@dataclass(frozen=True, slots=True)
class Provenance:
    as_of: str
    insights_version: str
    metric_registry_version: str
    graph_source: GraphSource
    policy_versions: dict | None
    scope_filter: ScopeFilterResult
    graph_staleness: dict | None  # MTA-002: the graph's own `staleness` result at build time
    artifact_probe: dict  # AC-2.5: the .spark/ presence-probe outcome, sealed on every build

    def to_dict(self) -> dict:
        return {
            "as_of": self.as_of,
            "insights_version": self.insights_version,
            "metric_registry_version": self.metric_registry_version,
            "graph_source": self.graph_source.to_dict(),
            "policy_versions": self.policy_versions,
            "scope_filter": self.scope_filter.to_dict(),
            "graph_staleness": self.graph_staleness,
            "artifact_probe": self.artifact_probe,
        }
