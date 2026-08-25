"""RM-T3: scopecount — a feature's own delivered scope, from its own
spec.md, never the graph (US-2/A1, AC-3.6)."""

from __future__ import annotations

from pathlib import Path

from aspark_insights.gitboard.scopecount import read_scope_counts

# CI B1: these three tests below were hardcoded to a local machine's absolute
# path and failed everywhere else (CI included) with a spurious "spec.md
# missing" — every other real-repo test in this project derives its root
# from `__file__` (see `tests/test_releasemap_figures.py`'s own `_REPO_ROOT`);
# this file simply forgot to.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_missing_spec_is_null_with_reason(tmp_path: Path):
    result = read_scope_counts(tmp_path / "no-such-spec.md")
    assert result == {"us": None, "acs": None, "reason": "spec.md missing"}


def test_unreadable_spec_is_null_with_reason(tmp_path: Path):
    bad = tmp_path / "spec.md"
    bad.write_bytes(b"\xff\xfe\x00not-utf8")
    result = read_scope_counts(bad)
    assert result["us"] is None
    assert result["acs"] is None
    assert "could not decode" in result["reason"]


def test_no_us_heading_is_null_with_reason(tmp_path: Path):
    spec = tmp_path / "spec.md"
    spec.write_text("# just a title\n\nno stories here.\n", encoding="utf-8")
    result = read_scope_counts(spec)
    assert result == {"us": None, "acs": None, "reason": "no US heading found"}


def test_us_heading_in_prose_or_wrong_level_is_not_counted(tmp_path: Path):
    spec = tmp_path / "spec.md"
    spec.write_text(
        "# spec\n\n"
        "See US-3 for details.\n\n"
        "#### US-9 (wrong heading level)\n\n"
        "### US-1 real story\n\n"
        "- [ ] AC-1.1 real ac\n",
        encoding="utf-8",
    )
    result = read_scope_counts(spec)
    assert result == {"us": 1, "acs": 1, "reason": None}


def test_spec_with_stories_but_zero_ac_lines_is_a_real_zero_not_null(tmp_path: Path):
    spec = tmp_path / "spec.md"
    spec.write_text("### US-1 a story\n\nno checkboxes below.\n", encoding="utf-8")
    result = read_scope_counts(spec)
    assert result == {"us": 1, "acs": 0, "reason": None}


def test_checked_and_unchecked_ac_lines_both_count(tmp_path: Path):
    spec = tmp_path / "spec.md"
    spec.write_text(
        "### US-1 a story\n\n"
        "- [ ] AC-1.1 unchecked\n"
        "- [x] AC-1.2 checked\n"
        "- [X] AC-1.3 checked upper\n",
        encoding="utf-8",
    )
    result = read_scope_counts(spec)
    assert result == {"us": 1, "acs": 3, "reason": None}


def test_never_raises_on_a_directory_path(tmp_path: Path):
    result = read_scope_counts(tmp_path)
    assert result["us"] is None
    assert result["reason"] is not None


# --- against this repo's own real specs (T3 DoD, independently re-verified) -


def test_real_spec_release_board_html():
    result = read_scope_counts(_REPO_ROOT / ".spark/release-board-html/spec.md")
    assert result == {"us": 3, "acs": 13, "reason": None}


def test_real_spec_combined_v0_3_0_features():
    mcp = read_scope_counts(_REPO_ROOT / ".spark/mcp-server/spec.md")
    polish = read_scope_counts(_REPO_ROOT / ".spark/public-repo-polish/spec.md")
    assert (mcp["us"] + polish["us"], mcp["acs"] + polish["acs"]) == (7, 24)


def test_real_spec_measurement_honesty():
    result = read_scope_counts(_REPO_ROOT / ".spark/measurement-honesty/spec.md")
    assert result == {"us": 6, "acs": 33, "reason": None}


# --- review F3: a file past the line bound refuses, never a truncated guess -


def test_file_past_line_bound_returns_null_with_reason_not_a_truncated_count(tmp_path: Path):
    spec = tmp_path / "spec.md"
    lines = ["### US-1 a story\n"] + ["- [ ] AC-1.%d an ac\n" % i for i in range(5010)]
    spec.write_text("".join(lines), encoding="utf-8")
    result = read_scope_counts(spec)
    assert result["us"] is None
    assert result["acs"] is None
    assert "5000" in result["reason"]
    assert "exceeds" in result["reason"]


def test_file_exactly_at_line_bound_is_still_counted_normally(tmp_path: Path):
    spec = tmp_path / "spec.md"
    lines = ["### US-1 a story\n"] + ["- [ ] AC-1.1 an ac\n"] * 4999
    assert len(lines) == 5000
    spec.write_text("".join(lines), encoding="utf-8")
    result = read_scope_counts(spec)
    assert result == {"us": 1, "acs": 4999, "reason": None}
