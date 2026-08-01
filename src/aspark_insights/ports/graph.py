"""GraphPort — the only seam to aspark-graph.

Two adapters:

- ``LibraryInterimGraphPort`` imports ``aspark_graph`` directly to read the whole
  graph document in one shot. This is a deliberate anti-corruption violation —
  the graph has no bulk `export` query yet (G6, unshipped) — kept behind this one
  port with a named sunset condition, so nothing else in this codebase reaches
  into the sibling's internals (AC-2.4, enforced by the boundary test in T7).
- ``CLIGraphPort`` subprocesses the graph's own published CLI contract (JSON on
  stdout, exit 1 on an unbuilt graph) for named queries.

Neither adapter reads ``.aspark-graph/graph.json`` from anywhere outside this file.
"""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
from pathlib import Path
from typing import Protocol

from aspark_insights.errors import GraphNotBuiltError, GraphUnreadableError, GraphVersionMismatchError

# The interim library adapter imports aspark_graph internals directly, so any
# version bump — even a patch — could change Graph.to_dict()'s shape under us.
# Bump this only alongside a deliberate re-validation of the adapter (AC-2.2).
PINNED_ASPARK_GRAPH_VERSION = "0.7.0"


class GraphPort(Protocol):
    access_mode: str

    def read_graph(self, repo_root: str | Path) -> dict:
        """Return the canonical ``{"nodes": [...], "edges": [...]}`` document."""
        ...

    def query(self, name: str, *args: str, repo_root: str | Path = ".") -> dict:
        """Run one of the graph's published queries; return its parsed JSON result."""
        ...


class LibraryInterimGraphPort:
    """Sunset condition: retire once the graph ships a bulk `export` query (G6)."""

    access_mode = "library-interim"

    def __init__(self, pinned_version: str = PINNED_ASPARK_GRAPH_VERSION) -> None:
        self._pinned_version = pinned_version

    def _check_version(self) -> None:
        # importlib.metadata, never aspark_graph.__version__: the sibling's
        # __version__ is stale (reports 0.1.0 against packaging metadata 0.7.0)
        # and would silently pass a wrong-version import (AC-2.2).
        installed = importlib.metadata.version("aspark-graph")
        if installed != self._pinned_version:
            raise GraphVersionMismatchError(
                f"aspark-graph {installed} is installed, but this adapter is "
                f"pinned to {self._pinned_version}"
            )

    def read_graph(self, repo_root: str | Path) -> dict:
        self._check_version()
        from aspark_graph.graph import Graph, default_graph_path

        path = default_graph_path(repo_root)
        if not Path(path).exists():
            raise GraphNotBuiltError(f"graph not built: {path} does not exist")
        try:
            return Graph.load(path).to_dict()
        except json.JSONDecodeError as exc:
            raise GraphUnreadableError(f"graph at {path} contains invalid JSON: {exc}") from exc
        except KeyError as exc:
            # A node/edge entry is missing a field Graph.load requires (e.g. "type").
            # str(KeyError) is just the missing key repr ("'type'") — folded into a
            # sentence so this doesn't read as a bare, unexplained Python exception.
            raise GraphUnreadableError(
                f"graph at {path} has an entry missing required field {exc}"
            ) from exc
        except (AttributeError, TypeError) as exc:
            # Valid JSON that isn't the expected shape (a top-level list/str/null/
            # number, or a node/edge that isn't a dict) — Graph.load's internal
            # `data.get(...)` calls raise these rather than KeyError/ValueError.
            raise GraphUnreadableError(
                f"graph at {path} is not shaped like a graph document (expected an "
                f"object with 'nodes' and 'edges' lists of objects): {exc}"
            ) from exc
        except ValueError as exc:
            raise GraphUnreadableError(f"graph at {path} contains invalid data: {exc}") from exc

    def query(self, name: str, *args: str, repo_root: str | Path = ".") -> dict:
        raise NotImplementedError(
            "LibraryInterimGraphPort has no named-query surface; use CLIGraphPort"
        )


class CLIGraphPort:
    """Subprocesses the graph's own published CLI — its C2 contract, unchanged."""

    access_mode = "cli"

    def read_graph(self, repo_root: str | Path) -> dict:
        raise NotImplementedError(
            "CLIGraphPort has no bulk read query yet (blocked on the graph's G6 export)"
        )

    def query(self, name: str, *args: str, repo_root: str | Path = ".") -> dict:
        cmd = ["aspark-graph", "query", name, *args, "--repo", str(repo_root)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise GraphNotBuiltError(f"aspark-graph CLI not found on PATH: {exc}") from exc
        if result.returncode != 0:
            raise GraphNotBuiltError(
                result.stderr.strip() or f"{' '.join(cmd)} exited {result.returncode}"
            )
        return json.loads(result.stdout)
