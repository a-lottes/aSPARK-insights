"""RB-T7: hostile-input security matrix (AC-1.5, NFR-2).

The full hostile-input checklist this project applies to every argument
that becomes a filesystem path or a subprocess argument (CLAUDE.md's own
"hostile-input checklist at /increment time" nudge), applied to the new
`releasemap`/`artifactstatus` seam.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import NotAGitRepoError
from aspark_insights.gitboard.releasemap import build_release_map


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
def corrupt_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "corrupt"
    repo.mkdir()
    (repo / ".git").write_text("not a real git directory\n", encoding="utf-8")
    return repo


# --- AC-1.5: five hostile --repo forms, table-driven -------------------------


def test_empty_repo_string_rejected_before_any_git_call():
    with pytest.raises(NotAGitRepoError):
        build_release_map("", "2026-08-19")


@pytest.mark.parametrize("hostile_repo", [
    "",
    "../../../../../../etc",
    "/nonexistent-path-xyz-abc",
])
def test_every_hostile_form_exits_1_with_named_error_no_traceback(tmp_path: Path, hostile_repo: str):
    result = _run_cli(tmp_path, "releases", "--as-of", "2026-08-19", "--repo", hostile_repo)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert '"error"' in result.stderr
    assert "not_a_git_repo" in result.stderr


def test_non_git_directory_is_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "releases", "--as-of", "2026-08-19", "--repo", str(tmp_path))
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


def test_corrupt_dot_git_is_named_error_not_a_traceback(corrupt_git_repo: Path):
    result = _run_cli(corrupt_git_repo.parent, "releases", "--as-of", "2026-08-19", "--repo", str(corrupt_git_repo))
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


def test_hostile_repo_value_with_shell_metacharacters_never_executes_them(tmp_path: Path):
    """Proves the fixed-vector claim behaviorally, not just by source
    inspection — a `--repo` value containing shell metacharacters must be
    treated as an inert path string, never interpreted."""
    marker = tmp_path / "should-not-exist"
    hostile = f"; touch {marker} #"
    result = _run_cli(tmp_path, "releases", "--as-of", "2026-08-19", "--repo", hostile)
    assert result.returncode == 1
    assert not marker.exists()


# --- NFR-2: every new git call is a fixed vector, never a shell string -----


def test_gitread_and_releasemap_never_use_shell_true():
    for module in ("gitread.py", "releasemap.py", "artifactstatus.py"):
        src = Path(f"src/aspark_insights/gitboard/{module}").read_text(encoding="utf-8")
        assert "shell=True" not in src
        assert "shell = True" not in src


# --- A malicious .spark/ entry never escapes attribution or the repo root --


def test_malicious_spark_entry_never_reaches_a_git_pathspec_or_escapes_root(tmp_path: Path):
    """A `.spark/` entry shaped like a traversal segment, a leading-dash
    flag, or a symlink escaping the repo is excluded before it can ever
    become part of a `git log -- <pathspec>` call or a filesystem read
    outside `.spark/`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")

    spark = repo / ".spark"
    spark.mkdir()
    (spark / "-rf").mkdir()
    (spark / "..evil").mkdir()
    outside = tmp_path / "outside-secret"
    outside.mkdir()
    (outside / "sensitive.md").write_text("do not read", encoding="utf-8")
    (spark / "escape-link").symlink_to(outside, target_is_directory=True)
    (spark / "real-feature").mkdir()
    (spark / "real-feature" / "spec.md").write_text(
        "| | |\n|---|---|\n| **Status** | `approved` |\n", encoding="utf-8",
    )
    _git(repo, "add", ".spark/real-feature/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: real-feature spec")
    _git(repo, "tag", "v2.0.0")

    result = build_release_map(str(repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    names = [m["name"] for m in v2["members"]]
    assert "-rf" not in names
    assert "..evil" not in names
    assert "escape-link" not in names
    assert "real-feature" in names

    # the escape-link's target must never be read or leaked into any output
    import json

    blob = json.dumps(result)
    assert "sensitive" not in blob
    assert "do not read" not in blob


def test_git_timeout_maps_to_named_error(tmp_path: Path, monkeypatch):
    import subprocess as sp

    def _timeout(*args, **kwargs):
        raise sp.TimeoutExpired(cmd=args, timeout=10)

    monkeypatch.setattr(sp, "run", _timeout)
    from aspark_insights.errors import GitUnavailableError

    with pytest.raises(GitUnavailableError):
        build_release_map(str(tmp_path), "2026-08-19")


# --- F1 (review, Blocker): an unreadable .spark/ must never raw-traceback --


def test_unreadable_spark_directory_is_a_named_error_not_a_traceback(tmp_path: Path):
    """Reproduces the reviewer's exact repro: `.spark/` exists but the
    process can't list it (a real filesystem permission error, not a mock) —
    must exit 1 with a named error, never a raw `PermissionError` traceback
    (constitution §6)."""
    import os

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    spark = repo / ".spark"
    spark.mkdir()
    (spark / "some-feature").mkdir()
    os.chmod(spark, 0o000)
    try:
        result = _run_cli(repo, "releases", "--as-of", "2026-08-19")
    finally:
        os.chmod(spark, 0o755)  # restore so tmp_path cleanup can remove it

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert '"error": "spark_dir_unreadable"' in result.stderr


def test_unreadable_spark_directory_raises_named_error_at_the_python_level(tmp_path: Path):
    import os

    from aspark_insights.errors import SparkDirUnreadableError

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    spark = repo / ".spark"
    spark.mkdir()
    (spark / "some-feature").mkdir()
    os.chmod(spark, 0o000)
    try:
        with pytest.raises(SparkDirUnreadableError):
            build_release_map(str(repo), "2026-08-19")
    finally:
        os.chmod(spark, 0o755)


def test_no_execute_spark_directory_is_also_a_named_error(tmp_path: Path):
    """Re-review (F1): a different filesystem failure mode than the
    developer's own `0o000` repro — `.spark/` with read but no execute
    permission (`0o444`) lets `iterdir()` list names but makes `is_dir()`'s
    stat call raise `PermissionError`. Caught by the same net."""
    import os

    from aspark_insights.errors import SparkDirUnreadableError

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    spark = repo / ".spark"
    spark.mkdir()
    (spark / "some-feature").mkdir()
    os.chmod(spark, 0o444)
    try:
        with pytest.raises(SparkDirUnreadableError):
            build_release_map(str(repo), "2026-08-19")
    finally:
        os.chmod(spark, 0o755)


def test_unreadable_feature_subdirectory_is_also_a_named_error(tmp_path: Path):
    """Re-review (F1): a genuinely different code path than `.spark/`
    itself being unreadable — a real, committed `.spark/<feature>/`
    subdirectory that later becomes unreadable is caught via
    `_member_entries` -> `read_artifact_status` -> `is_file()` re-raising
    `PermissionError` (EACCES isn't in `pathlib`'s own ignored-error set),
    not via `_list_feature_dirs`'s enumeration."""
    import os

    from aspark_insights.errors import SparkDirUnreadableError

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    feature_dir = repo / ".spark" / "some-feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text(
        "| | |\n|---|---|\n| **Status** | `approved` |\n", encoding="utf-8",
    )
    _git(repo, "add", ".spark/some-feature/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: some-feature spec")
    _git(repo, "tag", "v2.0.0")
    os.chmod(feature_dir, 0o000)
    try:
        with pytest.raises(SparkDirUnreadableError):
            build_release_map(str(repo), "2026-08-19")
    finally:
        os.chmod(feature_dir, 0o755)
