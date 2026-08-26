"""featurelens — a feature-centric regrouping of `build_release_map()`'s
already-assembled per-member data (feature-lens US-1/US-2/US-3).

Pure `dict -> dict`/`dict -> tuple` transforms only: no `subprocess`,
`gitread` or `pathlib` import, and no `.spark/`/git read of its own — every
field this module needs (a feature's `status`, `delivery`, `scope`) already
exists on each release's `members[]` entries (ADR-0). This module never
re-derives membership, commit ranges, or the delivery/document anchor rules
the release board already ships; it only collapses N occurrences of one
feature into a single row and labels its current gate.
"""

from __future__ import annotations

from aspark_insights.errors import ReleaseMapUnreadableError

_GATE_SEQUENCE = ("release", "qa", "review", "plan", "spec")
_GATE_NAMES = {
    "release": "Released",
    "qa": "QA",
    "review": "Review",
    "plan": "Increment",
    "spec": "Spec",
}


def current_gate(status: dict) -> tuple[str, str | None, list[dict]]:
    """AC-2.1: checks `release` -> `qa` -> `review` -> `plan` -> `spec`, in
    that order, and stops at the first non-null `status`. Returns
    `(gate, gate_artifact, gate_evidence)` — `gate_evidence` always carries
    the deciding artifact's own literal status, plus (when the decider is
    not `release`) the *next-checked-before-it* artifact's own verbatim
    null reason, e.g. `[{"artifact": "plan", "status": "approved", "reason":
    None}, {"artifact": "review", "status": None, "reason": "file not
    found"}]` — never the AC's own illustrative "not started" wording,
    which would assert more than the data knows (NFR-5). `Unknown` (every
    artifact null) surfaces `spec`'s own reason verbatim, alone (AC-2.4)."""
    for i, artifact in enumerate(_GATE_SEQUENCE):
        entry = status[artifact]
        if entry["status"] is not None:
            evidence = [{"artifact": artifact, "status": entry["status"], "reason": None}]
            if i > 0:
                prev_artifact = _GATE_SEQUENCE[i - 1]
                prev_entry = status[prev_artifact]
                evidence.append(
                    {"artifact": prev_artifact, "status": prev_entry["status"], "reason": prev_entry["reason"]}
                )
            return _GATE_NAMES[artifact], artifact, evidence
    spec_entry = status["spec"]
    return "Unknown", None, [{"artifact": "spec", "status": None, "reason": spec_entry["reason"]}]


def _sort_features(features: list[dict]) -> list[dict]:
    """AC-1.5/C5: dated features by `spec_date` string descending (never
    parsed — a malformed date must not raise), name ascending as the stable
    tie-break; undated features follow, name ascending. Undated is never
    treated as newest and never dropped."""
    dated = sorted((f for f in features if f["spec_date"] is not None), key=lambda f: f["name"])
    dated.sort(key=lambda f: f["spec_date"], reverse=True)
    undated = sorted((f for f in features if f["spec_date"] is None), key=lambda f: f["name"])
    return dated + undated


def build_feature_lens(release_map: dict) -> dict:
    """One row per feature, read (never re-derived) from `release_map`'s own
    `releases[]`/`members[]`. `_member_entries` reads every occurrence's
    `status` from the working tree at build time, so all occurrences of one
    feature carry a byte-identical status map within one run.

    `delivered_in` is read as *the tag of the release whose occurrence has
    `delivery["delivering"] is True`* — review F3: scanned across **every**
    occurrence, not assumed to be the first one seen. By `_attribute_delivery`'s
    own construction the delivering occurrence is always a feature's first
    (oldest), which would make a first-occurrence-only read appear correct on
    any real release map — but it is correct only because of that ordering
    coincidence, not by the code's own guarantee, and a delivering occurrence
    found later in the scan must still win over an earlier trailing one's
    already-correct `delivered_in` value. A trailing occurrence's own
    `delivered_in` field (stamped by `_attribute_delivery`) is read as a
    fallback, never re-derived; the delivering occurrence's own `delivered_in`
    field is `None` by design and is never read (A4/ADR-0)."""
    try:
        releases = release_map.get("releases")
        if not releases:
            return {
                "provenance": release_map["provenance"],
                "features": [],
                "reason": release_map.get("reason") or "no releases found",
            }

        order: list[str] = []
        statuses: dict[str, dict] = {}
        delivered_in_by_name: dict[str, str] = {}
        reason_by_name: dict[str, str] = {}
        for release in releases:
            for member in release["members"]:
                name = member["name"]
                if name not in statuses:
                    order.append(name)
                    statuses[name] = member["status"]
                delivery = member["delivery"]
                if delivery["delivering"]:
                    delivered_in_by_name[name] = release["tag"]
                    reason_by_name.pop(name, None)
                elif name not in delivered_in_by_name:
                    if delivery["delivered_in"] is not None:
                        delivered_in_by_name[name] = delivery["delivered_in"]
                    elif name not in reason_by_name:
                        reason_by_name[name] = delivery["reason"]

        features = []
        for name in order:
            status = statuses[name]
            spec_entry = status["spec"]
            if spec_entry["date"] is None:
                spec_date_reason = spec_entry["reason"] or "no Date row found in header table"
            else:
                spec_date_reason = None
            gate, gate_artifact, gate_evidence = current_gate(status)
            if name in delivered_in_by_name:
                delivered_in, delivered_in_reason = delivered_in_by_name[name], None
            else:
                delivered_in = None
                delivered_in_reason = reason_by_name.get(name) or "delivery status could not be determined"
            features.append({
                "name": name,
                "spec_date": spec_entry["date"],
                "spec_date_reason": spec_date_reason,
                "status": status,
                "gate": gate,
                "gate_artifact": gate_artifact,
                "gate_evidence": gate_evidence,
                "delivered_in": delivered_in,
                "delivered_in_reason": delivered_in_reason,
            })

        return {
            "provenance": release_map["provenance"],
            "features": _sort_features(features),
            "reason": None,
        }
    except (KeyError, TypeError, AttributeError) as exc:
        raise ReleaseMapUnreadableError(
            f"release map data has an unexpected shape: {exc}"
        ) from exc


_PIPELINE_ORDER = ("Spec", "Increment", "Review", "QA", "Released", "Unknown")


def group_by_gate(features: list[dict]) -> list[tuple[str, list[dict]]]:
    """AC-3.1: every feature in exactly one of `Spec`/`Increment`/`Review`/
    `QA`/`Released`, plus `Unknown` only if it actually occurs — a feature
    directory with no readable `spec.md` is a real, if rare, shape (AC-2.4),
    not a defect to hide by always showing the bucket."""
    buckets: dict[str, list[dict]] = {g: [] for g in _PIPELINE_ORDER}
    for f in features:
        buckets[f["gate"]].append(f)
    return [(g, buckets[g]) for g in _PIPELINE_ORDER if g != "Unknown" or buckets["Unknown"]]
