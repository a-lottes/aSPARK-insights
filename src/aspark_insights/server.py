"""FastMCP stdio server — a zero-parameter, read-only adapter over query.py.

The repo/output location is fixed once at process launch (`run(location)`,
called from `insights serve`) and kept in module state for the server's
entire lifetime — the `query` tool takes no arguments at all, so no caller
can supply or influence a filesystem path (AC-1.2). Read-only is enforced by
omission: this module never imports the snapshot-computation entrypoint or
any graph port (AC-1.5) — see tests/test_boundary.py, which fails the build
if it ever does.

Uses the official `mcp` SDK's FastMCP (a local stdio server, no auth/HTTP).
See pyproject.toml for why `mcp` is capped below the version that pulls
`cryptography`.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aspark_insights.errors import InsightsError
from aspark_insights.query import run_query

mcp = FastMCP("aspark-insights")

_location: str | None = None


@mcp.tool()
def query() -> dict:
    """Read facts/metrics/provenance from the latest snapshot at the server's
    fixed repo/output location. Takes no arguments — the location can never be
    supplied or changed per call. Never triggers a fresh build.

    On failure returns a clean `{"found": False, "reason", "message"}` dict —
    never an exception through the stdio transport — reusing `errors.py`'s
    existing `reason` values (`no_snapshot`, `snapshot_unreadable`)."""
    try:
        return run_query(_location)
    except InsightsError as exc:
        return {"found": False, "reason": exc.reason, "message": str(exc)}


def run(location: str) -> None:
    """Fix the repo/output location for this process, then serve over stdio."""
    global _location
    _location = location
    mcp.run()


if __name__ == "__main__":  # pragma: no cover - launched via `insights serve`
    raise SystemExit("run via `insights serve --repo <path> --output <path>`")
