"""FL-T1: `insights features` CLI, real git, against this repo's own real
data (feature-lens AC-1.1, AC-1.2, AC-2.2, NFR-1)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=repo,
    )


def test_real_repo_lists_all_eleven_named_features_exactly_once():
    result = _run_cli(_REPO_ROOT, "features", "--as-of", "2026-08-25", "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    names = [f["name"] for f in payload["features"]]
    expected = {
        "foundation", "traceability-metrics", "mcp-server", "public-repo-polish",
        "snapshot-report", "measurement-honesty", "git-native-mid-cycle-board",
        "release-board", "release-board-html", "release-board-docs", "release-metrics",
    }
    # containment + exactly-once over the 11 NAMED features (plan §4/§5 R1):
    # this feature's own .spark/feature-lens/ becomes a real 12th, genuinely
    # in-flight row the moment this increment's artifacts are committed —
    # never asserted as an exact total count.
    assert expected.issubset(set(names))
    for name in expected:
        assert names.count(name) == 1


def test_real_repo_release_board_docs_delivers_in_v0_10_0_not_v0_11_0():
    """AC-1.2: delivered in v0.10.0, appears exactly once, v0.11.0 is never
    shown as a second delivery despite the real trailing occurrence there."""
    result = _run_cli(_REPO_ROOT, "features", "--as-of", "2026-08-25", "--format", "json")
    payload = json.loads(result.stdout)
    rows = [f for f in payload["features"] if f["name"] == "release-board-docs"]
    assert len(rows) == 1
    assert rows[0]["delivered_in"] == "v0.10.0"


def test_real_repo_named_features_all_show_gate_released_with_literal_status():
    """AC-2.2: verified against this repo's own real data, not a fixture."""
    result = _run_cli(_REPO_ROOT, "features", "--as-of", "2026-08-25", "--format", "json")
    payload = json.loads(result.stdout)
    named = {
        "foundation", "traceability-metrics", "mcp-server", "public-repo-polish",
        "snapshot-report", "measurement-honesty", "git-native-mid-cycle-board",
        "release-board", "release-board-html", "release-board-docs", "release-metrics",
    }
    for f in payload["features"]:
        if f["name"] not in named:
            continue
        assert f["gate"] == "Released"
        assert f["gate_evidence"][0]["artifact"] == "release"
        assert f["gate_evidence"][0]["status"] is not None


def test_json_output_is_canonical_sorted_keys():
    result = _run_cli(_REPO_ROOT, "features", "--as-of", "2026-08-25", "--format", "json")
    canonical = json.dumps(json.loads(result.stdout), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    assert result.stdout == canonical


def test_help_documents_membership_and_write_location():
    result = _run_cli(_REPO_ROOT, "features", "--help")
    assert result.returncode == 0
    assert "no commit under it is not listed" in result.stdout
    assert "--output" in result.stdout
