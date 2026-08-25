"""GB-T4: days-since-tag (AC-1.10, NFR-5)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard import board, gitread
from aspark_insights.gitboard.board import build_board


def _git(repo: Path, *args: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True, env=env,
    )


def _corrupt_committer_timestamp(repo: Path, ref: str = "HEAD") -> None:
    """Real git corruption, not a mock (this project's own house convention
    — never mock the seam a bug lives in): replaces `ref`'s committer
    timestamp with a non-numeric token, forcing git's own date-formatting
    machinery into the failure mode QA's demo-day reproduced (B1/B2)."""
    raw = _git(repo, "cat-file", "-p", ref).stdout
    bad = re.sub(
        r"^committer (.*) <(.*)> \d+ [+-]\d+$",
        r"committer \1 <\2> NOTATIMESTAMP +0000",
        raw, flags=re.MULTILINE,
    )
    # CI fix: newer git (2.55, CI's runner) rejects writing an object this
    # malformed via a bare `hash-object -w` (older git, e.g. 2.39 locally,
    # was more permissive); `--literally` is git's own documented escape
    # hatch for "hash any garbage into a loose object ... for reproducing
    # characteristics of corrupted objects" — exactly this use case.
    new_hash = subprocess.run(
        ["git", "hash-object", "-w", "--literally", "-t", "commit", "--stdin"],
        cwd=repo, input=bad, capture_output=True, text=True, check=True,
    ).stdout.strip()
    branch = _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip()
    _git(repo, "update-ref", f"refs/heads/{branch}", new_hash)


@pytest.fixture
def tagged_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    fixed_date = {"GIT_AUTHOR_DATE": "2026-08-01T12:00:00+00:00", "GIT_COMMITTER_DATE": "2026-08-01T12:00:00+00:00"}
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: tagged", extra_env=fixed_date)
    _git(repo, "tag", "v1.0.0")
    return repo


# --- exact day count, as_of-relative -----------------------------------------


def test_exact_day_count_between_tag_date_and_as_of(tagged_repo: Path):
    b = build_board(str(tagged_repo), "2026-08-11")  # 10 days after 2026-08-01
    assert b["days_since_tag"]["value"] == 10
    assert b["days_since_tag"]["reason"] is None


def test_zero_days_when_as_of_equals_tag_date(tagged_repo: Path):
    b = build_board(str(tagged_repo), "2026-08-01")
    assert b["days_since_tag"]["value"] == 0


# --- AC-1.10(a): absent, not a second null, when there is no tag at all -----


def test_no_tag_omits_days_since_tag_key(tmp_path: Path):
    repo = tmp_path / "notag"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    b = build_board(str(repo), "2026-08-13")
    assert "days_since_tag" not in b


# --- AC-1.10(b): null+reason when the tag's commit date can't be read ------


def test_unreadable_tag_date_is_null_with_reason(monkeypatch, tagged_repo: Path):
    monkeypatch.setattr(gitread, "tag_commit_date", lambda repo_root, tag: None)
    b = build_board(str(tagged_repo), "2026-08-13")
    assert b["days_since_tag"]["value"] is None
    assert "v1.0.0" in b["days_since_tag"]["reason"]
    assert "could not be read" in b["days_since_tag"]["reason"]


def test_real_corrupted_tag_date_nulls_the_one_figure_not_the_whole_report(tmp_path: Path):
    """QA B1 (Major): a tag whose commit has an unparseable committer
    timestamp used to crash the entire command — `git log --format=%cI`
    leaves the literal, unexpanded `%cI` token instead of substituting
    anything, which is non-empty/truthy and slipped past the `is None`
    guard, raising uncaught inside `_whole_days` and reaching only
    `build_board`'s outer catch-all (`GitUnavailableError` for the *whole*
    report). Reproduced here with a real corrupted git object, not the
    mocked short-circuit `test_unreadable_tag_date_is_null_with_reason`
    already covers — this is the actual git behavior, not a stand-in."""
    repo = tmp_path / "badtagdate"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _corrupt_committer_timestamp(repo)
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: on top")

    b = build_board(str(repo), "2026-08-13")  # must not raise
    assert b["days_since_tag"]["value"] is None
    assert "v1.0.0" in b["days_since_tag"]["reason"]
    assert "could not be read" in b["days_since_tag"]["reason"]
    assert b["commits"]["value"] == 1  # the rest of the report still succeeds


# --- NFR-5: as_of-relative, UTC-normalized, never now() ----------------------


def test_whole_days_is_utc_normalized_not_local_offset_sensitive():
    # A commit date with a +14:00 offset (Kiribati) vs a -12:00 offset — must
    # normalize to UTC before taking the calendar date, or an off-by-one at
    # day boundaries would make the figure dependent on the committer's zone.
    assert board._whole_days("2026-08-01T23:00:00+14:00", "2026-08-02") == 1  # UTC: 2026-08-01T09:00
    assert board._whole_days("2026-08-01T01:00:00-12:00", "2026-08-02") == 1  # UTC: 2026-08-01T13:00
    # A case that actually distinguishes UTC conversion from naively slicing
    # the date off the ISO string: local calendar date is 2026-08-02, but
    # the true UTC instant falls on 2026-08-01 — naive slicing would compute
    # -1 day against as_of=2026-08-01; correct UTC conversion computes 0.
    assert board._whole_days("2026-08-02T00:30:00+14:00", "2026-08-01") == 0  # UTC: 2026-08-01T10:30


def test_days_computation_reads_no_wall_clock():
    """Pure function over its two string inputs — no ambient datetime.now()
    reachable from its signature at all (ADR-4)."""
    import inspect

    sig = inspect.signature(board._whole_days)
    assert list(sig.parameters) == ["from_iso", "as_of"]
