"""RM-T5: the two-anchor separation (A4) — document de-duplication anchors
to a feature's newest occurrence (release-board-docs, unchanged), scope
delivery anchors to its oldest (release-metrics, new). AC-2.5, AC-2.6,
AC-2.7."""

from __future__ import annotations

from aspark_insights.gitboard.releasemap import _build_figures
from aspark_insights.gitboard.releaseboard_report import (
    _document_plan,
    _display_order,
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


def _doc(text="content") -> dict:
    return {
        "text": text, "reason": None, "empty": False, "truncated": False,
        "byte_truncated": False, "line_truncated": False,
        "total_lines": 1, "shown_lines": 1, "total_bytes": len(text.encode("utf-8")),
    }


def _full_docs(text="content") -> dict:
    return {a: _doc(text) for a in ("spec", "plan", "review", "qa", "release")}


# --- AC-2.5: both anchors hold simultaneously ---------------------------------


def test_document_homes_newest_but_delivers_oldest_simultaneously():
    """The core two-anchor pin: a feature appearing in v1.0.0 (delivering)
    and v2.0.0 (trailing) must show its FULL document under v2.0.0 (newest
    — A4's unchanged document rule) while its `delivery.delivering` flag
    sits on v1.0.0 (oldest — A3, this feature's new rule)."""
    older = _release(
        "v1.0.0",
        members=[_member("feature-x", delivery=_delivery(delivering=True))],
    )
    newer = _release(
        "v2.0.0",
        members=[_member("feature-x", delivery=_delivery(delivering=False, delivered_in="v1.0.0"))],
    )
    documents = {"feature-x": _full_docs("current spec content")}
    text = render_release_board_html(_data([older, newer]), documents)

    older_block = text.split('id="rel-0"')[1].split("</article>")[0]
    newer_block = text.split('id="rel-1"')[1].split("</article>")[0]

    # document anchor: newest (v2.0.0) embeds the full content...
    assert "current spec content" in newer_block
    # ...while the older (v1.0.0) occurrence only links forward to it.
    assert "current spec content" not in older_block
    assert "Documents shown under" in older_block
    assert "v2.0.0" in older_block

    # delivery anchor: oldest (v1.0.0) is delivering, newest (v2.0.0) trailing.
    assert "Delivering" in older_block
    assert "Trailing" in newer_block
    assert "v1.0.0" in newer_block  # trailing note names the actual delivery release


def test_document_plan_structure_unchanged_by_delivery_attribution():
    """Structural pin: `_document_plan`'s own result shape (`home_index`,
    `home_anchor`, `embedded`, `k`) is computed purely from `members`/
    `documents`/display order — the new `delivery`/`scope` member keys
    must not perturb it."""
    older = _release("v1.0.0", members=[_member("feature-x")])
    newer = _release("v2.0.0", members=[_member("feature-x")])
    releases = [older, newer]
    order = _display_order(releases)
    plan = _document_plan(order, {"feature-x": _full_docs()}, 2_500_000)
    assert plan["feature-x"]["home_index"] == 1  # newest occurrence, index of v2.0.0
    assert plan["feature-x"]["embedded"] is True
    assert set(plan["feature-x"].keys()) == {"home_index", "home_anchor", "embedded", "k"}


# --- AC-2.6: empty delivering set states it in words ---------------------------


def test_empty_delivering_set_states_it_in_words_exact_wording():
    trailing = _member("feature-y", delivery=_delivery(delivering=False, delivered_in="v0.5.0"))
    r = _release("v0.6.0", members=[trailing], delivered_scope=_delivered_scope(us=0, acs=0, n=0))
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "no feature was delivered in this release" in detail


def test_empty_delivering_set_wording_coexists_with_no_members_at_all():
    """AC-2.6's statement ("no feature was delivered in this release") is
    truthful whenever the delivering set is empty, including the trivial
    case of zero members total — it renders alongside, not instead of,
    the pre-existing "no members" notice, so neither text is ever lost."""
    empty_members_release = _release("v1.0.0", members=[])
    text = render_release_board_html(_data([empty_members_release]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "No member features attributed to this release." in detail
    assert "no feature was delivered in this release" in detail


def test_nonempty_delivering_set_names_the_delivering_features():
    r = _release("v1.0.0", members=[_member("feature-a", delivery=_delivery(delivering=True))])
    text = render_release_board_html(_data([r]))
    detail = text.split('id="rel-0"')[1].split("</article>")[0]
    assert "no feature was delivered in this release" not in detail
    assert "feature-a" in detail


# --- AC-2.7: trailing note in all three document-viewing states ----------------


def test_trailing_note_present_when_document_is_embedded():
    older = _release("v1.0.0", members=[_member("feature-x", delivery=_delivery(delivering=True))])
    newer = _release("v2.0.0", members=[_member("feature-x", delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    text = render_release_board_html(_data([older, newer]), {"feature-x": _full_docs()})
    newer_block = text.split('id="rel-1"')[1].split("</article>")[0]
    assert "Trailing member" in newer_block
    assert "delivered in" in newer_block
    assert "v1.0.0" in newer_block
    assert "document shown as currently written" in newer_block


def test_trailing_note_present_when_document_is_linked_elsewhere():
    """A feature appearing in three releases: delivering at v1.0.0,
    trailing at both v2.0.0 (its document home, newest) and v3.0.0 — wait,
    only the newest is ever "home"; the middle occurrence (v2.0.0 here is
    not newest once v3.0.0 exists) links elsewhere. Construct that middle,
    non-home, trailing occurrence explicitly and confirm its trailing note
    still renders beside the link, not just beside the embedded copy."""
    v1 = _release("v1.0.0", members=[_member("feature-x", delivery=_delivery(delivering=True))])
    v2 = _release("v2.0.0", members=[_member("feature-x", delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    v3 = _release("v3.0.0", members=[_member("feature-x", delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    text = render_release_board_html(_data([v1, v2, v3]), {"feature-x": _full_docs()})
    v2_block = text.split('id="rel-1"')[1].split("</article>")[0]
    assert "Documents shown under" in v2_block  # non-home: links to v3.0.0
    assert "Trailing member" in v2_block
    assert "delivered in" in v2_block
    assert "v1.0.0" in v2_block


def test_trailing_note_present_when_over_page_budget():
    older = _release("v1.0.0", members=[_member("feature-x", delivery=_delivery(delivering=True))])
    newer = _release("v2.0.0", members=[_member("feature-x", delivery=_delivery(delivering=False, delivered_in="v1.0.0"))])
    huge_docs = {"feature-x": _full_docs("x" * 3_000_000)}  # exceeds the 2.5MB page budget alone
    text = render_release_board_html(_data([older, newer]), huge_docs)
    newer_block = text.split('id="rel-1"')[1].split("</article>")[0]
    assert "Not embedded in this page" in newer_block
    assert "Trailing member" in newer_block
    assert "v1.0.0" in newer_block
