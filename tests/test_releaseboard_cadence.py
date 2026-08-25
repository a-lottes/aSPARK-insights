"""RM-T8: the cadence strip (US-3/AC-3.2, AC-3.3, AC-3.7, NFR-5) — exactly
two states, one uniform hue regardless of value, the longest gap marked by
rank/text only, never a value-dependent color."""

from __future__ import annotations

import re

from aspark_insights.gitboard.releasemap import _build_figures
from aspark_insights.gitboard.releaseboard_report import (
    _STYLE,
    render_release_board_html,
)


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
    gap_days=None, gap_days_reason=None,
) -> dict:
    return {
        "tag": tag, "previous_tag": previous_tag, "next_tag": next_tag,
        "members": members if members is not None else [_member(f"{tag}-feature")],
        "unattributed": unattributed if unattributed is not None else [],
        "date": date, "date_reason": date_reason, "commit_count": commit_count,
        "delivered_scope": delivered_scope if delivered_scope is not None else _delivered_scope(),
        "gap_days": gap_days, "gap_days_reason": gap_days_reason,
    }


def _data(releases=None, reason=None) -> dict:
    releases = releases if releases is not None else []
    return {
        "provenance": {"as_of": "2026-08-24", "insights_version": "0.11.0", "source": "git-interim", "git_available": True},
        "figures": _build_figures(releases) if releases else None,
        "releases": releases,
        "reason": reason,
    }


def _tagged_chain(gaps: list[int]) -> list[dict]:
    """N+1 tags whose successive gap_days are exactly `gaps`."""
    releases = [_release("v1.0.0", gap_days=None, gap_days_reason="no predecessor release")]
    for i, g in enumerate(gaps, start=2):
        releases.append(_release(f"v{i}.0.0", previous_tag=releases[-1]["tag"], gap_days=g))
    return releases


def _cadence_section(text: str) -> str:
    return text.split("<h2>Cadence</h2>")[1].split('<ul class="index-list"')[0]


# --- AC-3.7: exactly two states -----------------------------------------------


def test_one_tag_refuses_itself_with_reason_naming_n():
    text = render_release_board_html(_data(_tagged_chain([])))
    cadence = _cadence_section(text)
    assert "<table" not in cadence
    assert "n=0" in cadence


def test_two_tags_one_gap_refuses_itself_with_reason_naming_n():
    text = render_release_board_html(_data(_tagged_chain([3])))
    cadence = _cadence_section(text)
    assert "<table" not in cadence
    assert "n=1" in cadence


def test_nine_gaps_renders_the_present_state_fully():
    text = render_release_board_html(_data(_tagged_chain([2, 2, 1, 6, 8, 1, 0, 2, 2])))
    cadence = _cadence_section(text)
    assert "<table" in cadence
    assert cadence.count("<tbody>") == 1
    assert cadence.split("<tbody>")[1].count("<tr>") == 9
    assert "not enough" not in cadence.lower()


def test_no_third_partial_state_at_the_boundary():
    """AC-3.7: no averaged/summarized value ever stands in for a raw gap,
    at either boundary (just below and just at the refusal threshold)."""
    below = _cadence_section(render_release_board_html(_data(_tagged_chain([3]))))
    at = _cadence_section(render_release_board_html(_data(_tagged_chain([3, 5]))))
    assert "<table" not in below
    assert "<table" in at
    assert "average" not in at.lower() and "avg" not in at.lower()


# --- AC-3.2: every gap a number in text, longest identifiable -----------------


def test_every_gap_shown_as_a_plain_number():
    text = render_release_board_html(_data(_tagged_chain([2, 2, 1, 6, 8, 1, 0, 2, 2])))
    cadence = _cadence_section(text)
    for g in (2, 1, 6, 8, 0):
        assert f"{g} d" in cadence


def test_longest_gap_marked_by_rank_and_word_never_only_by_bar():
    text = render_release_board_html(_data(_tagged_chain([2, 2, 1, 6, 8, 1, 0, 2, 2])))
    cadence = _cadence_section(text)
    assert "<strong>8 d (longest)</strong>" in cadence


# --- NFR-5: one uniform hue, no value-dependent color --------------------------


def test_exactly_one_css_class_and_hue_serves_every_bar():
    text = render_release_board_html(_data(_tagged_chain([2, 2, 1, 6, 8, 1, 0, 2, 2])))
    cadence = _cadence_section(text)
    bar_classes = set(re.findall(r'class="([^"]*cadence-bar[^"]*)"', cadence))
    assert bar_classes == {"cadence-bar"}
    # exactly one rule in the stylesheet defines this class's color/background
    bar_style_rules = re.findall(r"\.cadence-bar\s*\{[^}]*\}", _STYLE)
    assert len(bar_style_rules) == 1


def test_no_bar_style_attribute_varies_by_anything_other_than_width():
    text = render_release_board_html(_data(_tagged_chain([2, 2, 1, 6, 8, 1, 0, 2, 2])))
    cadence = _cadence_section(text)
    style_attrs = re.findall(r'<span class="cadence-bar" style="([^"]*)"', cadence)
    assert len(style_attrs) == 9
    for style in style_attrs:
        assert re.fullmatch(r"width:\d{1,3}%", style)


def test_gap_readable_as_number_even_at_zero_width_bar():
    """A `0`-day gap still shows its number in text, not just an empty bar."""
    text = render_release_board_html(_data(_tagged_chain([0, 2, 3, 1, 5, 2, 4, 1, 3])))
    cadence = _cadence_section(text)
    assert re.search(r"<td>0 d</td>", cadence)


# --- review F2: unreadable gap shows null+reason as a row, never dropped -----


def test_unreadable_gap_renders_as_a_row_with_reason_not_silently_dropped():
    """review F2 repro: 5 tags, one gap unreadable -> the strip used to
    silently drop that row and could mislabel the wrong gap 'longest'."""
    releases = [_release("v1.0.0", gap_days=None, gap_days_reason="no predecessor release")]
    for i, (g, reason) in enumerate([(2, None), (None, "a needed release date could not be read"), (5, None), (3, None)], start=2):
        releases.append(_release(f"v{i}.0.0", previous_tag=releases[-1]["tag"], gap_days=g, gap_days_reason=reason))
    text = render_release_board_html(_data(releases))
    cadence = _cadence_section(text)
    assert "<table" in cadence
    assert cadence.split("<tbody>")[1].count("<tr>") == 4  # every gap slot, not just the measured ones
    assert "a needed release date could not be read" in cadence
    # true longest is unknown (one gap unmeasured) -> no row is marked "longest"
    assert "longest" not in cadence.lower()
    assert "5 d" in cadence  # the measured gaps still show as plain numbers
    assert "measured" in cadence  # caption discloses the partial n


def test_unreadable_gap_row_has_no_bar():
    releases = [
        _release("v1.0.0", gap_days=None, gap_days_reason="no predecessor release"),
        _release("v2.0.0", previous_tag="v1.0.0", gap_days=None, gap_days_reason="a needed release date could not be read"),
        _release("v3.0.0", previous_tag="v2.0.0", gap_days=4),
    ]
    text = render_release_board_html(_data(releases))
    cadence = _cadence_section(text)
    assert 'class="cadence-bar"' not in cadence.split("<tbody>")[1].split("</tr>")[0]


# --- review F7: no "longest" mark on a tie or an all-zero set ----------------


def test_tied_maximum_gaps_are_not_both_marked_longest():
    text = render_release_board_html(_data(_tagged_chain([5, 5, 2])))
    cadence = _cadence_section(text)
    assert "longest" not in cadence.lower()


def test_all_zero_gaps_are_not_marked_longest():
    text = render_release_board_html(_data(_tagged_chain([0, 0, 0])))
    cadence = _cadence_section(text)
    assert "longest" not in cadence.lower()


def test_single_unambiguous_maximum_still_gets_marked():
    text = render_release_board_html(_data(_tagged_chain([2, 8, 3])))
    cadence = _cadence_section(text)
    assert "<strong>8 d (longest)</strong>" in cadence
