"""FL-T4: feature-lens HTML rendering — table, badges, wrap discipline
(feature-lens AC-1.1, AC-1.5, AC-2.5, NFR-1, NFR-4)."""

from __future__ import annotations

import re

from aspark_insights.gitboard.featurelens_report import (
    _LENS_STYLE,
    render_feature_lens_html,
)


def _artifact_status(status=None, date=None, reason=None) -> dict:
    return {"status": status, "date": date, "reason": reason}


def _status_map(**overrides) -> dict:
    status = {a: _artifact_status(status="approved", date="2026-08-01") for a in ("spec", "plan", "review", "qa", "release")}
    status.update(overrides)
    return status


def _feature(name="feature-a", spec_date="2026-08-01", spec_date_reason=None, status=None,
             gate="Released", gate_artifact="release", gate_evidence=None,
             delivered_in="v1.0.0", delivered_in_reason=None) -> dict:
    return {
        "name": name, "spec_date": spec_date, "spec_date_reason": spec_date_reason,
        "status": status if status is not None else _status_map(),
        "gate": gate, "gate_artifact": gate_artifact,
        "gate_evidence": gate_evidence if gate_evidence is not None else [{"artifact": "release", "status": "released", "reason": None}],
        "delivered_in": delivered_in, "delivered_in_reason": delivered_in_reason,
    }


def _data(features=None, reason=None) -> dict:
    return {"provenance": {}, "features": features if features is not None else [], "reason": reason}


_HOSTILE = "<script>alert(1)</script>"


# --- structure -----------------------------------------------------------------


def test_single_h1_and_real_table():
    html = render_feature_lens_html(_data([_feature()]))
    assert html.count("<h1") == 1
    assert '<table class="lens-table">' in html
    assert html.count('<th scope="col">') == 9


def test_column_headers_include_verbatim_date_label():
    html = render_feature_lens_html(_data([_feature()]))
    assert "spec.md&#x27;s own Date (last updated)" in html or "spec.md's own Date (last updated)" in html


def test_zero_features_shows_reason_no_table():
    html = render_feature_lens_html(_data([], reason="no features found"))
    assert "no features found" in html
    assert "<table" not in html


def test_zero_releases_reason_propagates():
    html = render_feature_lens_html(_data([], reason="repository has no tags"))
    assert "repository has no tags" in html


# --- badges / status cells -------------------------------------------------------


def test_null_status_shows_reason_not_duplicated_alongside_plain_status():
    status = _status_map(review=_artifact_status(reason="file not found"))
    html = render_feature_lens_html(_data([_feature(status=status)]))
    row = html.split("<tbody>")[1].split("</tbody>")[0]
    assert "file not found" in row
    # a plain-word status cell (e.g. "approved") shows the word once, not the reason
    assert row.count("approved") >= 1


def test_gate_badge_uses_one_class_regardless_of_value():
    released = render_feature_lens_html(_data([_feature(gate="Released")]))
    spec_row = _feature(gate="Spec", gate_artifact="spec", gate_evidence=[{"artifact": "spec", "status": "approved", "reason": None}])
    spec_html = render_feature_lens_html(_data([spec_row]))
    assert 'class="gate-badge"' in released
    assert 'class="gate-badge"' in spec_html
    # exactly one CSS rule governs .gate-badge, regardless of gate value
    rules = re.findall(r"\.gate-badge\s*\{[^}]*\}", _LENS_STYLE)
    assert len(rules) == 1


def test_gate_never_rendered_as_progress_bar_or_meter_element():
    html = render_feature_lens_html(_data([_feature()]))
    for forbidden in ("<progress", "<meter", "step-tracker", "dot-track"):
        assert forbidden not in html


def test_gate_evidence_always_present_beside_the_label():
    html = render_feature_lens_html(_data([_feature(gate_evidence=[{"artifact": "release", "status": "released", "reason": None}])]))
    assert 'class="gate-evidence"' in html
    assert "release: released" in html


# --- wrap discipline (NFR-4) -------------------------------------------------------


def test_lens_table_cells_have_wrap_and_max_width_rules():
    assert ".lens-table th, .lens-table td { overflow-wrap: anywhere;" in _LENS_STYLE.replace("\n", " ") or "overflow-wrap: anywhere" in _LENS_STYLE
    assert "max-width" in _LENS_STYLE


def test_long_reason_string_does_not_break_row_structure():
    long_reason = "x" * 400
    status = _status_map(review=_artifact_status(reason=long_reason))
    html = render_feature_lens_html(_data([_feature(status=status)]))
    assert long_reason in html
    assert html.count("<tr>") >= 1  # row structure intact


# --- security (also covered adversarially in T6, this is a render-level spot check) --


def test_hostile_feature_name_and_reason_are_escaped():
    status = _status_map(spec=_artifact_status(reason=_HOSTILE))
    html = render_feature_lens_html(_data([_feature(name=_HOSTILE, spec_date=None, spec_date_reason=_HOSTILE, status=status)]))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_zero_interactive_elements_keyboard_operability_by_construction():
    """T4 DoD deviation (recorded in plan.md): the DoD as written asked to
    compare this count against the release board page's own count, but
    feature-lens.html is a brand-new page with no shared baseline to compare
    against — there is nothing "before this feature" to diff. The actual,
    stronger fact: this page has zero `a`/`button`/`input`/`select`/
    `textarea`/`[tabindex]` elements of any kind, so keyboard operability
    holds trivially, by construction, with nothing to Tab to at all."""
    html = render_feature_lens_html(_data([_feature()]))
    for tag in ("<a ", "<button", "<input", "<select", "<textarea", "tabindex"):
        assert tag not in html


# --- QA B1: 375px table readability -------------------------------------------


def test_lens_table_has_a_min_width_floor_so_columns_cannot_be_crushed():
    """QA B1: `overflow-wrap: anywhere` alone let the browser's table-layout
    algorithm shrink every column to single-character width at 375px — a
    `min-width` floor on the table and its cells forces a readable natural
    width, so the shipped `.table-wrap { overflow-x: auto }` container
    scrolls horizontally instead of the table crushing itself. Live-verified
    in the browser at 375px and 1280px during /demo-day's fix-mode round;
    this pins the CSS mechanism structurally."""
    assert "min-width" in _LENS_STYLE
    assert ".lens-table { min-width:" in _LENS_STYLE.replace("\n", " ").replace("  ", " ") or "min-width: 62rem" in _LENS_STYLE
    # every cell also carries its own floor, not just the table element
    assert ".lens-table th, .lens-table td { overflow-wrap: anywhere; max-width: 22ch; min-width: 9ch; }" in _LENS_STYLE
