"""GB-T7/T8: board HTML — block order, provenance, listings, accessibility
mechanisms (AC-4.1-4.13, NFR-7).
"""

from __future__ import annotations

import re

from aspark_insights.gitboard.report import render_board_html

_EXTERNAL_REF_PATTERN = re.compile(r'(https?://|<link\b|<script\b[^>]*\bsrc=)', re.IGNORECASE)
_HOSTILE = "<script>alert(1)</script>"


def _board(**overrides) -> dict:
    base = {
        "provenance": {
            "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
            "git_available": True, "resolved_tag": "v1.0.0", "resolved_tag_reason": None,
            "shallow": False,
        },
        "commits": {
            "value": 2, "reason": None,
            "shown": [
                {"hash": "abc123", "subject": "feat: add thing", "date": "2026-08-13T10:00:00+00:00"},
                {"hash": "def456", "subject": "no prefix here", "date": "2026-08-12T10:00:00+00:00"},
            ],
            "shown_count": 2, "truncated": False,
        },
        "branches": [
            {"name": "main", "tip_hash": "abc123", "tip_date": "2026-08-13T10:00:00+00:00", "age_days": 0, "age_reason": None},
        ],
    }
    base.update(overrides)
    return base


# --- AC-4.1: static, offline, no JS ------------------------------------------


def test_html_has_no_javascript_no_external_refs():
    text = render_board_html(_board())
    assert "<script>" not in text
    assert not _EXTERNAL_REF_PATTERN.search(text)


def test_html_has_viewport_meta_doctype_title():
    text = render_board_html(_board())
    assert text.startswith("<!DOCTYPE html>")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in text
    assert "<title>" in text
    assert '<html lang="en">' in text


# --- AC-4.13: exact block order, absent block omits its heading -------------


def test_block_order_is_exact_by_byte_offset():
    board = _board(work_types={"value": {"feat": 100}, "reason": None})
    text = render_board_html(board)
    pos_h1 = text.index("<h1")
    pos_marker = text.index('class="interim-marker"')
    pos_sentence = text.index('class="answer-sentence"')
    pos_cards = text.index('class="metric-grid"')
    pos_worktypes = text.index('id="work-types"')
    pos_commits = text.index('id="commits"')
    pos_branches = text.index('id="branches"')
    pos_provenance = text.index('id="provenance"')
    assert (
        pos_h1 < pos_marker < pos_sentence < pos_cards < pos_worktypes
        < pos_commits < pos_branches < pos_provenance
    )


def test_absent_work_types_omits_its_heading_entirely():
    board = _board()  # no "work_types" key at all
    text = render_board_html(board)
    assert 'id="work-types"' not in text
    assert "<h2>Work types</h2>" not in text
    # the rest of the order still holds without it
    pos_cards = text.index('class="metric-grid"')
    pos_commits = text.index('id="commits"')
    assert pos_cards < pos_commits


def test_every_present_block_has_an_h2():
    board = _board(work_types={"value": None, "reason": "too few"})
    text = render_board_html(board)
    for heading in ("Work types", "Commits", "Branches", "Provenance"):
        assert f"<h2>{heading}</h2>" in text


# --- AC-4.5: interim marker — neutral, distinct from .stale-cue ------------


def test_interim_marker_is_legible_near_top_and_not_stale_cue_styled():
    text = render_board_html(_board())
    assert "INTERIM (git-native)" in text
    marker_tag = text[text.index('<p class="interim-marker"'):text.index("</p>", text.index('<p class="interim-marker"'))]
    assert "stale-cue" not in marker_tag  # the marker's own element never reuses the alarm class
    # "Near the top, unscrolled" is a DOM-position claim, not a raw byte
    # offset — the embedded <style> block is large and renders with zero
    # visible height, so measure position within <body> instead.
    body = text.split("<body>")[1]
    pos_marker = body.index("INTERIM (git-native)")
    pos_h1 = body.index("<h1")
    pos_sentence = body.index('class="answer-sentence"')
    assert pos_h1 < pos_marker < pos_sentence  # directly after <h1>, before anything else


def test_marker_source_field_also_lives_in_provenance():
    text = render_board_html(_board())
    provenance_section = text.split('id="provenance"')[1]
    assert "git-interim" in provenance_section


# --- AC-4.8: answer sentence, degenerate states in words --------------------


def test_answer_sentence_states_real_counts():
    text = render_board_html(_board())
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "2 commits landed since v1.0.0" in sentence
    assert "1 local branch" in sentence


def test_answer_sentence_no_tag_state_in_words_not_a_placeholder():
    board = _board(provenance={
        "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
        "git_available": True, "resolved_tag": None, "resolved_tag_reason": "repository has no tags",
        "shallow": False,
    }, commits={"value": None, "reason": "repository has no tags; commits-since-release is undefined without a release marker"})
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "no tags" in sentence
    assert "null" not in sentence.lower()
    assert "&mdash;" not in sentence and "—" not in sentence.split("no tags")[0][-3:]


def test_answer_sentence_zero_commits_since_tag_is_a_true_zero_sentence():
    board = _board(commits={"value": 0, "reason": None, "shown": [], "shown_count": 0, "truncated": False})
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "Nothing has landed since v1.0.0" in sentence


def test_answer_sentence_zero_branches_stated_plainly():
    board = _board(branches=[])
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "No local branches found" in sentence


def test_answer_sentence_shallow_qualifier_inline():
    board = _board(provenance={
        "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
        "git_available": True, "resolved_tag": "v1.0.0", "resolved_tag_reason": None, "shallow": True,
    })
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "At least 2 commits" in sentence


# --- AC-4.9: absent / null / true-zero trichotomy on stat cards -------------


def test_absent_days_since_tag_renders_no_card_at_all():
    board = _board()  # no "days_since_tag" key
    text = render_board_html(board)
    stat_row = text.split('class="metric-grid"')[1].split("</div>\n</div>")[0]
    assert "Days since tag" not in stat_row


def test_null_days_since_tag_renders_dashed_null_card():
    board = _board(days_since_tag={"value": None, "reason": "commit date for tag 'v1.0.0' could not be read"})
    text = render_board_html(board)
    stat_row = text.split('class="metric-grid"')[1]
    assert "Days since tag" in stat_row
    assert "metric-card--null" in stat_row
    assert "could not be read" in stat_row


def test_true_zero_branch_count_renders_a_real_zero_card_not_a_null_card():
    board = _board(branches=[])
    text = render_board_html(board)
    stat_row = text.split('class="metric-grid"')[1].split("</div>\n</div>")[0] + text.split('class="metric-grid"')[1]
    assert '<p class="metric-value">0</p>' in text  # branch count is a real 0
    # and it is NOT rendered as a null card
    branch_card_idx = text.index("Local branches")
    branch_card = text[branch_card_idx - 100:branch_card_idx + 200]
    assert "metric-card--null" not in branch_card


def test_oldest_branch_age_card_absent_when_no_branches():
    board = _board(branches=[])
    text = render_board_html(board)
    stat_row = text.split('class="metric-grid"')[1].split("<h2>")[0]
    assert "Oldest branch age" not in stat_row


# --- AC-4.2 / AC-4.7: honest-null shape reused from render.py --------------


def test_null_commits_card_uses_the_shared_null_shape():
    board = _board(
        provenance={
            "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
            "git_available": True, "resolved_tag": None, "resolved_tag_reason": "repository has no tags",
            "shallow": False,
        },
        commits={"value": None, "reason": "repository has no tags"},
    )
    text = render_board_html(board)
    assert "metric-card--null" in text
    assert "metric-value--null" in text
    assert "Not computed" in text


# --- AC-4.3: no red/green judgment coloring ---------------------------------


def test_no_judgment_color_in_stylesheet():
    text = render_board_html(_board())
    style = text.split("<style>")[1].split("</style>")[0]
    for hue in ("red", "green", "#f00", "#0f0", "#ff0000", "#00ff00"):
        assert hue not in style.lower()


# --- AC-4.11: work-type breakdown follows .confidence-mix pattern ----------


def test_work_types_breakdown_uses_confidence_mix_pattern_fixed_order():
    board = _board(work_types={
        "value": {"fix": 30, "feat": 50, "unclassified": 20}, "reason": None,
    })
    text = render_board_html(board)
    assert "confidence-mix" in text
    legend = text.split('class="confidence-legend"')[1].split("</p>")[0]
    # fixed declared order: feat before fix before unclassified (RECOGNIZED_TYPES order)
    assert legend.index("feat") < legend.index("fix") < legend.index("unclassified")


def test_null_work_types_renders_no_bar_only_a_null_card():
    board = _board(work_types={"value": None, "reason": "too few commits carry a recognized type"})
    text = render_board_html(board)
    worktypes_section = text.split('id="work-types"')[1].split("</section>")[0]
    assert "confidence-mix" not in worktypes_section
    assert "metric-card--null" in worktypes_section


# --- AC-4.12: named accessibility mechanisms --------------------------------


def test_branch_listing_is_a_real_table_with_scope_and_caption():
    text = render_board_html(_board())
    branches_section = text.split('id="branches"')[1].split("</section>")[0]
    assert "<table>" in branches_section
    assert "<caption>Branches</caption>" in branches_section
    assert '<th scope="col">' in branches_section


def test_branch_age_cell_carries_numeric_text_and_a_bar():
    board = _board(branches=[
        {"name": "main", "tip_hash": "abc", "tip_date": "2026-08-13T10:00:00+00:00", "age_days": 5, "age_reason": None},
    ])
    text = render_board_html(board)
    branches_section = text.split('id="branches"')[1]
    assert "5 days" in branches_section  # numeric text, never bar length alone
    assert "metric-bar-fill" in branches_section


def test_commit_listing_has_four_explicit_field_labels_including_type():
    text = render_board_html(_board())
    commits_section = text.split('id="commits"')[1].split("</section>")[0]
    for label in ("Type", "Subject", "Hash", "Date"):
        assert f"<dt>{label}</dt>" in commits_section


def test_commit_listing_has_programmatic_name():
    text = render_board_html(_board())
    assert '<section id="commits">\n<h2>Commits</h2>' in text


def test_unrecognized_commit_gets_unclassified_badge():
    text = render_board_html(_board())
    commits_section = text.split('id="commits"')[1]
    assert "badge--unclassified" in commits_section
    assert "unclassified" in commits_section


# --- AC-4.6: provenance renders on every report, dl field/value pairing ----


def test_provenance_section_has_dl_field_value_pairing():
    text = render_board_html(_board())
    provenance_section = text.split('id="provenance"')[1].split("</section>")[0]
    assert "<dl>" in provenance_section
    assert "<dt>as_of</dt><dd>2026-08-13</dd>" in provenance_section
    assert "<dt>source</dt><dd>git-interim</dd>" in provenance_section
    assert "<dt>shallow</dt><dd>False</dd>" in provenance_section


def test_provenance_shows_no_tag_reason_when_tag_absent():
    board = _board(
        provenance={
            "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
            "git_available": True, "resolved_tag": None, "resolved_tag_reason": "repository has no tags",
            "shallow": False,
        },
        commits={"value": None, "reason": "repository has no tags"},
    )
    text = render_board_html(board)
    provenance_section = text.split('id="provenance"')[1]
    assert "repository has no tags" in provenance_section


# --- AC-1.7 / escaping: every dynamic string flows through _esc ------------


def test_hostile_commit_subject_is_escaped():
    board = _board(commits={
        "value": 1, "reason": None,
        "shown": [{"hash": "abc", "subject": _HOSTILE, "date": "2026-08-13T10:00:00+00:00"}],
        "shown_count": 1, "truncated": False,
    })
    text = render_board_html(board)  # must not raise
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_hostile_branch_name_is_escaped():
    board = _board(branches=[
        {"name": _HOSTILE, "tip_hash": "abc", "tip_date": "2026-08-13T10:00:00+00:00", "age_days": 0, "age_reason": None},
    ])
    text = render_board_html(board)
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_hostile_tag_name_in_answer_sentence_and_provenance_is_escaped():
    board = _board(provenance={
        "as_of": "2026-08-13", "insights_version": "0.5.0", "source": "git-interim",
        "git_available": True, "resolved_tag": _HOSTILE, "resolved_tag_reason": None, "shallow": False,
    })
    text = render_board_html(board)
    assert "<script>alert(1)</script>" not in text


# --- Truncation disclosure (NFR-4) ------------------------------------------


def test_no_interactive_elements_anywhere():
    """NFR-7: fully static, no focusable element — checkable from source
    since no JS ever runs to add one at runtime (AC-4.1)."""
    text = render_board_html(_board(work_types={"value": {"feat": 100}, "reason": None}))
    for tag in ("<a ", "<a>", "<button", "<input", "<select", "<textarea"):
        assert tag not in text


def test_truncation_note_visible_in_context_when_bounded():
    board = _board(commits={
        "value": 75, "reason": None,
        "shown": [{"hash": f"h{i}", "subject": "feat: x", "date": "2026-08-13T10:00:00+00:00"} for i in range(50)],
        "shown_count": 50, "truncated": True,
    })
    text = render_board_html(board)
    commits_section = text.split('id="commits"')[1].split("</section>")[0]
    assert "Showing the most recent 50 of 75" in commits_section
