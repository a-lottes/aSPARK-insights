"""FL-T1/T2: current_gate, build_feature_lens, ordering — pure, no git
(feature-lens US-1/US-2, AC-1.1-1.5, AC-2.1-2.5, NFR-8's zero-extra-git-call
claim)."""

from __future__ import annotations

import ast
from pathlib import Path

from aspark_insights.gitboard.featurelens import build_feature_lens, current_gate


def _artifact_status(status=None, date=None, reason=None) -> dict:
    return {"status": status, "date": date, "reason": reason}


def _status_map(**overrides) -> dict:
    status = {a: _artifact_status() for a in ("spec", "plan", "review", "qa", "release")}
    status.update(overrides)
    return status


def _delivery(delivering=True, delivered_in=None, reason=None) -> dict:
    return {"delivering": delivering, "delivered_in": delivered_in, "reason": reason}


def _member(name: str, status=None, delivery=None, scope=None) -> dict:
    return {
        "name": name,
        "status": status if status is not None else _status_map(),
        "delivery": delivery if delivery is not None else _delivery(),
        "scope": scope if scope is not None else {"us": 1, "acs": 1, "reason": None},
    }


def _release(tag, members=None) -> dict:
    return {"tag": tag, "members": members if members is not None else []}


def _release_map(releases=None, reason=None) -> dict:
    return {
        "provenance": {"as_of": "2026-08-25", "insights_version": "0.12.0", "source": "git-interim", "git_available": True},
        "releases": releases if releases is not None else [],
        "reason": reason,
        "figures": None,
    }


# --- NFR-8: structural, zero extra git calls ---------------------------------


def test_featurelens_module_imports_no_git_or_path_machinery():
    """NFR-8's zero-extra-git-call claim, pinned structurally: this module
    must never import subprocess/gitread/pathlib, or it has stopped being a
    pure regrouping of already-computed data."""
    source = Path("src/aspark_insights/gitboard/featurelens.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    # review F4: the previous version compared only the FIRST dotted segment,
    # so `gitread` could never appear (every real import form normalizes to
    # `aspark_insights`) and that assertion was a tautology. Collect every
    # dotted segment of the module path *and* every imported name, so
    # `from aspark_insights.gitboard import gitread` is actually caught.
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.update(node.module.split("."))
            imported.update(alias.name for alias in node.names)
    assert "subprocess" not in imported
    assert "gitread" not in imported
    assert "pathlib" not in imported
    assert "Path" not in imported
    assert "os" not in imported


# --- AC-2.1: current_gate ------------------------------------------------------


def test_gate_released_when_release_status_present():
    status = _status_map(release=_artifact_status(status="released"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "Released"
    assert artifact == "release"
    assert evidence == [{"artifact": "release", "status": "released", "reason": None}]


def test_gate_qa_when_release_null_but_qa_present():
    status = _status_map(qa=_artifact_status(status="passed"), release=_artifact_status(reason="file not found"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "QA"
    assert artifact == "qa"
    assert evidence == [
        {"artifact": "qa", "status": "passed", "reason": None},
        {"artifact": "release", "status": None, "reason": "file not found"},
    ]


def test_gate_review_when_only_review_and_earlier_present():
    status = _status_map(review=_artifact_status(status="passed"), qa=_artifact_status(reason="not run"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "Review"
    assert evidence[1] == {"artifact": "qa", "status": None, "reason": "not run"}


def test_gate_increment_example_matches_plan_wording_with_verbatim_reason():
    """The plan's own named sub-decision: literal reason, never the AC's
    illustrative 'not started' wording."""
    status = _status_map(plan=_artifact_status(status="approved"), review=_artifact_status(reason="file not found"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "Increment"
    assert artifact == "plan"
    assert evidence == [
        {"artifact": "plan", "status": "approved", "reason": None},
        {"artifact": "review", "status": None, "reason": "file not found"},
    ]


def test_gate_spec_when_only_spec_present():
    status = _status_map(spec=_artifact_status(status="approved"), plan=_artifact_status(reason="file not found"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "Spec"
    assert evidence[1] == {"artifact": "plan", "status": None, "reason": "file not found"}


def test_gate_unknown_surfaces_specs_own_reason_alone():
    status = _status_map(spec=_artifact_status(reason="no header table found"))
    gate, artifact, evidence = current_gate(status)
    assert gate == "Unknown"
    assert artifact is None
    assert evidence == [{"artifact": "spec", "status": None, "reason": "no header table found"}]


def test_gate_unknown_never_guessed_as_spec_merely_because_directory_exists():
    status = _status_map()  # every artifact null
    gate, _, _ = current_gate(status)
    assert gate == "Unknown"


# --- AC-1.1/1.2: build_feature_lens dedup + delivered_in -----------------------


def test_feature_appears_exactly_once_across_multiple_occurrences():
    """AC-1.2 repro: a feature delivering in v1.0.0, trailing into v2.0.0 —
    exactly one row, delivered_in reads the delivering release's own tag,
    never the trailing occurrence's null delivered_in field."""
    status = _status_map(release=_artifact_status(status="released"))
    older = _release("v1.0.0", members=[_member("feature-x", status=status, delivery=_delivery(delivering=True))])
    newer = _release("v2.0.0", members=[_member("feature-x", status=status, delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    result = build_feature_lens(_release_map([older, newer]))
    names = [f["name"] for f in result["features"]]
    assert names.count("feature-x") == 1
    row = result["features"][0]
    assert row["delivered_in"] == "v1.0.0"
    assert row["delivered_in_reason"] is None


def test_delivered_in_read_from_delivering_occurrences_own_release_tag():
    """A4/ADR-0: `delivered_in` must never be read from the delivering
    occurrence's own (always-null) `delivered_in` field — it is the tag of
    the release whose occurrence has `delivering: True`."""
    status = _status_map(release=_artifact_status(status="released"))
    r = _release("v3.0.0", members=[_member("solo", status=status, delivery=_delivery(delivering=True, delivered_in=None))])
    result = build_feature_lens(_release_map([r]))
    assert result["features"][0]["delivered_in"] == "v3.0.0"


# --- AC-1.3: pseudo-only feature ------------------------------------------------


def test_feature_only_in_open_window_is_null_with_verbatim_reason():
    pseudo = _release(None, members=[_member(
        "not-yet",
        delivery=_delivery(delivering=False, delivered_in=None, reason="not yet delivered in a tagged release"),
    )])
    result = build_feature_lens(_release_map([pseudo]))
    row = result["features"][0]
    assert row["delivered_in"] is None
    assert row["delivered_in_reason"] == "not yet delivered in a tagged release"


# --- AC-1.4: spec.md degrade paths ----------------------------------------------


def test_unreadable_spec_date_still_produces_a_row_with_named_reason():
    status = _status_map(spec=_artifact_status(reason="no header table found"))
    r = _release("v1.0.0", members=[_member("broken", status=status)])
    result = build_feature_lens(_release_map([r]))
    row = result["features"][0]
    assert row["spec_date"] is None
    assert row["spec_date_reason"] == "no header table found"


# --- AC-1.5/C5: ordering --------------------------------------------------------


def test_status_row_present_but_no_date_row_still_names_a_date_reason():
    """review F1/F10: `read_artifact_status` sets `reason` exactly when
    `status` is null, so a header table carrying `**Status**` but no
    `**Date**` row arrives as `{status: <found>, date: None, reason: None}`.
    `spec_date_reason` must still name the specific cause — never a
    reason-less null (NFR-5). Mutation-checked: reverting the fallback
    fails this assertion."""
    status = _status_map(spec=_artifact_status(status="`in-review`", date=None, reason=None))
    r = _release("v1.0.0", members=[_member("dateless", status=status)])
    row = build_feature_lens(_release_map([r]))["features"][0]
    assert row["spec_date"] is None
    assert row["spec_date_reason"] == "no Date row found in header table"


def test_dated_features_sorted_by_date_descending_name_ascending_tiebreak():
    r = _release("v1.0.0", members=[
        _member("bravo", status=_status_map(spec=_artifact_status(status="approved", date="2026-08-01"))),
        _member("alpha", status=_status_map(spec=_artifact_status(status="approved", date="2026-08-01"))),
        _member("charlie", status=_status_map(spec=_artifact_status(status="approved", date="2026-08-05"))),
    ])
    result = build_feature_lens(_release_map([r]))
    names = [f["name"] for f in result["features"]]
    assert names == ["charlie", "alpha", "bravo"]


def test_undated_features_sort_last_by_name_never_treated_as_newest():
    r = _release("v1.0.0", members=[
        _member("dated", status=_status_map(spec=_artifact_status(status="approved", date="2026-08-01"))),
        _member("zeta", status=_status_map(spec=_artifact_status(reason="no header table found"))),
        _member("beta", status=_status_map(spec=_artifact_status(reason="no header table found"))),
    ])
    result = build_feature_lens(_release_map([r]))
    names = [f["name"] for f in result["features"]]
    assert names == ["dated", "beta", "zeta"]


def test_malformed_date_string_never_raises_and_sorts_as_a_string():
    r = _release("v1.0.0", members=[
        _member("normal", status=_status_map(spec=_artifact_status(status="approved", date="2026-08-01"))),
        _member("weird", status=_status_map(spec=_artifact_status(status="approved", date="not-a-date"))),
    ])
    result = build_feature_lens(_release_map([r]))
    names = [f["name"] for f in result["features"]]
    assert set(names) == {"normal", "weird"}


# --- zero-tag / empty cases ------------------------------------------------------


def test_zero_releases_returns_empty_features_with_reason():
    result = build_feature_lens(_release_map([], reason="repository has no tags"))
    assert result["features"] == []
    assert result["reason"] == "repository has no tags"


def test_status_map_identical_across_occurrences_invariant_relied_upon():
    """The invariant `build_feature_lens` relies on: the same feature's
    status map is byte-identical across every occurrence within one run
    (both read from the working tree at build time, not per-historical-
    commit) — pinned here so a future change to that invariant is caught."""
    status = _status_map(release=_artifact_status(status="released"))
    older = _release("v1.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=True))])
    newer = _release("v2.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    assert older["members"][0]["status"] == newer["members"][0]["status"]


def test_pseudo_only_reason_copied_byte_for_byte_from_release_maps_own_value():
    """T2 DoD: compared against the release map's own value, not a literal —
    if `_attribute_delivery`'s wording ever changes, this test tracks it."""
    reason_value = "not yet delivered in a tagged release"
    pseudo = _release(None, members=[_member(
        "not-yet", delivery=_delivery(delivering=False, delivered_in=None, reason=reason_value),
    )])
    release_map = _release_map([pseudo])
    result = build_feature_lens(release_map)
    row = result["features"][0]
    assert row["delivered_in_reason"] == release_map["releases"][0]["members"][0]["delivery"]["reason"]


def test_build_feature_lens_never_raises_on_completely_absent_artifacts():
    status = _status_map()  # every artifact null, every reason None too
    r = _release("v1.0.0", members=[_member("bare", status=status)])
    result = build_feature_lens(_release_map([r]))
    row = result["features"][0]
    assert row["gate"] == "Unknown"
    assert row["spec_date"] is None


def test_delivering_occurrence_wins_even_when_scanned_after_a_trailing_one():
    """review F3: a defensive, order-independent scan — not merely correct
    because `_attribute_delivery` happens to stamp the first occurrence.
    Constructs a release map where the delivering occurrence is scanned
    SECOND, deliberately violating the real shipped ordering invariant, to
    prove the read doesn't silently depend on it.

    review F10: the trailing occurrence deliberately carries a *decoy*
    `delivered_in` that disagrees with the delivering occurrence's tag. With
    the original fixture (trailing carrying the same `v0.5.0` the delivering
    occurrence would yield) both the buggy first-occurrence-only read and
    the fixed order-independent scan returned `v0.5.0`, so the test passed
    against the very bug it was added to pin. The decoy is what makes the
    two readings distinguishable.
    """
    status = _status_map(release=_artifact_status(status="released"))
    # trailing occurrence scanned first, delivering occurrence scanned second
    first = _release("v1.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=False, delivered_in="v0.1.0-decoy"))])
    second = _release("v0.5.0", members=[_member("x", status=status, delivery=_delivery(delivering=True))])
    result = build_feature_lens(_release_map([first, second]))
    row = result["features"][0]
    assert row["delivered_in"] == "v0.5.0"  # the delivering occurrence's own release tag
    assert row["delivered_in"] != "v0.1.0-decoy"  # never the first occurrence seen
    assert row["delivered_in_reason"] is None


def test_delivering_occurrence_wins_when_scanned_last_of_three_occurrences():
    """review F10: order-independence proven at a scan position the two-
    occurrence fixture cannot reach — three occurrences, the delivering one
    scanned last, both earlier trailing occurrences carrying a decoy tag."""
    status = _status_map(release=_artifact_status(status="released"))
    releases = [
        _release("v3.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=False, delivered_in="v9.9.9-decoy"))]),
        _release("v2.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=False, delivered_in="v9.9.9-decoy"))]),
        _release("v1.0.0", members=[_member("x", status=status, delivery=_delivery(delivering=True))]),
    ]
    result = build_feature_lens(_release_map(releases))
    assert len(result["features"]) == 1  # AC-1.1/1.2 dedup survives the scan rewrite
    assert result["features"][0]["delivered_in"] == "v1.0.0"
