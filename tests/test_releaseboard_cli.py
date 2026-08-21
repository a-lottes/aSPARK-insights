"""RBH-T1/T9: `insights releases --format html` end to end against a real
git repo — never mocked (this project's own sibling-integration precedent).
NFR-1: `--format json`'s existing byte-for-byte stdout is unchanged."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=repo,
    )


@pytest.fixture
def tagged_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "tagged"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: first")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "fix: second")
    return repo


def test_format_html_writes_file_and_reports_path(tagged_repo: Path):
    result = _run_cli(tagged_repo, "releases", "--as-of", "2026-08-20", "--format", "html")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    report_path = Path(data["report"])
    assert report_path.is_file()
    text = report_path.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>")
    assert "v1.0.0" in text


def test_format_json_stdout_byte_unchanged_by_html_addition(tagged_repo: Path):
    from aspark_insights.gitboard.releasemap import build_release_map
    from aspark_insights.serialization import canonical_json

    result = _run_cli(tagged_repo, "releases", "--as-of", "2026-08-20", "--format", "json")
    assert result.returncode == 0, result.stderr
    expected = canonical_json(build_release_map(str(tagged_repo), "2026-08-20"))
    assert result.stdout == expected


def test_output_flag_redirects_write_location(tagged_repo: Path, tmp_path: Path):
    out_dir = tmp_path / "elsewhere"
    out_dir.mkdir()
    result = _run_cli(
        tagged_repo, "releases", "--as-of", "2026-08-20", "--format", "html", "--output", str(out_dir),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert str(out_dir) in data["report"]
    assert (out_dir / ".aspark-insights" / "release-board.html").is_file()


def test_releases_help_documents_html_format_and_output(tmp_path: Path):
    result = _run_cli(tmp_path, "releases", "--help")
    assert result.returncode == 0
    assert "html" in result.stdout
    assert "--output" in result.stdout


# --- T9: hostile-input checklist on --repo, html format path ----------------


def test_non_git_repo_with_format_html_is_a_clean_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "releases", "--as-of", "2026-08-20", "--format", "html")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["error"] == "not_a_git_repo"
    assert result.stdout == ""


def test_path_traversal_repo_with_format_html_is_a_clean_named_error(tagged_repo: Path):
    result = _run_cli(
        tagged_repo, "releases", "--as-of", "2026-08-20", "--format", "html",
        "--repo", "../../../../../../etc",
    )
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["error"] in ("not_a_git_repo", "git_unavailable")


def test_output_pointing_at_a_file_is_a_clean_named_error_not_a_traceback(tagged_repo: Path, tmp_path: Path):
    """Review F1 (Blocker): `mkdir`/`write_text` used to sit outside the
    render function's own try/except, so a hostile `--output` (an existing
    file, not a directory) dumped a raw `NotADirectoryError` traceback."""
    blocker_file = tmp_path / "not-a-directory"
    blocker_file.write_text("x", encoding="utf-8")
    result = _run_cli(
        tagged_repo, "releases", "--as-of", "2026-08-20", "--format", "html",
        "--output", str(blocker_file),
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    data = json.loads(result.stderr)
    assert data["error"] == "report_unwritable"
    assert result.stdout == ""


# --- Review F3: AC-2.3's real-data claim, verified against this actual repo -


def test_real_repo_v070_has_exactly_one_member_git_native_mid_cycle_board():
    """AC-2.3 (corrected per review F3): `v0.7.0`'s real single member is
    `git-native-mid-cycle-board` — verified here against this repo itself,
    not a synthetic fixture, so a future rename/re-tag that breaks the
    spec's own illustrative claim is caught the same way F3 was."""
    from aspark_insights.gitboard.releasemap import build_release_map

    repo_root = Path(__file__).resolve().parent.parent
    data = build_release_map(str(repo_root), "2026-08-20")
    v070 = next(r for r in data["releases"] if r["tag"] == "v0.7.0")
    assert [m["name"] for m in v070["members"]] == ["git-native-mid-cycle-board"]
