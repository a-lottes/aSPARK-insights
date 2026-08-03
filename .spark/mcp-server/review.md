# Review Report: mcp-server

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | The diff of `/increment`, `.spark/mcp-server/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-03 |

## 1. Scope

Reviewed every uncommitted change vs `HEAD` (`0e60deb`): new `src/aspark_insights/server.py`,
`query.py`, `SECURITY.md`, six new `tests/test_mcp_*`/`test_query_core`/`test_security_doc` files;
edited `cli.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_boundary.py`. Read all in
full, plus adjacent `store.py`/`errors.py`/`cli.main` for context. Ran the full suite and targeted
probes myself. **aspark-graph:** `staleness` returned `stale: true` → per the tool's stale⇒absent
rule I treated the graph as absent and scoped by hand (the two load-bearing files, `server.py` and
`query.py`, are new and unindexed regardless). Not reviewed: NFR-7 wall-clock latency (deferred to
`/demo-day` by the plan); live no-write observation (automated behavioural test stands in — T4).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `serve` boots a zero-param stdio `query` tool; `run(location)` sets module state then `mcp.run()`; transport + signature tests present. |
| T2 | ✅ | `run_query(location)` imports only `store`/`errors`; `_cmd_query` delegates; CLI-byte-unchanged + parity tests present. |
| T3 | ✅ (with a gap fixed in F1) | `query` wraps `run_query` in `except InsightsError`. The malformed-snapshot claim was only partly true — see F1. |
| T4 | ✅ | Boundary guard extended with a real planted-regression proof; behavioural no-write + no-GraphPort tests present, run by default `pytest`. |
| T5 | ✅ | `SECURITY.md` matches all four AC-2.x; each claim verified against code (see §4); doc-introspection test present. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Blocker | `store.py:49` `require_snapshot_shape` (reached via `query.py:25`, both CLI `query` and MCP `query`) | A snapshot file that is valid JSON but a **bare scalar/null** (`5`, `null`, `3.14`) hit `key not in data` with a non-iterable → raw **`TypeError`**. On the CLI this printed a full Python traceback and on MCP escaped the `except InsightsError` — violating AC-1.4/NFR-3 and the "never a raw traceback" non-negotiable, exactly the constitution's own hostile-input checklist item (list/string/null/number). Verified live before/after. **Fix:** added `isinstance(data, dict)` guard raising `SnapshotUnreadableError` (narrow — only `query`/`verify` call this fn; `diff`'s `.get()` tolerance untouched) + parametrized regression tests in `test_query_core.py` and `test_mcp_errors.py`. Re-ran the original repro: both surfaces now return `snapshot_unreadable`. | fixed |
| F2 | Minor | `pyproject.toml:3` (`version = "0.2.0"`) | This feature adds a real public entry point (`serve`) and a new runtime dependency — a minor-version-worthy behaviour change under the library lens (NFR-5), unlike `public-repo-polish`'s deliberate no-bump. No bump in the diff. Version bumps land at `/go-live`, so this is a reminder, not an open blocker: bump the minor at release so "the version changed" keeps meaning "behaviour changed." | accepted — user confirmed 2026-08-03; carry as a `/go-live` reminder, no code change needed now |
| F3 | Nit | `server.py:23,25` | Module-level `mcp` (and `_location`) are importable public-ish names beyond the declared `serve`/`run`/`query` surface. Acceptable — it mirrors `aspark-graph/server.py`'s established FastMCP pattern exactly; noted only so the NFR-5 surface diff is explicit, not silent. | accepted — user confirmed 2026-08-03; matches family precedent, no change needed |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `cli.py:60-71` (`serve` + `--repo`/`--output`), `server.py:43-47` (`run`), `test_mcp_transport.py` | ✅ met |
| AC-1.2 | `server.py:29` (`def query()` no params), `test_mcp_transport.py:101` signature assert | ✅ met |
| AC-1.3 | `query.py:26`, `test_cli_mcp_parity.py`, `test_query_core.py` | ✅ met |
| AC-1.4 | `server.py:37-40` + `store.py:53` (F1 fix), `test_mcp_errors.py` (incl. new scalar cases) | ✅ met (after F1) |
| AC-1.5 | `query.py`/`server.py` imports (no `build`/`GraphPort`), `test_boundary.py` guard + planted regression, `test_mcp_readonly.py` | ✅ met |
| AC-1.6 | `server.py:47` (`mcp.run()` stdio default), `test_mcp_transport.py` round-trip | ✅ met |
| AC-2.1–2.4 | `SECURITY.md`, `test_security_doc.py` — trust boundary, 4 non-guarantees, reporting channel, denylist all verified against code | ✅ met |
| NFR-1 | no per-call path anywhere; `query()` zero-arg | ✅ met |
| NFR-2 | build-free `query.py` seam; boundary guard bites (proven) | ✅ met |
| NFR-3 | single `except InsightsError` + F1 fix closes the scalar-JSON leak | ✅ met (after F1) |
| NFR-4 | tool `query` == CLI `query`; launched via `serve` | ✅ met |
| NFR-5 | new surface = `serve`/`run_query`/`run`/`query`; see F2/F3 | ✅ met |
| NFR-6 | stdio only, no bind/HTTP/auth in code | ✅ met |
| NFR-7 | — deferred to `/demo-day` | n/a here |
| NFR-8 | one shared `run_query` for both adapters; parity + CLI-byte-unchanged tests | ✅ met |

## 5. What Was Checked

- [x] Correctness: logic satisfies each Must AC (traced above); F1 was the one real gap, now fixed
- [x] Non-functional: NFRs 1–6, 8 and the three non-negotiables hold (raw-traceback class closed)
- [x] Error handling: only `InsightsError` caught, and now every malformed-snapshot shape maps to it
- [x] Security: no per-call path (AC-1.2), read-only by omission (boundary guard), no secrets/PII; `mcp` pin matches graph's audited range; SECURITY.md claims match code
- [x] Tests: exist, are meaningful (planted-regression guard bites; GraphPort construction refused), pass — 158 green after fix
- [x] Readability: small, boring diff; shared `run_query` makes parity structural

## 6. Verdict

This is a well-executed, honest increment: parity is structural (one `run_query` both adapters
call), read-only is grep-enforced with a planted-regression guard that genuinely bites, and
`SECURITY.md` makes falsifiable claims that all hold against the code. One real Blocker was hiding
in the shared read path — a valid-JSON-but-scalar snapshot (`5`/`null`) raised an uncaught
`TypeError`, leaking a raw traceback on the CLI and escaping the MCP tool's `except InsightsError`,
in direct violation of AC-1.4/NFR-3 and the "never a raw traceback" non-negotiable, and squarely on
the constitution's own hostile-input checklist. I fixed it at the correct narrow seam
(`require_snapshot_shape`, which only `query`/`verify` use — `diff`'s tolerance is untouched), added
parametrized regression tests on both surfaces, and re-ran the original repro to confirm both now
return `snapshot_unreadable`. With F1 fixed the code meets every Must AC and applicable NFR; F2
(minor-version bump at `/go-live`) and F3 (the `mcp` module global, matching graph precedent) remain
for the user to route. I am **not** marking this passed — that is the user's call after routing F2;
the gate is otherwise clean.

---

## ✅ REVIEW GATE

- [x] No open Blocker findings (F1 fixed and re-verified)
- [x] No open Major findings — none exist; F2 (Minor) and F3 (Nit) accepted by the user 2026-08-03, not fixes
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated (raw-traceback class closed)
- [x] All plan deviations documented and accepted (none beyond F1's fixed gap)
- [x] Test suite runs green (158 passed)
- [x] Status set to `passed`
