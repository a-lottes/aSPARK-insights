# Plan: mcp-server

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/mcp-server/spec.md` (`approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-03 |

## 1. Architecture Decision

- **Context:** I2 shipped a real `insights query --repo X` that reads the latest snapshot via
  `store.latest_snapshot_path` → `read_snapshot_dict` → `require_snapshot_shape` and prints
  `canonical_json({"facts","metrics","provenance"})`. The spec adds an `insights serve` stdio
  MCP server exposing exactly one tool, `query`, that must return **value-identical** output
  (NFR-8, AC-1.3) with **zero call-time parameters** (AC-1.2), **never** reaching the
  computation path `build`/`verify` use (AC-1.5, NFR-2), and **never** leaking a traceback
  (AC-1.4, NFR-3). The family already solved the CLI↔MCP idiom in `aspark-graph`
  (`server.py` FastMCP, `cli.py serve` subcommand, `mcp>=1.12,<1.20`); we mirror it, with one
  deliberate divergence — graph's tools take a per-call `repo=` arg; ours must take none.

- **Decision:** Extract the read-only query core into a new `query.py` (`run_query(location) ->
  {"facts","metrics","provenance"}`) that imports **only** `store` + `serialization` + `errors`
  — never `build`. `cli._cmd_query` is refactored to call it (CLI output byte-unchanged); the
  new `server.py` calls the same function, so parity is by construction. The zero-parameter
  constraint (the load-bearing design) is met by fixing the location **once at process launch**:
  `serve` resolves `--output or --repo` and passes it to `server.run(location)`, which stores it
  in module state before `mcp.run()`; the `@mcp.tool()`-decorated `query()` takes no arguments
  and reads that module state — the caller can never contribute a path. Read-only is enforced by
  **omission** (A3): `server.py`/`query.py` structurally never import `build_snapshot`/verify,
  guarded grep/AST-style by extending `tests/test_boundary.py`. Errors reuse the existing
  taxonomy: the tool catches `InsightsError` and returns `{"found": False, "reason": exc.reason,
  "message": str(exc)}` — `no_snapshot` and `snapshot_unreadable` already exist, no new
  vocabulary. `SECURITY.md` ships as a DoD of US-2, its structure mirrored from
  `aspark-graph/SECURITY.md`, tested by doc-introspection.

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | MCP tool imports `cli._cmd_query` / calls the existing CLI path | `cli.py` imports `build_snapshot`; importing it into `server.py` transitively pulls the computation path in, defeating the grep-checkable "never imports build" enforcement (AC-1.5). A build-free `query.py` is the clean seam. |
  | Give the `query` tool a `repo`/`output` parameter (mirror graph's `repo="."`) | Violates AC-1.2/NFR-1 head-on: any per-call string that becomes a path is exactly the surface the spec removes. The fixed-at-launch location is the *stronger, simpler* mitigation the spec chose over graph's confinement check (A4). |
  | Subprocess `insights query` from the server and forward its stdout | Value-identity via string-parsing the CLI is brittle, adds a process per call (NFR-7), and re-opens the "which flags" question the fixed launch config closes. In-process shared function is faithful by construction. |
  | Reimplement snapshot reading inside `server.py` | Two read paths drift; NFR-8 value-identity becomes a maintenance promise instead of a structural fact. One `run_query` for both adapters. |
  | Invent a `found/found_reason` MCP error vocabulary | Constitution + AC-1.4 require reusing `errors.py`'s `reason` strings. The `{"found": False, "reason", "message"}` envelope reuses existing `reason` values verbatim — same shape `aspark-graph/server.py` already uses. |
  | Add a repo-confinement/marker check like graph's G3 | Explicitly out of scope (A4): with no per-call path left to confine and a fixed operator-chosen target, a marker check adds surface without a threat. Documented as a non-guarantee in `SECURITY.md`, not built. |

- **Consequences:** Easier — CLI↔MCP parity is structural, not a promise; a future newly
  registered TRC-*/MTA-* metric appears over MCP with zero server change (AC-1.3, no metric
  named in the tool); read-only is grep-checkable, not asserted. Harder — one new runtime
  dependency (`mcp`, already transitive via `aspark-graph` but now declared directly); module
  state for the fixed location means the server is single-location by design (matches A2, not a
  limitation to fix); the `query` core moves out of `cli.py`, a small refactor `_cmd_query` and
  its tests must follow.

## 2. Affected Components

**Blast radius scoped by hand** — not by an `impact` query. Mirrors the `traceability-metrics`
precedent: the change is dominated by *new* files (`server.py`, `query.py`) that no graph
indexes yet; the only pre-indexed source file edited is `cli.py`, whose downstream is confined
to this package's own CLI dispatch. A confirming call is named below; it will not change scope.

- **New:** `src/aspark_insights/server.py` (FastMCP stdio server, `query` tool, `run(location)`);
  `src/aspark_insights/query.py` (`run_query` read core); `SECURITY.md`; tests
  `tests/test_mcp_transport.py`, `tests/test_query_core.py`, `tests/test_cli_mcp_parity.py`,
  `tests/test_mcp_errors.py`, `tests/test_mcp_readonly.py`, `tests/test_security_doc.py`.
- **Edited:** `src/aspark_insights/cli.py` (`serve` subcommand; `_cmd_query` delegates to
  `run_query`; `--help` text); `pyproject.toml` (declare `mcp` dep); `tests/test_boundary.py`
  (extend to forbid `build`/verify imports in `server.py`/`query.py`); `README.md` (list the
  `serve`/`query` MCP surface, link `SECURITY.md`).
- **New runtime dependency — `mcp>=1.12,<1.20`.** *Justification:* the feature exposes a stdio
  MCP server; FastMCP is the family's established SDK for exactly this (`aspark-graph/server.py`).
  We adopt graph's **exact pin** deliberately — `<1.20` because mcp 1.20 hard-pulls
  `cryptography` (server-side OAuth we do not use), which has no macOS x86_64 wheel and would
  break install; `>=1.12` is the floor exposing `mcp.server.fastmcp.FastMCP` + `@mcp.tool()`.
  `mcp` is already present transitively via the `aspark-graph==0.7.0` path dep, but relying on a
  sibling's transitive dep for our own direct import is fragile — declared directly, same pin, no
  second SDK introduced.
- **Available confirming call (optional):**
  `aspark-graph query impact src/aspark_insights/cli.py --repo .`

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Walking skeleton: `insights serve` boots a zero-param stdio `query` tool | US-1 | AC-1.1, AC-1.2, AC-1.6, NFR-1, NFR-4, NFR-6 | – | `done` | `insights serve --repo <path> --output <path>` (defaults mirroring `query`: `--repo` default `.`, `--output` default `None`→uses repo, documented in `--help`) boots a FastMCP stdio server; `server.run(location)` sets module state, then `mcp.run()`; a `@mcp.tool()` `query()` takes **zero** parameters and (for now) returns the `no_snapshot` envelope. A stdio round-trip test (mirroring `aspark-graph/tests/test_mcp_transport.py`: initialize→notifications/initialized→tools/call `query` with empty arguments, match by id, watchdog+stderr-drain) gets a well-formed JSON-RPC result and the process exits 0; a second test asserts `query`'s signature has no parameters (reads no `repo`/`path`/`output`). No HTTP/port/auth surface exists — files: src/aspark_insights/server.py, src/aspark_insights/cli.py, pyproject.toml, tests/test_mcp_transport.py |
| T2 | Read core + value-identical output | US-1 | AC-1.3, NFR-5, NFR-7, NFR-8 | T1 | `done` | New `run_query(location) -> {"facts","metrics","provenance"}` importing only `store`/`serialization`/`errors` (never `build`), raising the existing `no_snapshot`/`snapshot_unreadable` `InsightsError`s; `cli._cmd_query` refactored to call it and print `canonical_json(result)` — a regression test proves CLI stdout is byte-unchanged from before; the `query` tool returns `run_query(<fixed location>)`; a parity test builds a snapshot and asserts the tool's returned dict equals the parsed `insights query` stdout for the same on-disk snapshot, and that whatever `metrics` entries are present pass through un-enumerated. Public surface adds only `serve` + `run_query`/`run` — files: src/aspark_insights/query.py, src/aspark_insights/cli.py, src/aspark_insights/server.py, tests/test_query_core.py, tests/test_cli_mcp_parity.py |
| T3 | Named-error shapes over stdio | US-1 | AC-1.4, NFR-3 | T2 | `done` | The `query` tool wraps `run_query` in a single `except InsightsError` returning `{"found": False, "reason": exc.reason, "message": str(exc)}` — never a raised exception through the transport; a no-snapshot fixture yields `reason == "no_snapshot"` and a present-but-malformed snapshot fixture (valid JSON, wrong shape / not JSON) yields `reason == "snapshot_unreadable"`, both `found is False`, both reusing `errors.py`'s existing `reason` values with no invented vocabulary — files: src/aspark_insights/server.py, tests/test_mcp_errors.py |
| T4 | Structural read-only + no-write guarantee | US-1 | AC-1.5, NFR-2 | T2 | `done` | `tests/test_boundary.py` extended so a planted `import`/reference of `build`/`build_snapshot`/`verify` in `server.py` or `query.py` fails the scan (same planted-regression style as its existing `aspark_graph` guard, proving the guard bites, not just that none exists today); a behavioural test calls the `query` tool N (≥3) times against a built-snapshot fixture and asserts no new write appears anywhere under `.aspark-insights/` (mtime/dirlisting snapshot before vs after) and no `GraphPort` is constructed — files: tests/test_boundary.py, tests/test_mcp_readonly.py |
| T5 | `SECURITY.md` trust-boundary doc | US-2 | AC-2.1, AC-2.2, AC-2.3, AC-2.4 | – | `done` | `SECURITY.md` at repo root, structured from `aspark-graph/SECURITY.md`, stating the trust boundary (local stdio child process, invoking user's permissions, no auth/HTTP/network/remote, one fixed repo/output per process set at launch — AC-2.1); a *Non-guarantees* section naming **all four** items of AC-2.2 (read-only by omission; no repo-confinement/marker check; removes no privilege the operator lacked; identifier strings originate from the analyzed repo's `.spark/`); a vulnerability-reporting channel + response window (AC-2.3); and no use of "sandbox"/"isolat"/"contain"/"prevent"/"protect" outside *Non-guarantees* (AC-2.4). A doc-introspection test (mirroring `aspark-graph/tests/test_security_doc.py`: section extraction + substring/count + denylist assertions) proves each — files: SECURITY.md, tests/test_security_doc.py |

## 4. Test Strategy

- **US-1 (read-only zero-param query tool):**
  - *Unit / in-process* — `run_query` on built / no-snapshot / malformed-snapshot fixtures
    (T2, T3); the `query` tool called directly (the `@mcp.tool()` function stays callable,
    same technique as graph's parity/error tests) for value-identity (T2) and each named-error
    shape (T3); zero-parameter signature assertion (T1).
  - *Integration (real stdio)* — one true round-trip launching the actual `insights serve`
    process and sending a real MCP `initialize`+`tools/call query`, mirroring
    `aspark-graph/tests/test_mcp_transport.py` (watchdog, stderr-drain, match-by-id). Per the
    constitution, the underlying `aspark-graph` dependency is **never mocked** — the snapshot
    under test is built for real (T1/T4 fixtures use a real built snapshot).
  - *Structural* — the boundary scan that `server.py`/`query.py` never import the build/verify
    path (T4), and the no-`.aspark-insights/`-write behavioural test across N calls (T4).
  - *Deliberately `/demo-day`* — NFR-7 sub-1s latency observation and NFR-2's "no write during a
    call" observed live. Reason: the automated T2 read path already proves the tool only reads a
    small on-disk JSON (no computation), so wall-clock timing is a confirmation, not the proof;
    live observation belongs to the real-client demo per the spec's own verification column.
- **US-2 (`SECURITY.md`):** doc-introspection tests (T5) — section presence, the four
  non-guarantees, the reporting channel, and the anti-overclaim denylist confined to
  *Non-guarantees*. No manual step: the document's claims are machine-checked so it cannot rot.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Module-state location design lets a second `serve` in-process, or a test, leak/reuse stale state | A tool call reads the wrong repo → NFR-8 parity silently wrong | One location set once in `run()` before `mcp.run()` (A2: one process, one location); parity test asserts the returned dict matches `insights query` for the *same* on-disk snapshot, catching a wrong-location read |
| A future edit imports `cli`/`build` into `server.py` for convenience, re-coupling the compute path | AC-1.5/NFR-2 regress silently — read-only-by-omission broken | The `query.py` build-free seam removes the temptation; the extended boundary guard (T4) fails the build on any planted `build`/verify import, proven to bite via a planted-regression test |
| `mcp` SDK wire/API drift across `>=1.12,<1.20` breaks the stdio round-trip or `@mcp.tool()` zero-arg form | Transport test flaky or serve broken on a resolved-but-untested mcp version | Adopt graph's exact, family-verified pin and its proven transport-test harness (watchdog + stderr-drain + match-by-id); the round-trip test is the canary if a resolved mcp diverges |
| `mcp` capped `<1.20` (no `cryptography` wheel on macOS x86_64) collides with a future dep wanting `>=1.20` | Install breaks on Intel macOS, as it did for graph | Documented in `pyproject` comment + `SECURITY.md` as a packaging decision; lifting the cap is tied to a real auth/remote feature that does not exist here (NFR-6) |
| Value-identity assumed but `run_query` and `_cmd_query` drift after the refactor | NFR-8 becomes a promise, not a fact | Single shared `run_query` for both adapters (structural parity); a CLI-byte-unchanged regression test (T2) plus the CLI↔MCP parity test pin both ends |
| A1's `insights serve` assumes graph's `serve` idiom, but insights' zero-param tool diverges from graph's `repo=`-per-call tools | A reviewer expecting graph's shape reads the divergence as a mistake | The ADR records the divergence as deliberate (AC-1.2 forbids the per-call path graph allows); `SECURITY.md` states the fixed-launch-target rationale (A4) |

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (named-error taxonomy + `canonical_json` reused; `GraphPort` untouched — the read path never reaches it; no ambient clock; `--output` discipline on `serve`; sibling `aspark-graph` never mocked)
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
