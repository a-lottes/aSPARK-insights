"""T2: the MCP `query` tool and `insights query` agree, byte-for-byte (NFR-8).

Parity is structural here — both adapters call the same `run_query()` — but
this test proves it against real subprocess/in-process behaviour rather than
just trusting the shared-function argument.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights import server
from aspark_insights.build import build_snapshot
from aspark_insights.store import write_snapshot

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_query_cli_equals_mcp_for_the_same_on_disk_snapshot(built_repo: Path):
    build_result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build_result.returncode == 0, build_result.stderr

    cli_result = _run_cli(built_repo, "query")
    assert cli_result.returncode == 0, cli_result.stderr
    cli_out = json.loads(cli_result.stdout)

    server._location = str(built_repo)
    mcp_out = server.query()

    assert mcp_out == cli_out
