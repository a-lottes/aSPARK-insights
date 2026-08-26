"""FL-T9: close-out — version, --help, no new error class, no shipped
gitboard file touched (feature-lens NFR-1, NFR-2)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )


def test_version_is_0_12_0():
    import aspark_insights

    assert aspark_insights.__version__ == "0.12.0"


def test_pyproject_version_matches():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.12.0"' in text


def test_no_new_insights_error_subclass():
    from aspark_insights import errors

    # every InsightsError subclass predates this feature; featurelens raises
    # only the already-shipped ReleaseMapUnreadableError.
    subclasses = {cls.__name__ for cls in errors.InsightsError.__subclasses__()}
    assert "FeatureLensError" not in subclasses
    assert "FeatureLensUnreadableError" not in subclasses


def test_features_help_documents_output_and_membership_rule():
    result = _run_cli("features", "--help")
    assert result.returncode == 0
    assert "--output" in result.stdout
    assert "no commit under it is not listed" in result.stdout


def test_no_shipped_gitboard_file_was_touched():
    """review F9: diffs against the fixed commit this feature's own
    increment started from (`cb8b664`), not the mutable working-tree
    status — a `git status`-based check goes vacuously true the moment
    this increment is committed (a clean tree yields zero lines, so the
    loop body never runs again). `git diff` never shows untracked files
    regardless of arguments, so pre-commit (now) the two new modules are
    invisible to it and only appear via `ls-files --others`; post-commit
    they become visible to the diff instead. Checking both keeps this
    test meaningful on either side of `/go-live`."""
    tracked_changed = subprocess.run(
        ["git", "diff", "--name-only", "cb8b664", "--", "src/aspark_insights/gitboard/"],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    untracked_new = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src/aspark_insights/gitboard/"],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    changed = [f.strip() for f in tracked_changed + untracked_new if f.strip()]
    assert changed  # the two new modules must actually show up somewhere
    for f in changed:
        assert "featurelens" in f, f"unexpected gitboard change: {f}"
