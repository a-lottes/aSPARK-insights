"""build — the walking skeleton: read the graph, seal an empty-metrics snapshot.

`as_of` is a required caller-supplied argument, never read from the wall clock
(ADR-4) — that is what makes the determinism canary (T12) meaningful at all.
Facts and real metric values are I2's job (Collectors, registry entries); this
feature proves the seam works and seals a snapshot with an empty catalog.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aspark_insights import __version__ as INSIGHTS_VERSION
from aspark_insights.errors import InvalidAsOfError, PolicyUnavailable
from aspark_insights.model.provenance import GraphSource, Provenance
from aspark_insights.model.snapshot import Snapshot
from aspark_insights.ports.graph import GraphPort, LibraryInterimGraphPort
from aspark_insights.ports.policy import NullPolicyPort, PolicyPort

# Versions the *mechanism*, not a catalog — the shipped registry has zero entries.
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


def build_snapshot(
    repo_root: str | Path,
    as_of: str,
    graph_port: GraphPort | None = None,
    policy_port: PolicyPort | None = None,
) -> Snapshot:
    _validate_as_of(as_of)
    port = graph_port or LibraryInterimGraphPort()
    port.read_graph(repo_root)  # proves the seam; raises a named error if unbuilt/mismatched

    policy_result = (policy_port or NullPolicyPort()).resolve(str(repo_root))
    policy_versions = None if isinstance(policy_result, PolicyUnavailable) else policy_result

    provenance = Provenance(
        as_of=as_of,
        insights_version=INSIGHTS_VERSION,
        metric_registry_version=METRIC_REGISTRY_VERSION,
        graph_source=GraphSource(access=port.access_mode, sealed=True),
        policy_versions=policy_versions,
    )
    return Snapshot.seal(facts=[], metrics=[], provenance=provenance)
