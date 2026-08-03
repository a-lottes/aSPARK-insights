"""T1: stdio MCP transport smoke test — `insights serve` boots a zero-param
`query` tool (AC-1.1, AC-1.2, AC-1.6).

Wire format: newline-delimited JSON (one compact JSON object + "\n" per
message). Handshake: initialize (id:1) -> notifications/initialized ->
tools/call (id:2). Match responses by "id" — the server emits the initialize
response before the tool result. Mirrors aspark-graph's own
tests/test_mcp_transport.py (the family's proven harness for this SDK).
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
import threading

from aspark_insights import server


def test_mcp_stdio_transport_round_trip(tmp_path):
    """AC-1.1/1.2/1.6: `insights serve` boots, `query` takes zero arguments,
    and a real stdio round-trip gets a well-formed JSON-RPC result."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "aspark_insights.cli", "serve", "--repo", str(tmp_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Drain stderr concurrently to prevent pipe-buffer deadlock and to capture
    # diagnostic content for timeout failures.
    stderr_buf: list[bytes] = []
    stderr_drain = threading.Thread(
        target=lambda: stderr_buf.append(proc.stderr.read()),
        daemon=True,
    )
    stderr_drain.start()

    # Watchdog: kill the process if the read loop deadlocks.
    watchdog = threading.Timer(10.0, proc.kill)
    watchdog.start()
    tool_response = None
    try:
        for msg in [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "smoke", "version": "0"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "query", "arguments": {}},
            },
        ]:
            proc.stdin.write((json.dumps(msg, separators=(",", ":")) + "\n").encode())
        proc.stdin.flush()

        # Read stdout lines; match by id==2 — initialize response arrives first.
        while True:
            raw = proc.stdout.readline()
            if not raw:
                break
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if data.get("id") == 2:
                tool_response = data
                break
    finally:
        watchdog.cancel()

    if tool_response is None:
        proc.kill()

    proc.stdin.close()
    proc.wait(timeout=5)
    stderr_drain.join(timeout=2)
    proc.stdout.close()
    proc.stderr.close()

    stderr_out = (stderr_buf[0] if stderr_buf else b"").decode(errors="replace")

    assert tool_response is not None, (
        f"No id=2 response within 10 s; server stderr: {stderr_out!r}"
    )
    assert "error" not in tool_response, f"Unexpected transport error: {tool_response}"
    assert proc.returncode == 0, f"Server exited with code {proc.returncode}"


def test_query_tool_signature_takes_no_parameters():
    """AC-1.2: no parameter of any kind — not `repo`, `path`, `output`, or
    anything else that could become or contribute to a filesystem path."""
    sig = inspect.signature(server.query)
    assert sig.parameters == {}
