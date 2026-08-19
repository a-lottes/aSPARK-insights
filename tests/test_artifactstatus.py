"""RB-T6: per-artifact header-table status (first pipe-table block only)
(AC-2.1, AC-2.2, AC-2.3, AC-2.4, NFR-2, NFR-5)."""

from __future__ import annotations

from pathlib import Path

from aspark_insights.gitboard.artifactstatus import read_artifact_status


# --- AC-2.1: present Status/Date extracted verbatim -------------------------


def test_present_status_and_date_extracted_verbatim(tmp_path: Path):
    f = tmp_path / "spec.md"
    f.write_text(
        "# Spec: example\n"
        "\n"
        "| | |\n"
        "|---|---|\n"
        "| **Phase** | Specify |\n"
        "| **Status** | `approved` |\n"
        "| **Date** | 2026-08-19 |\n"
        "\n"
        "## 1. Problem\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    assert result == {"status": "`approved`", "date": "2026-08-19", "reason": None}


def test_status_cell_with_trailing_prose_is_carried_verbatim(tmp_path: Path):
    """A real, observed shape in this project's own artifacts
    (git-native-mid-cycle-board/qa.md): the Status cell carries explanatory
    prose beyond a clean token. AC-2.1 says verbatim — the whole cell, not
    a truncated or reinterpreted value."""
    f = tmp_path / "qa.md"
    f.write_text(
        "# QA Report: example\n"
        "\n"
        "| | |\n"
        "|---|---|\n"
        "| **Status** | `passed` — independent re-test, every one held up |\n"
        "| **Date** | 2026-08-19 |\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    assert result["status"] == "`passed` — independent re-test, every one held up"
    assert result["reason"] is None


def test_status_cell_containing_a_literal_pipe_is_rejoined_verbatim_not_truncated(tmp_path: Path):
    """F2 (review, Minor): a value cell containing a literal `|` used to
    split into more raw cells than expected and silently truncate at the
    first embedded pipe. Must be rejoined exactly, whitespace included."""
    f = tmp_path / "release.md"
    f.write_text(
        "# Release: example\n"
        "\n"
        "| | |\n"
        "|---|---|\n"
        "| **Status** | `preparing` (see A | B for details) |\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    assert result["status"] == "`preparing` (see A | B for details)"
    assert result["reason"] is None


# --- AC-2.2: missing file -> null + "file not found", never omitted --------


def test_missing_file_is_null_with_file_not_found_reason(tmp_path: Path):
    result = read_artifact_status(tmp_path / "does-not-exist.md")
    assert result == {"status": None, "date": None, "reason": "file not found"}


# --- AC-2.3: malformed/absent-Status/bad-encoding -> null + specific reason -


def test_no_pipe_table_at_all_is_null_with_specific_reason(tmp_path: Path):
    f = tmp_path / "no_table.md"
    f.write_text("# Just a heading\n\nSome prose, no table anywhere.\n", encoding="utf-8")
    result = read_artifact_status(f)
    assert result["status"] is None
    assert result["reason"] == "no header table found"


def test_table_present_but_no_status_row_is_null_with_specific_reason(tmp_path: Path):
    f = tmp_path / "no_status_row.md"
    f.write_text(
        "# Spec: example\n"
        "\n"
        "| | |\n"
        "|---|---|\n"
        "| **Phase** | Specify |\n"
        "| **Owner** | Someone |\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    assert result["status"] is None
    assert result["reason"] == "no Status row found in header table"


def test_bad_encoding_is_null_with_specific_reason(tmp_path: Path):
    f = tmp_path / "bad_encoding.md"
    f.write_bytes(b"| **Status** | \xff\xfe invalid utf-8 |\n")
    result = read_artifact_status(f)
    assert result["status"] is None
    assert "could not read file" in result["reason"]


def test_status_field_nested_under_a_heading_not_a_pipe_row_is_honest_null(tmp_path: Path):
    """A synthetic drift shape: Status expressed as a heading rather than a
    table row (never actually a `|`-leading line) — must degrade honestly,
    never be guessed at from prose."""
    f = tmp_path / "drifted.md"
    f.write_text(
        "# Release: example\n"
        "\n"
        "### Status: preparing\n"
        "\n"
        "Some narrative text.\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    assert result["status"] is None
    assert result["reason"] == "no header table found"


# --- AC-2.4: only the first pipe-table block is read, nothing else ---------


def test_a_second_pipe_table_later_in_the_file_is_never_read(tmp_path: Path):
    f = tmp_path / "two_tables.md"
    f.write_text(
        "# Spec: example\n"
        "\n"
        "| | |\n"
        "|---|---|\n"
        "| **Phase** | Specify |\n"
        "\n"
        "## Some section\n"
        "\n"
        "| **Status** | `this must never be read` |\n",
        encoding="utf-8",
    )
    result = read_artifact_status(f)
    # the first (only real header) table has no Status row -> honest null,
    # even though a later, unrelated table happens to contain that literal cell
    assert result["status"] is None
    assert result["reason"] == "no Status row found in header table"


# --- NFR-5: bounded read, even when no table is ever found -----------------


def test_a_pathologically_large_file_with_no_table_does_not_hang_or_read_it_all(tmp_path: Path):
    f = tmp_path / "huge.md"
    with f.open("w", encoding="utf-8") as fh:
        for _ in range(50_000):
            fh.write("just an ordinary line, no pipe table anywhere in this file\n")
    result = read_artifact_status(f)
    assert result["status"] is None
    assert result["reason"] == "no header table found"


# --- Real-file integration: every real artifact in this repo parses clean --


def test_every_real_artifact_in_this_repo_parses_without_error():
    """Not a hypothetical — runs against this repo's own real `.spark/`
    artifacts across all cycles, confirming the parser survives the real
    format (and the real drift in prose Status cells) rather than only
    synthetic fixtures."""
    repo_root = Path(__file__).resolve().parents[1]
    spark_dir = repo_root / ".spark"
    checked = 0
    for feature_dir in spark_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        for artifact in ("spec", "plan", "review", "qa", "release"):
            path = feature_dir / f"{artifact}.md"
            if not path.is_file():
                continue
            result = read_artifact_status(path)  # must not raise
            assert set(result.keys()) == {"status", "date", "reason"}
            checked += 1
    assert checked > 20  # sanity: this repo really does have this many real artifacts
