"""RBD-T2..T6: document-content viewing — dedup, honest states, page-budget
disclosure, visual framing, hardening (release-board-docs US-2)."""

from __future__ import annotations

import re

import pytest

from aspark_insights.errors import ReleaseMapUnreadableError
from aspark_insights.gitboard.releaseboard_report import (
    render_release_board_html,
    run_release_board_report,
)

_HOSTILE_BODY = (
    "# Notes\n\n"
    "<script>alert(1)</script>\n"
    '<img src=x onerror="alert(2)">\n'
    "</pre><script>alert(3)</script>\n"
    "Status: failed — this is prose, not a real board status.\n"
)


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


def _doc(
    text="content", *, reason=None, empty=False, truncated=False,
    byte_truncated=None, line_truncated=None,
    total_lines=None, shown_lines=None, total_bytes=None,
):
    shown_lines = shown_lines if shown_lines is not None else (len(text.split("\n")) if text else 0)
    total_lines = total_lines if total_lines is not None else shown_lines
    total_bytes = total_bytes if total_bytes is not None else len(text.encode("utf-8"))
    # Default: a caller passing bare `truncated=True` without specifying
    # which cap tripped means "line cap" (the common test case) — bare
    # `byte_truncated`/`line_truncated` override this explicitly.
    line_truncated = line_truncated if line_truncated is not None else truncated
    byte_truncated = byte_truncated if byte_truncated is not None else False
    return {
        "text": text, "reason": reason, "empty": empty, "truncated": truncated,
        "byte_truncated": byte_truncated, "line_truncated": line_truncated,
        "total_lines": total_lines, "shown_lines": shown_lines, "total_bytes": total_bytes,
    }


def _artifact_status(status="approved", date="2026-08-01", reason=None) -> dict:
    return {"status": status, "date": date, "reason": reason}


def _member(name: str, **status_overrides) -> dict:
    status = {a: _artifact_status() for a in ("spec", "plan", "review", "qa", "release")}
    status.update(status_overrides)
    return {"name": name, "status": status}


def _release(tag, previous_tag=None, next_tag=None, members=None, unattributed=None) -> dict:
    return {
        "tag": tag, "previous_tag": previous_tag, "next_tag": next_tag,
        "members": members if members is not None else [_member(f"{tag}-feature")],
        "unattributed": unattributed if unattributed is not None else [],
    }


def _full_docs(text="content") -> dict:
    return {a: _doc(text) for a in ("spec", "plan", "review", "qa", "release")}


def _sized_docs(total_bytes: int) -> dict:
    """A feature whose combined 5-artifact size is exactly `total_bytes` —
    all of it in `spec`, the other 4 artifacts empty, so budget-consumption
    tests can reason about one round number per feature."""
    docs = {a: _doc("") for a in ("spec", "plan", "review", "qa", "release")}
    docs["spec"] = _doc("z" * total_bytes)
    return docs


def _data(releases=None, reason=None) -> dict:
    return {
        "provenance": {"as_of": "2026-08-23", "insights_version": "0.10.0", "source": "git-interim", "git_available": True},
        "releases": releases if releases is not None else [],
        "reason": reason,
    }


# --- T2: dedup, details markup, home rendering -------------------------------


def test_documents_none_renders_byte_identical_to_no_documents():
    releases = [_release("v1.0.0")]
    without = render_release_board_html(_data(releases))
    with_none = render_release_board_html(_data(releases), None)
    assert without == with_none
    assert '<details class="doc-content"' not in without


def test_feature_document_renders_as_closed_details_with_named_summary():
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("# Spec: feature-x\n\nBody text.")}
    text = render_release_board_html(_data([release]), documents)
    assert '<details class="doc-content"' in text
    assert "<summary>spec.md</summary>" in text
    assert "Body text." in text
    # closed by default — no `open` attribute
    assert '<details class="doc-content" id="doc-f0-spec" open' not in text


def test_feature_appearing_in_two_releases_embedded_only_once():
    """T2 dedup: same feature, member of both releases; documents appear
    under only its first occurrence in DISPLAY order (newest-first, so the
    newer release is the home)."""
    older = _release("v1.0.0", members=[_member("shared-feature")])
    newer = _release("v2.0.0", members=[_member("shared-feature")])
    documents = {"shared-feature": _full_docs("unique marker text")}
    text = render_release_board_html(_data([older, newer]), documents)
    # once per artifact (5), never doubled by appearing under both releases
    assert text.count("unique marker text") == 5
    # v2.0.0 is newer -> display order puts it first -> it's the home
    newer_detail = text.split('id="rel-1"')[1].split("</article>")[0]
    older_detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "unique marker text" in newer_detail
    assert "unique marker text" not in older_detail
    assert "doc-content-link" in older_detail
    # Review F13: links to the member block itself, not just the release
    # card (a card can hold up to 50 members).
    assert 'href="#member-1-0"' in older_detail


def test_non_home_occurrence_links_to_home_release_label():
    older = _release("v1.0.0", members=[_member("shared-feature")])
    newer = _release("v2.0.0", members=[_member("shared-feature")])
    documents = {"shared-feature": _full_docs("x")}
    text = render_release_board_html(_data([older, newer]), documents)
    older_detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "Documents shown under" in older_detail
    assert ">v2.0.0<" in older_detail


def test_missing_documents_entry_for_a_member_degrades_honestly_per_artifact():
    """A member whose feature never made it into the `documents` dict
    (shouldn't normally happen — the collector reads every member — but
    must degrade honestly if it does) still renders each artifact's
    `<details>`, each stating "not read" — never a crash, and never a
    silent, unexplained absence of the capability entirely."""
    release = _release("v1.0.0", members=[_member("undocumented-feature")])
    text = render_release_board_html(_data([release]), {})  # empty documents dict
    assert '<details class="doc-content"' in text
    # Review F14: a real, specific reason — not the bare "not read"
    assert "document not collected for this render" in text


# --- T3: honest per-document states (AC-2.2/2.3) -----------------------------


def test_missing_document_shows_its_reason_in_the_details_body():
    release = _release("v1.0.0", members=[_member("feature-x")])
    docs = _full_docs()
    docs["plan"] = _doc(reason="file not found")
    text = render_release_board_html(_data([release]), {"feature-x": docs})
    assert "file not found" in text


def test_empty_document_states_plainly_distinct_from_missing():
    release = _release("v1.0.0", members=[_member("feature-x")])
    docs = _full_docs()
    docs["release"] = _doc("", empty=True)
    text = render_release_board_html(_data([release]), {"feature-x": docs})
    assert "This document is empty." in text


# --- T4: truncation disclosure + page budget (AC-2.5/A5) ---------------------


def test_line_truncated_document_discloses_shown_of_total():
    release = _release("v1.0.0", members=[_member("feature-x")])
    docs = _full_docs()
    docs["spec"] = _doc("line\n" * 100, truncated=True, shown_lines=100, total_lines=3000)
    text = render_release_board_html(_data([release]), {"feature-x": docs})
    assert "Showing the first 100 of 3000 lines of this document." in text


def test_byte_truncated_single_line_document_discloses_bytes_not_lines():
    release = _release("v1.0.0", members=[_member("feature-x")])
    docs = _full_docs()
    docs["spec"] = _doc(
        "x" * 100, truncated=True, byte_truncated=True, line_truncated=False,
        shown_lines=1, total_lines=1, total_bytes=1_000_000,
    )
    text = render_release_board_html(_data([release]), {"feature-x": docs})
    assert "Showing the first 100 of 1000000 bytes of this document." in text


def test_both_caps_tripped_discloses_both_never_just_lines():
    """Review F6: a huge first line trips the byte cap AND forces the
    partial trailing line to be dropped (so `shown_lines < total_lines` by
    one) — the line-only wording would wrongly imply the shown line(s)
    were complete."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    docs = _full_docs()
    docs["spec"] = _doc(
        "x" * 100, truncated=True, byte_truncated=True, line_truncated=True,
        shown_lines=1, total_lines=12, total_bytes=1_000_000,
    )
    text = render_release_board_html(_data([release]), {"feature-x": docs})
    assert "Showing the first 1 of 12 lines (100 of 1000000 bytes) of this document." in text


def test_page_budget_exhausted_discloses_not_embedded_never_silent():
    release = _release("v1.0.0", members=[_member("big-feature")])
    huge_text = "x" * 3_000_000  # exceeds the 2.5MB page budget alone
    documents = {"big-feature": _full_docs(huge_text)}
    text = render_release_board_html(_data([release]), documents)
    assert "Not embedded in this page" in text
    assert ".spark/big-feature/" in text
    assert huge_text not in text  # never partially dumped either


def test_page_budget_consumed_in_display_order_first_wins():
    """Two features that together exceed the budget: whichever is first in
    NEWEST-FIRST display order gets embedded, the later one is disclosed."""
    older = _release("v1.0.0", members=[_member("feature-old")])
    newer = _release("v2.0.0", members=[_member("feature-new")])
    documents = {
        "feature-old": _sized_docs(2_000_000),  # 2MB each; budget is 2.5MB total
        "feature-new": _sized_docs(2_000_000),
    }
    text = render_release_board_html(_data([older, newer]), documents)
    newer_detail = text.split('id="rel-1"')[1].split("</article>")[0]
    older_detail = text.split('id="rel-0"')[1].split("</article>")[0]
    # newer release displays first (rel-1, v2.0.0) -> its feature wins the budget
    assert "Not embedded in this page" in older_detail
    assert "Not embedded in this page" not in newer_detail
    # exactly one of them got embedded, not both, not neither
    embedded_count = text.count('<summary>spec.md</summary>')
    assert embedded_count == 1


def test_budget_overflow_is_disclosed_at_page_level_not_only_per_member():
    """Review F7, caught unguarded at re-review: the per-member notice was
    tested, the *page-level* `.truncation-note` that F7 actually added was
    not — deleting `_render_page_budget_notice` from the page left the whole
    suite green. T4's DoD requires a page-level count plus each omitted
    feature's path, above the release cards, so a reader learns what is
    missing without opening all fifty of them.

    Also pins the best-fit behaviour the DoD now describes: a later,
    *smaller* feature still fits after a larger one was skipped."""
    rel = _release("v1.0.0", members=[
        _member("a-huge"), _member("b-giant"), _member("c-tiny"),
    ])
    documents = {
        "a-huge": _sized_docs(2_000_000),   # fits: 2.0MB of the 2.5MB budget
        "b-giant": _sized_docs(2_000_000),  # skipped: no room left
        "c-tiny": _full_docs("# t\ntiny\n"),  # best-fit: still fits after the skip
    }
    text = render_release_board_html(_data([rel]), documents)

    page_note = (
        "1 feature's documents were not embedded in this page"
    )
    assert page_note in text
    assert ".spark/b-giant/" in text
    # page-level means above the first release card, not buried in a member
    assert text.index(page_note) < text.index('class="release-card"')
    # best-fit, not a hard stop: the small later feature is still embedded
    assert "tiny" in text
    assert text.count('<summary>spec.md</summary>') == 2


def test_member_past_the_50_bound_never_becomes_an_unreachable_home():
    """Review F3 (Major): `_document_plan` used to iterate ALL members
    while `_render_members_section` renders only the first 50 — a feature
    whose first display-order occurrence sat at slot >=50 got "homed" to a
    member block that never renders, vanishing its documents entirely
    while another release still linked to them."""
    many_members = [_member(f"f{i}") for i in range(60)]
    release_a = _release("v2.0.0", members=many_members)  # newer -> displays first
    release_b = _release("v1.0.0", members=[_member("f55")])  # older, shares f55
    documents = {m["name"]: _full_docs(f"content for {m['name']}") for m in many_members}
    documents["f55"] = _full_docs("content for f55")
    text = render_release_board_html(_data([release_b, release_a]), documents)
    # f55 (index 55 in release_a's member list) is now capped out of
    # _document_plan too, so its real home is release_b (the only release
    # where it's within the rendered slice) — never a vanished feature.
    assert "content for f55" in text
    assert text.count("content for f55") >= 1


# --- T5: visual framing, wayfinding ------------------------------------------


def test_document_block_has_provenance_and_repo_relative_path():
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("content")}
    text = render_release_board_html(_data([release]), documents)
    assert "Document content" in text
    assert ".spark/feature-x/spec.md" in text


def test_document_block_ends_with_back_link_to_member():
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("content")}
    text = render_release_board_html(_data([release]), documents)
    assert "doc-back-link" in text
    assert "Back to feature-x" in text
    # the back-link target must be a real, existing member id
    member_id_match = re.search(r'<div class="member-block" id="(member-\d+-\d+)"', text)
    assert member_id_match
    assert f'href="#{member_id_match.group(1)}"' in text


def test_sr_only_state_prefix_actually_has_a_visually_hiding_css_rule():
    """Review F2: `markdownlite` emits `<span class="sr-only">checked:</span>`
    on every checklist item, but no `.sr-only` rule existed in `_STYLE`, so
    the prefix rendered as visible body copy next to every glyph. Asserting
    the class name is in the markup (test_markdownlite.py) cannot catch that
    — the stylesheet has to actually define it."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("- [x] done\n- [ ] not done")}
    text = render_release_board_html(_data([release]), documents)
    assert 'class="sr-only"' in text
    style = text.split("<style>")[1].split("</style>")[0]
    assert ".sr-only" in style
    rule = style.split(".sr-only", 1)[1].split("}", 1)[0]
    assert "position: absolute" in rule and "1px" in rule


def test_doc_content_prose_and_code_wrap_long_unbreakable_spans():
    """QA B1 (Major): a long inline `<code>` span in embedded document
    prose (a real test-name reference in this project's own `plan.md`
    files) was not wrapped and pushed the whole page out sideways at
    375px — `.doc-content pre` had `word-break` already, `p`/`li`/`code`
    never did. Asserting the class exists in markup can't catch a missing
    wrap rule — the stylesheet has to actually define it."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("A paragraph with `a_very_long_unbreakable_inline_code_span_reference` inside it.")}
    text = render_release_board_html(_data([release]), documents)
    assert "<code>" in text
    style = text.split("<style>")[1].split("</style>")[0]
    p_li_rule = style.split(".doc-content p, .doc-content li", 1)[1].split("}", 1)[0]
    assert "overflow-wrap" in p_li_rule
    code_rule = style.split(".doc-content code", 1)[1].split("}", 1)[0]
    assert "overflow-wrap" in code_rule or "word-break" in code_rule


def test_new_doc_content_color_pairs_clear_wcag_floor():
    # .doc-content text (--text-secondary on --bg-secondary) and the
    # provenance label (same pair) — both must clear 4.5:1.
    assert _contrast_ratio("#a0a0c0", "#12121a") >= 4.5


# --- T6: hardening — hostile document body, path validation, determinism ----


def test_hostile_document_body_is_fully_inert():
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs(_HOSTILE_BODY)}
    text = render_release_board_html(_data([release]), documents)
    assert "<script>alert(1)</script>" not in text
    assert "<script>alert(3)</script>" not in text
    assert 'onerror="alert(2)"' not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text
    assert "&lt;script&gt;alert(3)&lt;/script&gt;" in text


def test_status_shaped_prose_in_a_document_body_does_not_produce_a_second_badge():
    """A document's own prose containing 'Status: failed' must not be
    mistaken for — or rendered as — one of the board's own `.badge`
    elements (finding 3)."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs(_HOSTILE_BODY)}
    text = render_release_board_html(_data([release]), documents)
    doc_section = text.split('<summary>spec.md</summary>')[1].split("</details>")[0]
    assert '<span class="badge"' not in doc_section


def test_malformed_documents_argument_raises_named_error_not_a_traceback(tmp_path):
    release = _release("v1.0.0", members=[_member("feature-x")])
    with pytest.raises(ReleaseMapUnreadableError):
        run_release_board_report(_data([release]), str(tmp_path), documents="not-a-dict")


# --- T10: structured rendering, full-page heading order ---------------------


def test_full_page_has_exactly_one_h1_regardless_of_document_content():
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("# Spec: feature-x\n\n# Another H1 inside the doc")}
    text = render_release_board_html(_data([release]), documents)
    assert text.count("<h1>") == 1  # the page's own h1, never doubled by a document's own


def test_document_headings_never_produce_a_second_page_level_heading():
    """A document's own top-level `# Spec: <name>` heading must be demoted
    to h5, never compete with the page's h1/h2."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs("# Spec: feature-x\n\nBody.")}
    text = render_release_board_html(_data([release]), documents)
    doc_section = text.split('<summary>spec.md</summary>')[1].split("</details>")[0]
    assert "<h5>Spec: feature-x</h5>" in doc_section
    assert "<h1>" not in doc_section
    assert "<h2>" not in doc_section


def test_structured_path_hostile_fixture_re_run_independently():
    """T6's hostile fixture, re-run through the structured (markdownlite)
    path — not assumed inert just because the `<pre>` path already held."""
    release = _release("v1.0.0", members=[_member("feature-x")])
    documents = {"feature-x": _full_docs(_HOSTILE_BODY)}
    text = render_release_board_html(_data([release]), documents)
    assert "<script>alert(1)</script>" not in text
    assert "<script>alert(3)</script>" not in text
    assert 'onerror="alert(2)"' not in text
    doc_section = text.split('<summary>spec.md</summary>')[1].split("</details>")[0]
    assert '<span class="badge"' not in doc_section  # status-shaped prose still not mistaken for a badge


def test_double_render_with_documents_is_byte_identical():
    release = _release("v1.0.0", members=[_member("feature-x"), _member("feature-y")])
    documents = {"feature-x": _full_docs("a"), "feature-y": _full_docs("b")}
    data = _data([release])
    first = render_release_board_html(data, documents)
    second = render_release_board_html(data, documents)
    assert first == second
