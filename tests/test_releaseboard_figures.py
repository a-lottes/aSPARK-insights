"""RM-T1/T2/T7/T10: per-release stats line (US-1), the global figures band
(US-3/AC-3.1/AC-3.4/AC-3.5), and the per-release US-4 figures header
(AC-4.1/AC-4.2/AC-4.3/AC-4.4)."""

from __future__ import annotations

import re

from aspark_insights.gitboard.releasemap import _build_figures
from aspark_insights.gitboard.releaseboard_report import (
    _STYLE,
    render_release_board_html,
)

_HOSTILE = "<script>alert(1)</script>"


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    r, g, b = linear
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    la, lb = _relative_luminance(hex_a), _relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _artifact_status(status="approved", date="2026-08-01", reason=None) -> dict:
    return {"status": status, "date": date, "reason": reason}


def _delivery(delivering=True, delivered_in=None, reason=None) -> dict:
    return {"delivering": delivering, "delivered_in": delivered_in, "reason": reason}


def _scope(us=1, acs=1, reason=None) -> dict:
    return {"us": us, "acs": acs, "reason": reason}


def _member(name: str, *, delivery=None, scope=None, **status_overrides) -> dict:
    status = {a: _artifact_status() for a in ("spec", "plan", "review", "qa", "release")}
    status.update(status_overrides)
    return {
        "name": name, "status": status,
        "delivery": delivery if delivery is not None else _delivery(),
        "scope": scope if scope is not None else _scope(),
    }


def _delivered_scope(us=1, acs=1, n=1, unreadable=None, reason=None) -> dict:
    return {"us": us, "acs": acs, "n": n, "unreadable": unreadable if unreadable is not None else [], "reason": reason}


def _release(
    tag, previous_tag=None, next_tag=None, members=None, unattributed=None,
    date="2026-08-01", date_reason=None, commit_count=1, delivered_scope=None,
    gap_days=None, gap_days_reason=None, work_types=None,
) -> dict:
    entry = {
        "tag": tag, "previous_tag": previous_tag, "next_tag": next_tag,
        "members": members if members is not None else [_member(f"{tag}-feature")],
        "unattributed": unattributed if unattributed is not None else [],
        "date": date, "date_reason": date_reason, "commit_count": commit_count,
        "delivered_scope": delivered_scope if delivered_scope is not None else _delivered_scope(),
        "gap_days": gap_days, "gap_days_reason": gap_days_reason,
    }
    if work_types is not None:
        entry["work_types"] = work_types
    return entry


def _data(releases=None, reason=None) -> dict:
    releases = releases if releases is not None else []
    return {
        "provenance": {"as_of": "2026-08-24", "insights_version": "0.11.0", "source": "git-interim", "git_available": True},
        "figures": _build_figures(releases) if releases else None,
        "releases": releases,
        "reason": reason,
    }


# --- T1/T2: _real_stats_line -------------------------------------------------


def test_real_release_shows_date_and_commit_count():
    text = render_release_board_html(_data([_release("v1.0.0", date="2026-08-05", commit_count=3)]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "2026-08-05" in detail
    assert "3 commits" in detail


def test_real_release_unreadable_date_shows_reason_not_a_traceback():
    text = render_release_board_html(_data([_release("v1.0.0", date=None, date_reason="tag commit date could not be read")]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "tag commit date could not be read" in detail


def test_real_release_work_types_present_when_set():
    wt = {"value": {"feat": 100}, "reason": None}
    text = render_release_board_html(_data([_release("v1.0.0", work_types=wt)]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "feat 100%" in detail


def test_null_work_types_shows_breakdowns_own_specific_reason_not_a_generic_one():
    """Re-review F15: F8's fix (read `work_types` directly instead of
    string-slicing `_work_types_clause`'s sentence) was unpinned — replacing
    the specific reason with the generic fallback left the whole suite green.
    The `value is None` + specific-`reason` path is exactly what F8 was
    raised about, so it gets its own assertion (NFR-5: a non-empty, specific
    reason, never a generic stand-in when a real one exists)."""
    reason = "2 of 5 commits carry a recognized Conventional Commit type; too few to report a mix"
    wt = {"value": None, "reason": reason}
    text = render_release_board_html(_data([_release("v1.0.0", work_types=wt)]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert reason in detail
    assert "not classifiable for this range" not in detail


def test_absent_work_types_key_still_falls_back_to_the_generic_reason():
    """The other half of F8: a genuinely absent key (zero-commit range) has
    no reason of its own to show, so the generic wording is correct there —
    pinned so the fallback is not deleted along with the generic default."""
    text = render_release_board_html(_data([_release("v1.0.0")]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "not classifiable for this range" in detail


def test_real_release_work_types_absent_key_renders_no_work_types_clause_in_stats_line():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    stats_line = text.split('class="stats-line"')[1].split("</p>")[0]
    assert "Work types" not in stats_line


# --- T7: figures band ---------------------------------------------------------


def test_band_renders_all_ac_3_1_figures():
    releases = [
        _release("v1.0.0", date="2026-07-31", gap_days=None, gap_days_reason="no predecessor release"),
        _release("v1.1.0", date="2026-08-04", gap_days=4),
    ]
    text = render_release_board_html(_data(releases))
    band = text.split('<h2>Overview</h2>')[1].split("<h2>Cadence</h2>")[0]
    assert "Tagged releases" in band and ">2<" in band
    assert "2026-07-31" in band
    assert "2026-08-04" in band
    assert "Median gap" in band
    assert "Features delivered" in band
    assert "Delivered scope" in band
    assert "Commits since last release" in band


def test_zero_tag_repo_band_shows_reason_and_no_figures():
    text = render_release_board_html(_data([], reason="repository has no tags"))
    assert "repository has no tags" in text
    assert '<dl class="figures-band">' not in text


def test_band_never_shows_a_bare_zero_for_unreadable_scope():
    """AC-3.6: a release whose whole delivering set is unreadable must null
    the band total, never fold it in as 0."""
    bad_member = _member("bad", delivery=_delivery(delivering=True), scope=_scope(us=None, acs=None, reason="no US heading found"))
    r = _release(
        "v1.0.0", members=[bad_member],
        delivered_scope=_delivered_scope(us=None, acs=None, n=0, unreadable=["bad"], reason="no delivering member's scope could be read"),
    )
    text = render_release_board_html(_data([r]))
    band = text.split('<h2>Overview</h2>')[1].split("<h2>Cadence</h2>")[0]
    assert "scope unavailable" in band
    assert "Scope unreadable for: bad" in text


def test_band_hostile_tag_and_feature_name_are_inert():
    releases = [_release(_HOSTILE, members=[_member(_HOSTILE)])]
    text = render_release_board_html(_data(releases))
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;" in text


# --- T10: US-4 per-release figures header -------------------------------------


def test_release_figures_header_shows_all_ac_4_1_figures():
    delivering = _member("feature-a", delivery=_delivery(delivering=True), scope=_scope(us=2, acs=6))
    trailing = _member("feature-b", delivery=_delivery(delivering=False, delivered_in="v0.9.0"))
    r = _release(
        "v1.0.0", members=[delivering, trailing], unattributed=[{"hash": "abc1234", "subject": "docs: x"}],
        gap_days=5, delivered_scope=_delivered_scope(us=2, acs=6, n=1),
    )
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "release-figures" in detail
    assert "feature-a" in detail  # delivering
    assert "feature-b" in detail  # trailing
    assert "2 US / 6 ACs" in detail
    assert "5 d" in detail
    assert ">1<" in detail  # unattributed count


def test_earliest_release_gap_shows_null_reason_never_zero():
    r = _release("v0.1.0", gap_days=None, gap_days_reason="no predecessor release")
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "no predecessor release" in detail
    # AC-4.2: never renders a bare `0` standing in for the missing gap
    assert not re.search(r"<dt>Gap to predecessor</dt>\s*<dd>0", detail)


def test_v0_6_0_style_combination_ac_4_3():
    trailing = _member("measurement-honesty", delivery=_delivery(delivering=False, delivered_in="v0.5.0"))
    r = _release(
        "v0.6.0", members=[trailing], gap_days=8,
        unattributed=[{"hash": "26e7f95", "subject": "feat: snapshot-report scorecard redesign"}],
        delivered_scope=_delivered_scope(us=0, acs=0, n=0),
    )
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "<dd>none</dd>" in detail  # 0 delivering features
    assert "measurement-honesty" in detail
    assert "8 d" in detail
    assert "26e7f95" in detail
    assert "feat: snapshot-report scorecard redesign" in detail
    assert "no feature was delivered in this release" in detail


def test_pseudo_release_never_gets_a_release_figures_header():
    """AC-4.4-adjacent: the Should-level header is Must-free — a pseudo
    release (which has no delivery/commit_count/etc. of this shape) is
    never routed through `_render_release_figures`."""
    pseudo = {
        "tag": None, "previous_tag": "v1.0.0", "next_tag": None,
        "members": [], "unattributed": [],
        "commits": {"value": 2, "reason": None}, "branches": [{"name": "main"}],
        "days_since_tag": {"value": 1, "reason": None},
    }
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1].split("</article>")[0]
    assert "release-figures" not in detail


# --- contrast (NFR-4) ---------------------------------------------------------


def _tokens_from_style() -> dict[str, str]:
    return dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{3,6});", _STYLE))


def test_figures_band_text_meets_4_5_to_1_contrast():
    tokens = _tokens_from_style()
    assert _contrast_ratio(tokens["--text-primary"], tokens["--bg-card"]) >= 4.5
    assert _contrast_ratio(tokens["--text-secondary"], tokens["--bg-card"]) >= 4.5


def test_cadence_bar_fill_meets_3_to_1_non_text_contrast():
    tokens = _tokens_from_style()
    assert _contrast_ratio(tokens["--accent-teal"], tokens["--bg-card"]) >= 3.0


# --- review F1: partial-unreadable delivering scope discloses n/unreadable ---


def test_partial_unreadable_delivering_scope_discloses_n_and_names_unreadable():
    """review F1 repro: delivering `alpha` (readable) + `beta` (unreadable)
    must never render as a complete-looking total with no disclosure."""
    alpha = _member("alpha", delivery=_delivery(delivering=True), scope=_scope(us=1, acs=1))
    beta = _member("beta", delivery=_delivery(delivering=True), scope=_scope(us=None, acs=None, reason="no US heading found"))
    r = _release(
        "v1.0.0", members=[alpha, beta],
        delivered_scope=_delivered_scope(us=1, acs=1, n=1, unreadable=["beta"]),
    )
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "1 US / 1 AC" in detail
    assert "n=1 of 2 delivering" in detail
    assert "unreadable: beta" in detail


def test_band_partial_unreadable_scope_shows_n_of_features_delivered():
    alpha_release = _release(
        "v1.0.0", members=[_member("alpha", scope=_scope(us=1, acs=1))],
        delivered_scope=_delivered_scope(us=1, acs=1, n=1),
    )
    beta_release = _release(
        "v2.0.0", members=[_member("beta", scope=_scope(us=None, acs=None, reason="no US heading found"))],
        delivered_scope=_delivered_scope(us=0, acs=0, n=0, unreadable=["beta"]),
    )
    text = render_release_board_html(_data([alpha_release, beta_release]))
    band = text.split('<h2>Overview</h2>')[1].split("<h2>Cadence</h2>")[0]
    assert "n=1 of 2 delivering" in band
    assert "Scope unreadable for: beta" in text


# --- review F11: integral median displays without a trailing .0 --------------


def test_integral_median_displays_without_trailing_decimal():
    releases = [
        _release("v1.0.0", gap_days=None, gap_days_reason="no predecessor release"),
        _release("v1.1.0", gap_days=2),
    ]
    text = render_release_board_html(_data(releases))
    band = text.split('<h2>Overview</h2>')[1].split("<h2>Cadence</h2>")[0]
    assert "2 d" in band
    assert "2.0 d" not in band


def test_fractional_median_still_displays_with_decimal():
    releases = [
        _release("v1.0.0", gap_days=None, gap_days_reason="no predecessor release"),
        _release("v1.1.0", gap_days=1),
        _release("v1.2.0", gap_days=2),
    ]
    text = render_release_board_html(_data(releases))
    band = text.split('<h2>Overview</h2>')[1].split("<h2>Cadence</h2>")[0]
    assert "1.5 d" in band


# --- review F12: AC singularizes, US does not -------------------------------


def test_singular_ac_count_reads_ac_not_acs():
    r = _release("v1.0.0", members=[_member("feature-a", delivery=_delivery(delivering=True), scope=_scope(us=1, acs=1))])
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "1 AC" in detail
    assert "1 ACs" not in detail
