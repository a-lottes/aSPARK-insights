"""markdownlite — a bounded, hand-written Markdown-to-HTML renderer
(release-board-docs, US-3).

Deliberately NOT a general-purpose CommonMark implementation (A3): bounded
to the constructs this project's own shipped artifacts actually use —
ATX headings, paragraphs, bold/italic, inline code, fenced code blocks,
horizontal rules, links (scheme-allowlisted), pipe tables, bullet/numbered/
checklist lists, and HTML comments (stripped). Anything outside that set
degrades to plain, visible, escaped text (AC-3.4) — never dropped, never a
crash, never a broken render of the rest of the document.

Every leaf text run flows through `render.py`'s canonical `_esc` — the same
single choke-point every other HTML surface in this project uses (NFR-2).
No dependency was chosen deliberately (plan.md §1's own rejected
alternative): every off-the-shelf Markdown library passes raw HTML through
by default, which would open a second, un-escaped path to the page.
"""

from __future__ import annotations

import re

from aspark_insights.render import _esc

_ATX_HEADING = re.compile(r"^(#{1,4})\s+(.*)$")
_FENCE = re.compile(r"^```")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
_LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(?:\[( |x|X)\]\s*)?(.*)$")
_TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_HTML_COMMENT_START = re.compile(r"^\s*<!--")

_INLINE_PATTERN = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\*\*(?P<bold>[^*]+)\*\*"
    r"|\*(?P<italic1>[^*]+)\*"
    # Review F11: a bare word-boundary requirement around the `_` markers —
    # without it, every snake_case identifier in this project's own
    # artifacts (`test_releaseboard_render`, `git_init`, ...) got its
    # middle segment wrongly italicised, corrupting identifiers in exactly
    # the documents this feature exists to make readable.
    r"|(?<!\w)_(?P<italic2>[^_]+)_(?!\w)"
    # Review F15 (Nit, confirmed not a bypass): stops `linkhref` at the
    # first `)`, so a target with its own nested parens — e.g.
    # `[t](javascript:alert(1))` — captures a truncated href and leaves a
    # stray `)` as trailing text. Deliberately not "fixed" by matching to
    # the *last* `)` instead: that would merge two separate links on one
    # line ("[a](u1) and [b](u2)") into one malformed match, a worse
    # regression than this cosmetic artifact. `_link_allowed` still
    # rejects the truncated href correctly either way (a `:` before the
    # first `/` still trips the scheme check).
    r"|\[(?P<linktext>[^\]]*)\]\((?P<linkhref>[^)]*)\)"
)

_ALLOWED_LINK_SCHEMES = ("http://", "https://", "mailto:", "#")


def _link_allowed(href: str) -> bool:
    """NFR-2's new surface: a link target this renderer will make
    clickable. `javascript:`/`data:`/any other scheme is rejected — only
    http(s), mailto, an in-page fragment, or a schemeless relative path are
    ever turned into a real `<a href>`; anything else keeps its visible
    text but drops the link itself, never silently dropped, never
    executable.

    Review F5: casefolded before the prefix test — `HTTP://`/`MAILTO:`
    were previously (safely, but wrongly) rejected as unknown schemes,
    against this function's own docstring. A leading `//` (a
    protocol-relative URL — neither http(s)/mailto/fragment nor a genuine
    relative path) is now explicitly rejected: on a `file://`-opened page
    it would resolve to whatever host the browser fills in, an
    attacker-steerable target this project's own offline/ADR-5 guarantee
    should not allow a document body to reach."""
    lowered = href.strip().lower()
    if lowered.startswith(_ALLOWED_LINK_SCHEMES):
        return True
    if lowered.startswith("//"):
        return False
    prefix = lowered.split("/", 1)[0]
    return ":" not in prefix


def _render_inline(text: str) -> str:
    """Bold/italic/inline-code/links over one line's worth of text. Every
    leaf text run — including link/emphasis content — flows through
    `_esc`; no branch ever concatenates raw source text into the output."""
    out = []
    pos = 0
    for m in _INLINE_PATTERN.finditer(text):
        out.append(_esc(text[pos:m.start()]))
        if m.group("code") is not None:
            out.append(f'<code>{_esc(m.group("code"))}</code>')
        elif m.group("bold") is not None:
            out.append(f'<strong>{_esc(m.group("bold"))}</strong>')
        elif m.group("italic1") is not None:
            out.append(f'<em>{_esc(m.group("italic1"))}</em>')
        elif m.group("italic2") is not None:
            out.append(f'<em>{_esc(m.group("italic2"))}</em>')
        else:  # link
            href = m.group("linkhref")
            link_text = m.group("linktext")
            if _link_allowed(href):
                out.append(f'<a href="{_esc(href)}">{_esc(link_text)}</a>')
            else:
                out.append(_esc(link_text))
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


def _render_heading(level: int, text: str) -> str:
    """Plan §1's clamped mapping: level 5/6 are real `<h5>`/`<h6>` (native
    HTML has no room below h6 given the page's own shipped h1-h4); level
    7/8 use `role="heading" aria-level="N"` (design finding 2)."""
    inline = _render_inline(text)
    if level <= 6:
        return f"<h{level}>{inline}</h{level}>\n"
    return f'<div role="heading" aria-level="{level}">{inline}</div>\n'


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip() for c in stripped.split("|")]


def _render_table(table_lines: list[str], caption_source: str | None) -> str:
    """T8/AC-3.2: real `<table>`/`<th scope="col">`, never raw pipe text.
    Caption sourced from the nearest preceding heading, 60-char truncated
    (B2's clipping lesson); omitted when there is none. Ragged rows (too
    few/many cells) are tolerated as-is — every cell present is shown,
    nothing crashes on a short or long row."""
    header_cells = _split_table_row(table_lines[0])
    body_rows = [_split_table_row(line) for line in table_lines[2:]]
    caption_html = ""
    if caption_source:
        caption_text = caption_source[:60]
        caption_html = f"<caption>{_esc(caption_text)}</caption>\n"
    thead = (
        "<thead><tr>"
        + "".join(f'<th scope="col">{_render_inline(c)}</th>' for c in header_cells)
        + "</tr></thead>\n"
    )
    body_html = "".join(
        "<tr>" + "".join(f"<td>{_render_inline(c)}</td>" for c in row) + "</tr>\n"
        for row in body_rows
    )
    return (
        '<div class="table-wrap">\n<table>\n'
        f"{caption_html}{thead}"
        f"<tbody>\n{body_html}</tbody>\n"
        "</table>\n</div>\n"
    )


def _build_nested_list(items: list[tuple[int, str, str, bool | None]]) -> str:
    """items: `(indent_len, kind['ul'|'ol'|'check'], text, checked)`.
    Builds a real nested `<ul>`/`<ol>` structure from flat indent-tagged
    lines (T9: "nested lists render nested, not flattened")."""

    def render(items, index, indent):
        html = []
        list_tag = None
        while index < len(items):
            item_indent, kind, text, checked = items[index]
            if item_indent < indent:
                break
            if list_tag is None:
                list_tag = "ol" if kind == "ol" else "ul"
                style = ' style="list-style:none"' if kind == "check" else ""
                html.append(f"<{list_tag}{style}>\n")
            child_html = ""
            if index + 1 < len(items) and items[index + 1][0] > indent:
                child_html, index = render(items, index + 1, items[index + 1][0])
            else:
                index += 1
            if kind == "check":
                # T9/AC-3.3: state is text/glyph, never color alone — a
                # visually-hidden word carries it to assistive tech too.
                glyph = "☑" if checked else "☐"
                state_word = "checked" if checked else "unchecked"
                html.append(
                    f'<li><span aria-hidden="true">{glyph}</span> '
                    f'<span class="sr-only">{state_word}:</span> {_render_inline(text)}{child_html}</li>\n'
                )
            else:
                html.append(f"<li>{_render_inline(text)}{child_html}</li>\n")
        if list_tag:
            html.append(f"</{list_tag}>\n")
        return "".join(html), index

    if not items:
        return ""
    result, _ = render(items, 0, items[0][0])
    return result


def render_markdown(text: str, *, base_level: int = 5) -> str:
    """Pure — Markdown `str` in, HTML `str` out, bounded to A3's construct
    set. `base_level` is the heading level a top-level `#` maps to (5 by
    default: the page's own shipped hierarchy already runs h1-h4)."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    # Review F12: a stack of (source_level, emitted_level) — the standard
    # outline algorithm. Popping every entry whose source level is >= the
    # new heading's own means consecutive *sibling* headings (same source
    # level) reuse the same emitted level instead of deepening on every
    # occurrence; pushing one level past the current top is what still
    # guarantees a skip in the source can never produce a skip on the page.
    heading_stack: list[tuple[int, int]] = []
    last_heading_text: str | None = None
    paragraph_buf: list[str] = []

    def flush_paragraph():
        nonlocal paragraph_buf
        if paragraph_buf:
            out.append(f"<p>{_render_inline(' '.join(paragraph_buf))}</p>\n")
            paragraph_buf = []

    while i < n:
        line = lines[i]

        if _HTML_COMMENT_START.match(line):
            # Review F4: find the real closing '-->' before committing to
            # comment-consumption mode — the previous version scanned to
            # EOF looking for it and, if never found, silently discarded
            # every remaining line (AC-3.4 forbids exactly that). An
            # unterminated comment instead falls through to plain text.
            end_i = end_col = None
            for j in range(i, n):
                idx = lines[j].find("-->")
                if idx != -1:
                    end_i, end_col = j, idx
                    break
            if end_i is None:
                paragraph_buf.append(line.strip())
                i += 1
                continue
            flush_paragraph()
            remainder = lines[end_i][end_col + 3:]
            if remainder.strip():
                paragraph_buf.append(remainder.strip())
            i = end_i + 1
            continue

        if _FENCE.match(line):
            flush_paragraph()
            code_lines = []
            i += 1
            while i < n and not _FENCE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{_esc(chr(10).join(code_lines))}</code></pre>\n")
            continue

        m = _ATX_HEADING.match(line)
        if m:
            flush_paragraph()
            source_level = len(m.group(1))
            heading_text = m.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= source_level:
                heading_stack.pop()
            emitted_level = heading_stack[-1][1] + 1 if heading_stack else base_level
            heading_stack.append((source_level, emitted_level))
            last_heading_text = heading_text
            out.append(_render_heading(emitted_level, heading_text))
            i += 1
            continue

        if _HR.match(line):
            flush_paragraph()
            out.append("<hr>\n")
            i += 1
            continue

        if _TABLE_ROW.match(line) and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            flush_paragraph()
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < n and _TABLE_ROW.match(lines[i]):
                table_lines.append(lines[i])
                i += 1
            out.append(_render_table(table_lines, last_heading_text))
            continue

        m = _LIST_ITEM.match(line)
        if m:
            flush_paragraph()
            items = []
            while i < n:
                lm = _LIST_ITEM.match(lines[i])
                if not lm:
                    break
                indent = len(lm.group(1))
                marker = lm.group(2)
                checkbox = lm.group(3)
                item_text = lm.group(4)
                if checkbox is not None:
                    kind, checked = "check", checkbox.lower() == "x"
                elif marker in ("-", "*"):
                    kind, checked = "ul", None
                else:
                    kind, checked = "ol", None
                items.append((indent, kind, item_text, checked))
                i += 1
            out.append(_build_nested_list(items))
            continue

        if line.strip() == "":
            flush_paragraph()
            i += 1
            continue

        # A3/AC-3.4: any unrecognized construct (blockquotes, reference
        # links, raw HTML tables, ...) simply falls through to here and
        # becomes plain paragraph text, escaped — never dropped, never a
        # crash, never a broken render of the rest of the document.
        paragraph_buf.append(line.strip())
        i += 1

    flush_paragraph()
    return "".join(out)
