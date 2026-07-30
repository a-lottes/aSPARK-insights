"""US-1: family-stack package scaffold (AC-1.1, AC-1.2, AC-1.3)."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_imports_clean():
    import aspark_insights
    import aspark_insights.cli
    import aspark_insights.metrics
    import aspark_insights.model
    import aspark_insights.ports

    assert aspark_insights.__version__


def test_pyproject_facts():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.11"
    assert data["build-system"]["build-backend"] == "hatchling.build"
    assert "aspark-graph==0.7.0" in data["project"]["dependencies"]
    assert data["tool"]["uv"]["sources"]["aspark-graph"]["path"] == "../aSPARK-graph"


def test_gitignore_excludes_derived_state_not_spark():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".aspark-insights/" in text
    assert ".spark" not in text
