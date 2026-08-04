"""insights CLI — build | query | render | diff | verify, in the family's C2 idiom.

JSON on stdout (sort_keys), human messages on stderr, exit 1 with a named error
on failure — never an unhandled traceback. Subcommands are wired up incrementally;
an unwired one reports itself as such rather than pretending to succeed.
"""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

from aspark_insights.build import build_snapshot
from aspark_insights.errors import GraphNotBuiltError, InsightsError, VerifyMismatchError
from aspark_insights.query import run_query
from aspark_insights.render import run_render
from aspark_insights.serialization import canonical_json
from aspark_insights.store import (
    read_snapshot_dict,
    require_snapshot_shape,
    write_snapshot,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="insights",
        description="Analytics for the aSPARK family.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser(
        "build",
        help="Build a snapshot from the graph — metrics carries real TRC-*/MTA-* entries.",
    )
    p_build.add_argument("--as-of", required=True, help="Date this snapshot represents, YYYY-MM-DD (an input, never the wall clock).")
    p_build.add_argument(
        "--repo", default=".",
        help="Repo root to read the graph from (default: .). Also where .aspark-insights/ "
             "derived state is written, unless --output redirects it.",
    )
    p_build.add_argument(
        "--output", default=None,
        help="Where to write .aspark-insights/ derived state (default: --repo). "
             "Set this to avoid writing into a repo you're only analyzing.",
    )

    p_query = sub.add_parser(
        "query",
        help="Read back facts/metrics/provenance from the last snapshot.",
    )
    p_query.add_argument("--repo", default=".", help="Repo root (default: .)")
    p_query.add_argument(
        "--output", default=None,
        help="Where the snapshot was written (default: --repo). Must match the --output "
             "used at build time, if any.",
    )

    p_serve = sub.add_parser(
        "serve",
        help="Run a read-only MCP stdio server exposing the `query` tool.",
    )
    p_serve.add_argument(
        "--repo", default=".",
        help="Repo root the snapshot was built for (default: .). Fixed for the "
             "server's entire process lifetime — never a per-call argument.",
    )
    p_serve.add_argument(
        "--output", default=None,
        help="Where the snapshot was written (default: --repo). Must match the "
             "--output used at build time, if any. Fixed at launch, same as --repo.",
    )

    p_render = sub.add_parser(
        "render",
        help="Render the latest snapshot as one self-contained HTML report.",
    )
    p_render.add_argument("--repo", default=".", help="Repo root (default: .)")
    p_render.add_argument(
        "--output", default=None,
        help="Where the snapshot was written (default: --repo). Must match the --output "
             "used at build time, if any.",
    )

    p_diff = sub.add_parser("diff", help="Diff two snapshots.")
    p_diff.add_argument("a")
    p_diff.add_argument("b")

    p_verify = sub.add_parser("verify", help="Recompute and byte-compare a snapshot.")
    p_verify.add_argument("snapshot")
    p_verify.add_argument("--repo", default=".", help="Repo root to recompute against (default: .)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            return _cmd_build(args)
        if args.command == "query":
            return _cmd_query(args)
        if args.command == "serve":
            return _cmd_serve(args)
        if args.command == "render":
            return _cmd_render(args)
        if args.command == "diff":
            return _cmd_diff(args)
        if args.command == "verify":
            return _cmd_verify(args)
        parser.error(f"command {args.command!r} not wired up yet")
        return 2  # pragma: no cover - argparse.error() exits before this
    except InsightsError as exc:
        print(canonical_json(exc.to_dict()), end="", file=sys.stderr)
        return 1


def _cmd_build(args: argparse.Namespace) -> int:
    snapshot = build_snapshot(args.repo, args.as_of)
    write_snapshot(args.output or args.repo, snapshot)
    print(canonical_json(snapshot.to_dict()), end="")
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    result = run_query(args.output or args.repo)
    print(canonical_json(result), end="")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from aspark_insights.server import run

    run(args.output or args.repo)
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    path = run_render(args.output or args.repo)
    print(canonical_json({"report": str(path)}), end="")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    a = read_snapshot_dict(args.a)
    b = read_snapshot_dict(args.b)
    print(canonical_json(_structural_diff(a, b)), end="")
    return 0


def _structural_diff(a: dict, b: dict) -> dict:
    """Field-by-field diff of two snapshot documents. Empty dict means no difference."""
    diff: dict = {}

    provenance_diff = {}
    keys = sorted(set(a.get("provenance", {})) | set(b.get("provenance", {})))
    for key in keys:
        va = a.get("provenance", {}).get(key)
        vb = b.get("provenance", {}).get(key)
        if va != vb:
            provenance_diff[key] = {"a": va, "b": vb}
    if provenance_diff:
        diff["provenance"] = provenance_diff

    if a.get("facts") != b.get("facts"):
        diff["facts"] = {"a": a.get("facts"), "b": b.get("facts")}

    if a.get("metrics") != b.get("metrics"):
        diff["metrics"] = {"a": a.get("metrics"), "b": b.get("metrics")}

    return diff


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)
    stored_data = read_snapshot_dict(path)  # raises a named error if missing/corrupt
    require_snapshot_shape(stored_data, path)  # raises if valid JSON but not snapshot-shaped
    stored_text = path.read_text(encoding="utf-8")
    as_of = stored_data["provenance"]["as_of"]

    try:
        recomputed = build_snapshot(args.repo, as_of)
    except GraphNotBuiltError as exc:
        # verify recomputes against --repo (default '.'), not a path recorded in
        # the snapshot itself — a bare "graph not built" reads as "you never ran
        # build," which is misleading when the real issue is a missing/wrong
        # --repo (B4).
        raise GraphNotBuiltError(
            f"{exc} (verify recomputes against --repo, which defaults to '.' — "
            "pass --repo pointing at the analyzed repo if this isn't it)"
        ) from exc
    recomputed_text = canonical_json(recomputed.to_dict())

    matches = recomputed_text == stored_text
    if not matches:
        raise VerifyMismatchError(f"recomputed snapshot does not byte-match stored file: {path}")
    print(canonical_json({"snapshot": str(path), "matches": True}), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
