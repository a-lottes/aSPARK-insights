"""RB-T8: determinism canary (AC-1.7, NFR-7)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from aspark_insights.gitboard.releasemap import build_release_map
from aspark_insights.serialization import canonical_json


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def test_double_build_is_byte_identical(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    (repo / ".spark" / "example").mkdir(parents=True)
    (repo / ".spark" / "example" / "spec.md").write_text(
        "| | |\n|---|---|\n| **Status** | `approved` |\n", encoding="utf-8",
    )
    _git(repo, "add", ".spark/example/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: example spec")
    _git(repo, "tag", "v2.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: open work")

    a = build_release_map(str(repo), "2026-08-19")
    b = build_release_map(str(repo), "2026-08-19")
    assert canonical_json(a) == canonical_json(b)
