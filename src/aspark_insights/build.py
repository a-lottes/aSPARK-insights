"""build — read the graph, collect Facts, run the registered metrics, seal a snapshot.

`as_of` is a required caller-supplied argument, never read from the wall clock
(ADR-4) — that is what makes the determinism canary meaningful at all. This
feature (I2) turns the graph document into Facts (Collector), scope-filters and
freshness-discloses it, and seals a snapshot with a real, non-empty TRC-*/MTA-*
metrics catalog.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aspark_insights import __version__ as INSIGHTS_VERSION
from aspark_insights.errors import InsightsError, InvalidAsOfError, PolicyUnavailable
from aspark_insights.metrics import traceability  # noqa: F401 - registers TRC-*/MTA-* on import
from aspark_insights.metrics.collectors import collect_facts
from aspark_insights.metrics.registry import registry as METRIC_REGISTRY
from aspark_insights.metrics.scope import apply_scope_filter
from aspark_insights.model.provenance import GraphSource, Provenance
from aspark_insights.model.snapshot import Snapshot
from aspark_insights.ports.graph import CLIGraphPort, GraphPort, LibraryInterimGraphPort
from aspark_insights.ports.policy import NullPolicyPort, PolicyPort

# Versions the registry *mechanism/shape*, not the catalog's contents — bumped
# only when the registry's own contract changes, not when a metric is added.
METRIC_REGISTRY_VERSION = "0.1.0"


def _validate_as_of(as_of: str) -> None:
    """A parse of a caller-supplied string, not a clock read — ADR-4 is untouched.

    Rejects anything that isn't a real calendar date in YYYY-MM-DD form, which
    also closes the path-traversal hole a raw `as_of` (e.g. `"../../etc/evil"`)
    would otherwise open once it's used to build a snapshot's filename.
    """
    try:
        datetime.strptime(as_of, "%Y-%m-%d")
    except ValueError as exc:
        raise InvalidAsOfError(
            f"--as-of must be an ISO-8601 date (YYYY-MM-DD), got {as_of!r}"
        ) from exc


def _collect_staleness(staleness_port: GraphPort, repo_root: str | Path) -> dict:
    """Best-effort: a failed staleness query never blocks a build (AC-6.2).

    Mirrors MetricValue's own honesty pattern — `available: False` plus a
    `reason` is the "null with cause" shape for a provenance field that can't
    itself use MetricValue's null-needs-a-reason invariant.
    """
    try:
        result = staleness_port.query("staleness", repo_root=str(repo_root))
        return {"available": True, **result}
    except (InsightsError, OSError, ValueError) as exc:
        # OSError (e.g. the CLI binary present but not executable) and ValueError
        # (json.JSONDecodeError on a returncode-0-but-non-JSON stdout) must also
        # degrade to null+reason, never escape as a raw traceback that breaks a
        # build — AC-6.2 ("build never refuses") and the "never a raw traceback"
        # non-negotiable both apply here, not just to named InsightsError.
        return {"available": False, "reason": str(exc)}


def build_snapshot(
    repo_root: str | Path,
    as_of: str,
    graph_port: GraphPort | None = None,
    policy_port: PolicyPort | None = None,
    staleness_port: GraphPort | None = None,
) -> Snapshot:
    _validate_as_of(as_of)
    port = graph_port or LibraryInterimGraphPort()
    graph_doc = port.read_graph(repo_root)
    graph_doc, scope_result = apply_scope_filter(graph_doc)

    graph_staleness = _collect_staleness(staleness_port or CLIGraphPort(), repo_root)

    facts = tuple(collect_facts(graph_doc))
    metrics = [
        METRIC_REGISTRY.get(entry["metric_id"], entry["metric_version"])(facts, as_of=as_of)
        for entry in METRIC_REGISTRY.list()
    ]

    policy_result = (policy_port or NullPolicyPort()).resolve(str(repo_root))
    policy_versions = None if isinstance(policy_result, PolicyUnavailable) else policy_result

    provenance = Provenance(
        as_of=as_of,
        insights_version=INSIGHTS_VERSION,
        metric_registry_version=METRIC_REGISTRY_VERSION,
        graph_source=GraphSource(access=port.access_mode, sealed=True),
        policy_versions=policy_versions,
        scope_filter=scope_result,
        graph_staleness=graph_staleness,
    )
    return Snapshot.seal(facts=facts, metrics=metrics, provenance=provenance)
