"""Read-only snapshot query core — shared by the CLI and the MCP server.

Imports only `store` and `errors` — never `build` — so read-only is enforced
by omission, not just documented (AC-1.5, NFR-2). Both `cli._cmd_query` and
`server.query` call `run_query`, so their answers are identical by
construction (NFR-8).
"""

from __future__ import annotations

from aspark_insights.errors import InsightsError
from aspark_insights.store import latest_snapshot_path, read_snapshot_dict, require_snapshot_shape


def run_query(location: str) -> dict:
    """Facts/metrics/provenance from the latest snapshot at `location`.

    Raises `InsightsError` (`no_snapshot` / `snapshot_unreadable`) on failure
    — never returns a partial or guessed result.
    """
    path = latest_snapshot_path(location)
    if path is None:
        raise InsightsError("no snapshot found; run `insights build` first", reason="no_snapshot")
    data = read_snapshot_dict(path)
    require_snapshot_shape(data, path)
    return {"facts": data["facts"], "metrics": data["metrics"], "provenance": data["provenance"]}
