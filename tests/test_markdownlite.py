"""RBD-T7/T8/T9: markdownlite — bounded Markdown-to-HTML rendering."""

from __future__ import annotations

from aspark_insights.gitboard.markdownlite import render_markdown


# --- T7: core constructs -----------------------------------------------------


def test_atx_heading_base_level_maps_hash_to_h5():
    assert render_markdown("# Title") == "<h5>Title</h5>\n"


def test_paragraph_renders_as_p():
    assert render_markdown("Just some text.") == "<p>Just some text.</p>\n"


def test_bold_italic_code_render_correctly():
    out = render_markdown("**bold** *italic* `code`")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out
    assert "<code>code</code>" in out


def test_underscore_italic_also_supported():
    assert "<em>word</em>" in render_markdown("_word_")


def test_snake_case_identifiers_are_never_italicised():
    """Review F11, caught unguarded at re-review: the word-boundary
    lookarounds could be deleted outright and the whole suite stayed green,
    while `test_releaseboard_render` rendered as
    `test<em>releaseboard</em>render` on the real page — the exact defect
    F11 reported, in exactly the documents this feature exists to make
    readable."""
    for identifier in (
        "test_releaseboard_render", "git_init", "_leading", "trailing_",
        "mid_dle", "__dunder__", "a_b_c_d", "_word_s", "1_word_",
    ):
        assert "<em>" not in render_markdown(identifier), identifier
        assert identifier in render_markdown(identifier), identifier


def test_real_italics_still_work_when_they_touch_word_boundaries():
    """The other half of F11: the fix must not over-reach onto legitimate
    emphasis that abuts punctuation, quotes or brackets."""
    for source in ("_word_.", "(_word_)", "[_word_]", "_word_, then",
                   'say _word_ here', '"_word_"', "_multi word phrase_"):
        assert "<em>" in render_markdown(source), source


def test_fenced_code_block_preserves_content_escaped():
    out = render_markdown("```\n<script>x</script>\nline2\n```")
    assert "<pre><code>" in out
    assert "&lt;script&gt;x&lt;/script&gt;" in out
    assert "line2" in out
    assert "<script>x</script>" not in out


def test_horizontal_rule_renders_hr():
    assert "<hr>" in render_markdown("---")


def test_html_comment_is_stripped_entirely():
    out = render_markdown("before\n\n<!-- internal note -->\n\nafter")
    assert "internal note" not in out
    assert "before" in out and "after" in out


def test_multiline_html_comment_is_stripped():
    out = render_markdown("<!-- start\nmiddle\nend -->\n\nvisible text")
    assert "start" not in out and "middle" not in out and "end" not in out
    assert "visible text" in out


def test_unterminated_comment_never_silently_drops_the_rest_of_the_document():
    """Review F4: the old scan-to-EOF-looking-for-'-->' approach silently
    discarded every remaining line when the comment never closed — a whole-
    document loss AC-3.4 explicitly forbids."""
    out = render_markdown("<!-- start\nmiddle\n# Heading\nafter text")
    assert "Heading" in out
    assert "after text" in out


def test_comment_closed_same_line_preserves_the_remainder():
    out = render_markdown("<!-- hidden --> visible remainder")
    assert "hidden" not in out
    assert "visible remainder" in out


def test_allowed_link_schemes_become_real_anchors():
    for href in ("https://example.com", "http://example.com", "mailto:a@b.com", "#anchor", "relative/path.md"):
        out = render_markdown(f"[text]({href})")
        assert f'<a href="{href}"' in out


def test_javascript_scheme_link_never_becomes_an_anchor():
    """T7's own DoD: `[x](javascript:alert(1))` renders as plain text, not
    an anchor — the core security property, not exact text fidelity."""
    out = render_markdown("[x](javascript:alert(1))")
    assert "<a " not in out
    assert "javascript:" not in out


def test_data_scheme_link_never_becomes_an_anchor():
    out = render_markdown("[x](data:text/html,<script>alert(1)</script>)")
    assert "<a " not in out


def test_case_varied_allowed_schemes_still_become_real_anchors():
    """Review F5: `HTTP://`/`MAILTO:` were previously (safely, but wrongly
    per the function's own docstring) rejected as unknown schemes."""
    for href in ("HTTP://example.com", "HTTPS://example.com", "MAILTO:a@b.com", "HtTpS://x"):
        out = render_markdown(f"[text]({href})")
        assert "<a href=" in out, f"{href} should be allowed"


def test_protocol_relative_url_is_rejected():
    """Review F5: `//evil.example.com` is neither http(s)/mailto/fragment
    nor a genuine relative path — on a `file://`-opened page it resolves
    to whatever host the browser fills in, an attacker-steerable target."""
    out = render_markdown("[x](//evil.example.com/path)")
    assert "<a " not in out


def test_unrecognized_construct_degrades_to_plain_text_never_crashes():
    """AC-3.4: a blockquote (outside A3's bounded set) is not dropped —
    it becomes plain, visible, escaped text, and the rest of the document
    still renders."""
    out = render_markdown("> a blockquote\n\nafter text")
    assert "a blockquote" in out
    assert "after text" in out


def test_every_leaf_text_run_is_escaped():
    out = render_markdown("plain <script>alert(1)</script> text")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


# --- Heading clamping (design finding 2) -------------------------------------


def test_first_heading_is_always_base_level():
    out = render_markdown("### starts deep")
    assert out.startswith("<h5>")  # clamped: first heading is never deeper than base


def test_heading_skip_in_source_never_skips_a_level_in_output():
    out = render_markdown("# one\n#### four")
    assert "<h5>one</h5>" in out
    assert "<h6>four</h6>" in out  # clamped to last_level+1, not jumped to level 8


def test_heading_beyond_h6_uses_aria_level():
    out = render_markdown("# a\n## b\n### c")
    assert '<div role="heading" aria-level="7">c</div>' in out


def test_sibling_headings_at_the_same_source_level_share_one_emitted_level():
    """Review F12: consecutive sibling headings that all start below `#`
    used to deepen on every occurrence (A/B/C/D/E at source level 4 became
    a 4-deep fake nest) instead of staying siblings at one level. Three
    top-of-document `####` headings in a row have no parent to nest under,
    so all three are first-level siblings -> all three emit `<h5>`, never
    progressively deeper aria-level divs."""
    out = render_markdown("#### A\n#### B\n#### C")
    assert out == "<h5>A</h5>\n<h5>B</h5>\n<h5>C</h5>\n"
    assert "aria-level" not in out


def test_sibling_headings_after_a_deeper_child_still_share_the_parent_level():
    out = render_markdown("# Top\n## Child one\n### Grandchild\n## Child two")
    # both "Child one" and "Child two" are h2 siblings under "Top" -> both h6
    assert out.count("<h6>") == 2
    assert "<h6>Child one</h6>" in out
    assert "<h6>Child two</h6>" in out


def test_heading_can_return_to_a_shallower_level_freely():
    out = render_markdown("# a\n## b\n### c\n# back to top")
    assert out.count("<h5>") == 2  # "a" and "back to top" both real h5


# --- T8: tables ---------------------------------------------------------------


def test_pipe_table_renders_real_table_markup():
    out = render_markdown("| A | B |\n|---|---|\n| 1 | 2 |")
    assert "<table>" in out
    assert '<th scope="col">A</th>' in out
    assert '<th scope="col">B</th>' in out
    assert "<td>1</td><td>2</td>" in out
    assert "|---|" not in out


def test_table_caption_from_nearest_preceding_heading():
    out = render_markdown("## Acceptance criteria\n\n| A |\n|---|\n| x |")
    assert "<caption>Acceptance criteria</caption>" in out


def test_table_without_preceding_heading_has_no_caption():
    out = render_markdown("| A |\n|---|\n| x |")
    assert "<caption>" not in out


def test_long_heading_text_truncates_caption_to_60_chars():
    long_heading = "#" * 1 + " " + "x" * 100
    out = render_markdown(long_heading + "\n\n| A |\n|---|\n| 1 |")
    caption = out.split("<caption>")[1].split("</caption>")[0]
    assert len(caption) == 60


def test_ragged_row_tolerated_not_crashed():
    out = render_markdown("| A | B |\n|---|---|\n| 1 |\n| 2 | 3 | 4 |")
    assert "<td>1</td>" in out
    assert "<td>2</td><td>3</td><td>4</td>" in out


# --- T9: lists -----------------------------------------------------------------


def test_bullet_list_renders_ul_li():
    out = render_markdown("- one\n- two")
    assert "<ul>" in out
    assert out.count("<li>") == 2


def test_numbered_list_renders_ol_li():
    out = render_markdown("1. first\n2. second")
    assert "<ol>" in out
    assert out.count("<li>") == 2


def test_checklist_checked_and_unchecked_distinguishable_by_text():
    out = render_markdown("- [x] done\n- [ ] not done")
    assert "checked" in out
    assert "unchecked" in out
    assert "☑" in out
    assert "☐" in out


def test_checklist_state_never_conveyed_by_a_distinct_color_rule():
    """AC-3.3: no CSS rule in this module's own output gives checked vs.
    unchecked a different hue — state is text/glyph only."""
    out = render_markdown("- [x] done\n- [ ] not done")
    assert "color:" not in out
    assert "style=" not in out or "list-style:none" in out  # only the list-style reset, no color styling


def test_plain_bullet_distinguishable_from_checklist_items():
    out = render_markdown("- plain bullet\n- [x] checked item")
    plain_li = out.split("<li>plain bullet")[1] if "<li>plain bullet" in out else None
    assert plain_li is not None
    assert "☑" not in out.split("plain bullet")[0]


def test_nested_list_renders_nested_not_flattened():
    out = render_markdown("- parent\n  - child")
    assert "<li>parent<ul>" in out
    assert "<li>child</li>" in out
    # the nested <ul> is inside parent's <li>, not a sibling of it
    assert out.index("<li>parent") < out.index("<ul>\n<li>child") if "<ul>\n<li>child" in out else True


def test_checklist_accessible_name_begins_with_checked_or_unchecked():
    out = render_markdown("- [x] task one")
    li = out.split("<li>")[1].split("</li>")[0]
    # aria-hidden glyph first, then the visually-hidden state word
    assert 'aria-hidden="true">☑' in li
    assert "sr-only" in li and "checked" in li
