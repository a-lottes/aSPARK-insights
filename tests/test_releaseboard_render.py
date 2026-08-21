"""RBH-T1..T8: release-board.html rendering — index ordering, pseudo-release
discrimination, drill-down detail, badge hue/contrast, honest degenerate
states (release-board-html spec AC-1.x/2.x/3.x, plan.md T1-T8)."""

from __future__ import annotations

import re

import pytest

from aspark_insights.errors import ReleaseMapUnreadableError, ReportUnwritableError
from aspark_insights.gitboard.releaseboard_logo import LOGO_PNG_BASE64
from aspark_insights.gitboard.releaseboard_report import (
    _ARTIFACT_HUES,
    _STYLE,
    render_release_board_html,
    run_release_board_report,
)

_EXTERNAL_REF_PATTERN = re.compile(r'(https?://|<link\b|<script\b)', re.IGNORECASE)
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


def _member(name: str, **status_overrides) -> dict:
    status = {a: _artifact_status() for a in ("spec", "plan", "review", "qa", "release")}
    status.update(status_overrides)
    return {"name": name, "status": status}


def _release(tag: str, previous_tag=None, next_tag=None, members=None, unattributed=None) -> dict:
    return {
        "tag": tag,
        "previous_tag": previous_tag,
        "next_tag": next_tag,
        "members": members if members is not None else [_member(f"{tag}-feature")],
        "unattributed": unattributed if unattributed is not None else [],
    }


def _pseudo(previous_tag="v1.0.0", commits_value=2, days=1, branches=None, members=None, unattributed=None) -> dict:
    return {
        "tag": None,
        "previous_tag": previous_tag,
        "next_tag": None,
        "members": members if members is not None else [],
        "unattributed": unattributed if unattributed is not None else [],
        "commits": {"value": commits_value, "reason": None},
        "branches": branches if branches is not None else [{"name": "main"}],
        "days_since_tag": {"value": days, "reason": None},
    }


def _data(releases=None, reason=None) -> dict:
    return {
        "provenance": {
            "as_of": "2026-08-20", "insights_version": "0.9.0", "source": "git-interim",
            "git_available": True,
        },
        "releases": releases if releases is not None else [],
        "reason": reason,
    }


# --- T2: doc scaffolding, offline, no JS -------------------------------------


def test_html_has_no_javascript_no_external_refs():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    assert "<script>" not in text
    assert not _EXTERNAL_REF_PATTERN.search(text)


def test_html_has_doctype_lang_viewport_title_single_h1():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    assert text.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in text
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in text
    assert "<title>" in text
    assert text.count("<h1") == 1


def test_style_block_defines_root_tokens():
    for token in ("--bg-primary", "--bg-card", "--text-primary", "--text-secondary"):
        assert token in _STYLE


# --- T1: index ordering and counts (AC-1.1/1.2) ------------------------------


def test_index_lists_one_row_per_entry_in_given_order():
    releases = [_release("v0.1.0"), _release("v0.2.0"), _pseudo(previous_tag="v0.2.0")]
    text = render_release_board_html(_data(releases))
    idx_v01 = text.index(">v0.1.0<")
    idx_v02 = text.index(">v0.2.0<")
    idx_pseudo = text.index("Since v0.2.0")
    assert idx_v01 < idx_v02 < idx_pseudo


def test_index_row_counts_read_from_list_lengths_not_recomputed():
    release = _release(
        "v0.3.0",
        members=[_member("a"), _member("b"), _member("c")],
        unattributed=[{"hash": "abc1234", "subject": "x"}],
    )
    text = render_release_board_html(_data([release]))
    row = text.split('href="#rel-0"')[1].split("</a>")[0]
    assert "3 members" in row
    assert "1 unattributed" in row


# --- T3: pseudo-release discrimination + true-zero (AC-1.3/AC-3.2) ----------


def test_pseudo_release_distinguished_by_tag_null_not_row_position():
    releases = [_release("v1.0.0"), _pseudo(previous_tag="v1.0.0")]
    text = render_release_board_html(_data(releases))
    assert "open window" in text
    assert "Since v1.0.0" in text


def test_pseudo_release_figures_shown_verbatim():
    pseudo = _pseudo(previous_tag="v1.0.0", commits_value=5, days=3, branches=[{"name": "a"}, {"name": "b"}])
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1]
    assert "5 commits since v1.0.0, 3 days ago" in detail
    assert "2 local branches" in detail


def test_pseudo_release_zero_commits_is_a_true_zero_sentence():
    pseudo = _pseudo(previous_tag="v1.0.0", commits_value=0)
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1]
    assert "Nothing has landed since v1.0.0." in detail


# --- T4: drill-down detail, real table, backtick strip, back-link -----------


def test_index_row_links_to_same_document_anchor():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    assert 'href="#rel-0"' in text
    assert 'id="rel-0"' in text


def test_three_members_all_render_no_truncation():
    release = _release("v0.3.0", members=[_member("traceability-metrics"), _member("public-repo-polish"), _member("mcp-server")])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    for name in ("traceability-metrics", "public-repo-polish", "mcp-server"):
        assert name in detail


def test_single_member_exactly_one_member_block():
    release = _release("v0.5.0", members=[_member("measurement-honesty")])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert detail.count('<div class="member-block">') == 1


def test_artifact_matrix_is_a_real_table_with_scope_and_caption():
    release = _release("v1.0.0", members=[_member("feature-x")])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    assert "<table>" in detail
    assert '<th scope="col">Artifact</th>' in detail
    assert "<caption>" in detail


def test_backtick_status_is_stripped_for_display():
    release = _release("v1.0.0", members=[_member("feature-x", spec=_artifact_status(status="`approved`"))])
    text = render_release_board_html(_data([release]))
    assert ">approved<" in text
    assert "`approved`" not in text


def test_non_backtick_status_passes_through_unchanged():
    release = _release("v1.0.0", members=[_member("feature-x", spec=_artifact_status(status="in review"))])
    text = render_release_board_html(_data([release]))
    assert "in review" in text


def test_compound_narrative_status_only_leading_span_stripped():
    """QA B1: a real status cell — this repo's own `git-native-mid-cycle-
    board` qa.md — wraps only its leading word in backticks and continues
    with unwrapped free text; the old whole-value-wrap check left a literal
    backtick visible."""
    narrative = "`passed` — independent re-test (2026-08-19, second pass) reproduced B1–B5"
    release = _release("v1.0.0", members=[_member("feature-x", qa=_artifact_status(status=narrative))])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    assert "passed — independent re-test (2026-08-19, second pass) reproduced B1" in detail
    assert "`passed`" not in detail
    assert "`" not in detail.split("Unattributed commits")[0]


def test_caption_omits_redundant_member_name():
    """QA B2: the caption used to repeat the member's name (already stated
    by the `<h4>` directly above), which could clip at 375px inside the
    table's own scroll container for a long name."""
    release = _release("v1.0.0", members=[_member("a-very-long-feature-directory-name-indeed")])
    text = render_release_board_html(_data([release]))
    assert "<caption>Artifact status</caption>" in text
    assert "a-very-long-feature-directory-name-indeed — artifact status" not in text


def test_back_link_present_in_every_release_detail():
    releases = [_release("v1.0.0"), _release("v2.0.0")]
    text = render_release_board_html(_data(releases))
    assert text.count('class="back-link" href="#index"') == 2


def test_index_list_carries_id_index_for_back_link_target():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    assert 'id="index"' in text


# --- T5: unattributed commits verbatim / "none" (AC-2.4/2.5) ----------------


def test_unattributed_commit_shown_verbatim_never_reattributed():
    release = _release("v0.6.0", unattributed=[{"hash": "26e7f95", "subject": "feat: snapshot-report scorecard redesign"}])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    assert "26e7f95" in detail
    assert "feat: snapshot-report scorecard redesign" in detail


def test_empty_unattributed_states_none_explicitly():
    release = _release("v1.0.0", unattributed=[])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    unattributed_block = detail.split("Unattributed commits</h3>")[1]
    assert "none" in unattributed_block[:60]


# --- T6: badge hue keyed to type, never status; contrast ---------------------


def test_badge_hue_identical_for_failed_and_passed_status():
    release = _release("v1.0.0", members=[
        _member("passing-feature", qa=_artifact_status(status="passed")),
        _member("failing-feature", qa=_artifact_status(status="failed")),
    ])
    text = render_release_board_html(_data([release]))
    passing_hue = re.search(r'style="color:(#[0-9a-f]{6})">qa</span></td><td>passed', text)
    failing_hue = re.search(r'style="color:(#[0-9a-f]{6})">qa</span></td><td>failed', text)
    assert passing_hue and failing_hue
    assert passing_hue.group(1) == failing_hue.group(1) == _ARTIFACT_HUES["qa"]


def test_every_badge_carries_a_text_label_not_color_alone():
    release = _release("v1.0.0", members=[_member("feature-x")])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    for artifact in ("spec", "plan", "review", "qa", "release"):
        assert f">{artifact}</span>" in detail


@pytest.mark.parametrize("artifact,hue", list(_ARTIFACT_HUES.items()))
def test_every_artifact_hue_clears_wcag_small_text_floor_on_both_backgrounds(artifact, hue):
    """T6: badges sit on `--bg-secondary` (#12121a) — the CSS explicitly
    sets it, never inherited from a card ancestor — but review F7 pointed
    out the name overclaimed "both backgrounds" while only asserting one;
    now genuinely both, matching `--bg-secondary` and `--bg-card`."""
    assert _contrast_ratio(hue, "#12121a") >= 4.5
    assert _contrast_ratio(hue, "#16162a") >= 4.5


def test_text_secondary_clears_floor_on_both_backgrounds():
    for bg in ("#0a0a0f", "#16162a"):
        assert _contrast_ratio("#a0a0c0", bg) >= 4.5


# --- T7: honest empty / degenerate states (AC-3.1/AC-3.3) -------------------


def test_zero_tags_states_reason_empty_index_never_a_traceback():
    text = render_release_board_html(_data([], reason="repository has no tags"))
    assert "repository has no tags" in text
    assert "<li>" not in text  # no index rows
    assert "<article" not in text  # no release detail cards


def test_null_status_with_reason_shows_reason_next_to_badge():
    release = _release("v1.0.0", members=[
        _member("feature-x", spec=_artifact_status(status=None, date=None, reason="file not found")),
    ])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    assert "file not found" in detail


# --- T8: inline logo -----------------------------------------------------


def test_logo_embedded_as_inline_data_uri_with_alt_no_external_ref():
    text = render_release_board_html(_data([_release("v1.0.0")]))
    assert "data:image/png;base64," in text
    assert 'alt="aSPARK"' in text
    assert "<img" in text and 'src="http' not in text


def test_committed_logo_constant_decodes_within_page_weight_bound():
    import base64

    decoded = base64.b64decode(LOGO_PNG_BASE64)
    assert len(decoded) <= 30_000
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"  # a real PNG, not a placeholder string


# --- T9: escaping, named-error shape guard ------------------------------------


def test_hostile_commit_subject_escaped_in_unattributed():
    release = _release("v1.0.0", unattributed=[{"hash": "abc1234", "subject": _HOSTILE}])
    text = render_release_board_html(_data([release]))
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_hostile_status_string_escaped():
    release = _release("v1.0.0", members=[_member("feature-x", spec=_artifact_status(status=_HOSTILE))])
    text = render_release_board_html(_data([release]))
    assert "<script>alert(1)</script>" not in text


def test_hostile_reason_string_escaped():
    release = _release("v1.0.0", members=[
        _member("feature-x", spec=_artifact_status(status=None, date=None, reason=_HOSTILE)),
    ])
    text = render_release_board_html(_data([release]))
    assert "<script>alert(1)</script>" not in text


def test_hostile_member_name_escaped():
    release = _release("v1.0.0", members=[_member(_HOSTILE)])
    text = render_release_board_html(_data([release]))
    assert "<script>alert(1)</script>" not in text


def test_hostile_tag_escaped():
    text = render_release_board_html(_data([_release(_HOSTILE)]))
    assert "<script>alert(1)</script>" not in text


def test_malformed_data_raises_named_error_never_a_traceback(tmp_path):
    with pytest.raises(ReleaseMapUnreadableError):
        run_release_board_report({"releases": "not-a-list", "reason": None}, str(tmp_path))


# --- Review F1 (Blocker): hostile --output never raises a raw traceback ----


def test_output_pointing_at_an_existing_file_raises_named_error_not_a_traceback(tmp_path):
    blocker_file = tmp_path / "not-a-directory"
    blocker_file.write_text("x", encoding="utf-8")
    with pytest.raises(ReportUnwritableError):
        run_release_board_report(_data([_release("v1.0.0")]), str(blocker_file))


def test_output_unwritable_path_raises_named_error_not_a_traceback():
    with pytest.raises(ReportUnwritableError):
        run_release_board_report(_data([_release("v1.0.0")]), "/nonexistent-root-cannot-create/x")


# --- Review F2 (Major): NFR-4 bounded lists, disclosed as truncated --------


def test_members_beyond_bound_are_truncated_and_disclosed(monkeypatch):
    import aspark_insights.gitboard.releaseboard_report as mod

    monkeypatch.setattr(mod, "_MAX_MEMBERS_SHOWN", 2)
    release = _release("v1.0.0", members=[_member("a"), _member("b"), _member("c")])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert detail.count('<div class="member-block">') == 2
    assert "Showing the first 2 of 3" in detail


def test_unattributed_beyond_bound_are_truncated_and_disclosed(monkeypatch):
    import aspark_insights.gitboard.releaseboard_report as mod

    monkeypatch.setattr(mod, "_MAX_UNATTRIBUTED_SHOWN", 1)
    release = _release("v1.0.0", unattributed=[
        {"hash": "aaa1111", "subject": "x"}, {"hash": "bbb2222", "subject": "y"},
    ])
    text = render_release_board_html(_data([release]))
    detail = text.split('id="rel-0"')[1]
    assert detail.count('<li class="commit-item">') == 1
    assert "Showing the first 1 of 2" in detail


def test_lists_within_bound_show_no_truncation_note():
    release = _release("v1.0.0", members=[_member("a")], unattributed=[{"hash": "aaa1111", "subject": "x"}])
    text = render_release_board_html(_data([release]))
    assert 'class="truncation-note"' not in text


# --- Review F5: work_types shown when present, dropped only when absent ----


def test_pseudo_release_work_types_shown_when_present():
    pseudo = _pseudo(previous_tag="v1.0.0", commits_value=4)
    pseudo["work_types"] = {"value": {"feat": 50, "fix": 25, "unclassified": 25}, "reason": None}
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1]
    assert "Work types: feat 50%, fix 25%, unclassified 25%" in detail


def test_pseudo_release_work_types_render_in_fixed_order_not_dict_order():
    """Re-review F11: the test above happens to pass a dict already in
    `RECOGNIZED_TYPES` order, so it would still pass if the renderer fell
    back to raw dict iteration. Feed it in reverse insertion order — the
    output must still be the declared order (NFR-6)."""
    pseudo = _pseudo(previous_tag="v1.0.0", commits_value=4)
    pseudo["work_types"] = {
        "value": {"unclassified": 25, "test": 10, "docs": 15, "fix": 25, "feat": 25},
        "reason": None,
    }
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1]
    assert "Work types: feat 25%, fix 25%, docs 15%, test 10%, unclassified 25%" in detail


def test_pseudo_release_work_types_absent_renders_no_clause():
    pseudo = _pseudo(previous_tag="v1.0.0", commits_value=4)
    assert "work_types" not in pseudo
    text = render_release_board_html(_data([_release("v1.0.0"), pseudo]))
    detail = text.split('id="rel-1"')[1]
    assert "Work types" not in detail
