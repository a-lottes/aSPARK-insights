"""GB-T2: hostile --repo + git-invocation rigor (AC-1.4, NFR-2).

The full hostile-input checklist this project applies to every argument that
becomes a filesystem path or a subprocess argument (CLAUDE.md's own
"hostile-input checklist at /increment time" nudge).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import InsightsError, NotAGitRepoError
from aspark_insights.gitboard.board import build_board


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=repo,
    )


@pytest.fixture
def corrupt_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "corrupt"
    repo.mkdir()
    (repo / ".git").write_text("not a real git directory\n", encoding="utf-8")
    return repo


# --- AC-1.4: five hostile forms, table-driven --------------------------------


def test_empty_repo_string_rejected_before_any_git_call():
    with pytest.raises(NotAGitRepoError):
        build_board("", "2026-08-13")


def test_path_traversal_repo_is_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13", "--repo", "../../../../../../etc")
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


def test_absolute_nonexistent_path_is_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13", "--repo", "/nonexistent-path-xyz-abc")
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


def test_non_git_directory_is_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13", "--repo", str(tmp_path))
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


def test_corrupt_dot_git_is_named_error_not_a_traceback(corrupt_git_repo: Path):
    result = _run_cli(corrupt_git_repo.parent, "board", "--as-of", "2026-08-13", "--repo", str(corrupt_git_repo))
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("hostile_repo", [
    "",
    "../../../../../../etc",
    "/nonexistent-path-xyz-abc",
])
def test_every_hostile_form_exits_1_with_named_error(tmp_path: Path, hostile_repo: str):
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13", "--repo", hostile_repo)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert '"error"' in result.stderr


# --- NFR-2: fixed argument vector, never a shell string ----------------------


def test_gitread_never_uses_shell_true():
    """A hostile --repo value could otherwise smuggle shell metacharacters
    into the invocation — checked against the actual source, not inferred
    from behavior."""
    src = Path("src/aspark_insights/gitboard/gitread.py").read_text(encoding="utf-8")
    assert "shell=True" not in src
    assert "shell = True" not in src


def test_hostile_repo_value_with_shell_metacharacters_never_executes_them(tmp_path: Path):
    """A `--repo` value containing shell metacharacters must be treated as an
    inert path string, never interpreted — proves the fixed-vector claim
    behaviorally, not just by source inspection."""
    marker = tmp_path / "should-not-exist"
    hostile = f"; touch {marker} #"
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13", "--repo", hostile)
    assert result.returncode == 1
    assert not marker.exists()


# --- TimeoutExpired -> GitUnavailableError (not a raw exception) -------------


def test_git_timeout_maps_to_named_error(tmp_path: Path, monkeypatch):
    import subprocess as sp

    def _timeout(*args, **kwargs):
        raise sp.TimeoutExpired(cmd=args, timeout=10)

    monkeypatch.setattr(sp, "run", _timeout)
    from aspark_insights.errors import GitUnavailableError

    with pytest.raises(GitUnavailableError):
        build_board(str(tmp_path), "2026-08-13")


# --- F3 (review): an exit-0 git call whose output doesn't parse as expected
#     (e.g. a non-integer rev-list count) must map to a named error too,
#     never escape main()'s InsightsError-only catch as a raw traceback -----


def test_unparseable_git_output_maps_to_named_error_not_a_traceback(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test",
         "commit", "--allow-empty", "-q", "-m", "feat: base"],
        cwd=repo, check=True,
    )
    subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)

    from aspark_insights.gitboard import gitread
    monkeypatch.setattr(gitread, "count_commits_since", lambda *a, **k: int("not-a-number"))

    from aspark_insights.errors import GitUnavailableError

    with pytest.raises(GitUnavailableError):
        build_board(str(repo), "2026-08-13")
