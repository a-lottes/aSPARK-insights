"""gitboard walking skeleton (GB-T1): `board --format json` end to end against
real git repos — never mocked, per this project's own sibling-integration
precedent (test_graph_integration.py's "never mock the real dependency").
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import InsightsError
from aspark_insights.gitboard.board import build_board


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env_args = ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args]
    return subprocess.run(env_args, cwd=repo, capture_output=True, text=True, check=True)


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


@pytest.fixture
def tagless_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "tagless"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only commit")
    return repo


@pytest.fixture
def bare_no_graph_no_spark_repo(tmp_path: Path) -> Path:
    """US-2's exact target: a real git repo with neither `.aspark-graph/` nor
    `.spark/` present — proves the standalone claim, not just describes it."""
    repo = tmp_path / "bare"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: bare")
    _git(repo, "tag", "v0.1.0")
    assert not (repo / ".aspark-graph").exists()
    assert not (repo / ".spark").exists()
    return repo


# --- AC-1.2 / AC-1.9: honest null on no tags, exit 0 -------------------------


def test_no_tag_repo_reports_null_commits_exit_0(tagless_repo: Path):
    result = _run_cli(tagless_repo, "board", "--as-of", "2026-08-13")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["commits"]["value"] is None
    assert "no tags" in data["commits"]["reason"]
    assert data["provenance"]["source"] == "git-interim"  # AC-1.9


def test_no_tag_repo_omits_days_since_tag_and_work_types_entirely(tagless_repo: Path):
    """AC-1.10(a)/AC-1.12(c): absent, not a second null for the same cause
    AC-1.2 already explains once."""
    board = build_board(str(tagless_repo), "2026-08-13")
    assert "days_since_tag" not in board
    assert "work_types" not in board


# --- AC-1.5: git absent is distinct from "no tag" ---------------------------


def test_git_absent_is_distinct_named_error(tagged_repo: Path, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent-bin-dir")
    with pytest.raises(InsightsError) as exc_info:
        build_board(str(tagged_repo), "2026-08-13")
    assert exc_info.value.reason == "git_unavailable"


# --- AC-2.1/2.2/2.3: the standalone proof ------------------------------------


def test_runs_with_zero_graph_zero_spark(bare_no_graph_no_spark_repo: Path):
    result = _run_cli(bare_no_graph_no_spark_repo, "board", "--as-of", "2026-08-13")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["commits"]["value"] == 0  # HEAD is the tag itself


def test_gitboard_package_never_imports_graph_port():
    """AC-2.2, structurally: the package's own source never *imports*
    GraphPort/aspark_graph — checked against actual import lines, not a bare
    substring scan (which would also trip on this feature's own doc comments
    explaining that it does *not* import them)."""
    import ast

    import aspark_insights.gitboard.board as board_mod
    import aspark_insights.gitboard.gitread as gitread_mod
    import aspark_insights.gitboard.worktype as worktype_mod

    for mod in (board_mod, gitread_mod, worktype_mod):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module)
        assert not any("graph" in name.lower() for name in imported_names), imported_names


def test_non_git_directory_is_an_honest_named_result_never_a_fabricated_zero(tmp_path: Path):
    """AC-2.3: mirrors NullPolicyPort's 'no source configured -> honest
    unavailable' — never a count:0 success."""
    result = _run_cli(tmp_path, "board", "--as-of", "2026-08-13")
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["error"] == "not_a_git_repo"
    assert '"value": 0' not in result.stdout
    assert result.stdout == ""


# --- AC-1.6: byte-identical on repeat -----------------------------------------


def test_repeated_build_is_byte_identical(tagged_repo: Path):
    from aspark_insights.serialization import canonical_json

    first = canonical_json(build_board(str(tagged_repo), "2026-08-13"))
    second = canonical_json(build_board(str(tagged_repo), "2026-08-13"))
    assert first == second


# --- AC-1.8: shallow disclosure ------------------------------------------------


def test_shallow_flag_present_and_false_for_a_full_clone(tagged_repo: Path):
    board = build_board(str(tagged_repo), "2026-08-13")
    assert board["provenance"]["shallow"] is False


# --- NFR-1: CLI idiom ----------------------------------------------------------


def test_cli_output_is_sort_keys_json(tagged_repo: Path):
    result = _run_cli(tagged_repo, "board", "--as-of", "2026-08-13")
    assert result.returncode == 0, result.stderr
    from aspark_insights.serialization import canonical_json

    data = json.loads(result.stdout)
    assert result.stdout == canonical_json(data)


def test_board_help_documents_the_standalone_read(tmp_path: Path):
    result = _run_cli(tmp_path, "board", "--help")
    assert result.returncode == 0
    assert "--repo" in result.stdout
    assert "git-interim" in result.stdout or "graph" in result.stdout.lower()
