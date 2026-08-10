"""MetricRegistry — a versioned catalog of pure metric functions.

Registration is explicit (`register()`), not decorator-driven at import time: an
import-time decorator would run as a side effect of merely importing the module,
which conflicts with "no I/O reachable from inside a metric" (AC-5.2) — an
explicit call keeps the derivation path inspectable.

The module-level `registry` ships with **zero** entries. Real metric definitions
(TRC-*, FLW-*, ...) are I2's job, not this feature's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from aspark_insights.model.fact import Fact
from aspark_insights.model.value import MetricValue

if TYPE_CHECKING:
    from aspark_insights.metrics.evidence import EvidenceKind


class MetricFn(Protocol):
    def __call__(self, facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue: ...


class MetricRegistry:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], MetricFn] = {}
        self._evidence_kinds: dict[tuple[str, str], "EvidenceKind | None"] = {}

    def register(
        self, metric_id: str, version: str, fn: MetricFn,
        *, evidence_kind: "EvidenceKind | None" = None,
    ) -> None:
        key = (metric_id, version)
        if key in self._entries:
            raise ValueError(f"metric {metric_id!r} version {version!r} already registered")
        self._entries[key] = fn
        self._evidence_kinds[key] = evidence_kind

    def get(self, metric_id: str, version: str) -> MetricFn:
        return self._entries[(metric_id, version)]

    def evidence_kind(self, metric_id: str, version: str) -> "EvidenceKind | None":
        return self._evidence_kinds.get((metric_id, version))

    def list(self) -> list[dict]:
        """All registered (id, version) pairs, in stable sort order."""
        return [
            {"metric_id": mid, "metric_version": ver}
            for mid, ver in sorted(self._entries.keys())
        ]


registry = MetricRegistry()
