# Review Report: foundation

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | The full new package (no prior commit to diff), `.spark/foundation/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-07-30 (re-review round 2 after fix-mode) |

## 1. Scope

Reviewed every new file (no git history — whole tree is "the diff"): all of
`src/aspark_insights/`, all of `tests/`, `.github/workflows/ci.yml`,
`pyproject.toml`, `uv.lock`, `.gitignore`, `.python-version`, `README.md`.
Verified by execution, not by trusting the increment: `uv run pytest` → **50
passed** (incl. the real-`aspark-graph` integration test, which *ran* not
skipped), `uv lock --check` → exit 0. No tool file was passed; reviewed by
reading and by probing failure paths directly. Not reviewed: the sibling
`aSPARK-graph` repo internals (out of scope, exercised only as a dependency).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 Scaffold | ✅ | pyproject facts, path source, gitignore all as specced. |
| T2 canonical JSON + errors | ✅ | Byte-stable; named errors carry `reason`. |
| T3 Model guardrails | ✅ | Enum + `__post_init__` invariants sound (see §4). |
| T4 Registry | ✅ | Explicit `register()`, zero shipped entries, order stable. |
| T5 GraphPort | ✅ | Pin-check via `importlib.metadata`, raises before any read. |
| T6 build skeleton | ✅ | Empty-metrics sealed snapshot, byte-identical double build. |
| T7 Boundary guard | ✅ | F3 fixed: hyphen pattern added + synthetic-violation test (verified). |
| T8 PolicyPort | ✅ | Deviation (wired into build.py) reasonable, matches DoD. |
| T9 CLI help/render/query | ✅ | F1 fixed; F5 fixed — `query` now guards wrong-shape input via `require_snapshot_shape` before indexing (verified). |
| T10 diff | ✅ | F1 fixed and verified; safe on wrong-shape input (uses `.get`) — left untouched by design, correctly (see §6). |
| T11 verify | ✅ | F1 fixed; F5 fixed — `verify <non-snapshot.json>` now emits a named error, exit 1, no traceback (verified). |
| T12 Canary | ✅ | F2 fixed: negative canary now builds two real Snapshots and byte-compares `canonical_json` (verified). |
| T13 Integration | ✅ | Runs against real pinned sibling, not a skip (C4 met). |

Both §6 deviations (PolicyPort wired into `build.py`; CLI errors surfaced as
`canonical_json(exc.to_dict())`) are disclosed, in-scope, and sound.

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Major | `cli.py:81,91,122` (via `store.py:30`) | `query` (corrupt file), `diff` (missing file), `verify` (missing file) let `FileNotFoundError`/`JSONDecodeError` escape past `main()`'s `except InsightsError`, printing a **raw traceback** to stderr — violates NFR-3 ("never a raw traceback") and cli.py's own docstring promise. Confirmed by running each. `build`'s error path is correctly protected; these three are not. Fix: wrap the read/parse in `read_snapshot_dict` (or each handler) to raise a named `InsightsError` (e.g. `reason="snapshot_unreadable"`), caught by the existing handler. | **fixed** — added `SnapshotUnreadableError` (`errors.py`); `store.read_snapshot_dict` now catches `OSError`/`JSONDecodeError` and raises it; `_cmd_verify` reordered so the protected read happens before the raw `path.read_text()`. Regression tests added: `test_store.py` (2), `test_cli_diff.py`, `test_cli_verify.py`, `test_cli_stubs.py` — all assert exit 1, `snapshot_unreadable` in stderr, and no `"Traceback"` substring. |
| F2 | Major | `tests/test_determinism_canary.py:52` | AC-7.2's negative canary asserts a monkeypatched `time.time()` returns `1000≠2000` — it never builds a snapshot nor byte-compares `canonical_json`, so it does **not** exercise the substrate it claims to validate ("the canary itself is tested to catch this regression class"). It is a near-tautology bundled under the same AC as the real double-build test. Mitigant: AC-7.1's positive canary *does* byte-compare the real pipeline, so a clock read in `build.py` **would** be caught. Fix: build two snapshots carrying a clock-derived `MetricValue` and assert their `canonical_json` bytes differ, or add a metric-injection seam and run the real canary against it. | **fixed** — rewrote the test to build two real `Snapshot.seal(...)` objects (same `Provenance`, same `as_of`) whose only difference is a clock-derived `MetricValue`, then asserts `canonical_json(snapshot.to_dict())` differs between them — now exercises the actual serialization substrate the CI canary byte-compares. |
| F3 | Minor | `tests/test_boundary.py:12-15` | Guard catches `aspark_graph` (underscore) imports and the `graph.json` path, but not a hyphen-form `subprocess.run(["aspark-graph", …])` bypassing `CLIGraphPort` outside `ports/graph.py`. AC-2.4 as written (imports/internals) is met; this is a residual blind spot, not a live violation. Fix: add a pattern for the `"aspark-graph"` string used outside the port, or note the gap in the test. | **fixed** — added a bare `aspark-graph` regex pattern; extracted `_find_offenders()` and added `test_guard_catches_a_hyphen_form_bypass`, which plants a synthetic violation in a temp tree and asserts the guard flags it. |
| F4 | Nit | `cli.py:63-64` | `parser.error(...)` branch is unreachable (`add_subparsers(required=True)` rejects unknown commands first). Harmless defensive dead code. | accepted as-is (user decision) |
| F5 | Major | `cli.py:87` (query), `cli.py:129` (verify) | The F1 fix guarded *read/parse* but the handlers still indexed the parsed dict directly — `data["facts"]` / `stored_data["provenance"]["as_of"]` — so a valid-JSON-but-wrong-shape file (`insights verify package.json`, or `{}` in the store for `query`) raised a raw `KeyError` traceback, the same NFR-3 non-negotiable F1 defends. Fix: validate required keys after `read_snapshot_dict` and raise `SnapshotUnreadableError`. | **fixed** — added `store.require_snapshot_shape(data, path)` (`store.py:43`) checking `facts`/`metrics`/`provenance` present and `provenance.as_of` present; raises `SnapshotUnreadableError`. Called in `_cmd_query` (`cli.py:87`) and `_cmd_verify` (`cli.py:129`) *before* any indexing — order verified by read. Kept a **separate** function, not folded into `read_snapshot_dict`, so `diff`'s deliberate `.get()` tolerance is untouched — reviewer confirms that scoping is correct (§6). Regression tests: `test_store.py` (both branches + positive), `test_cli_stubs.py::test_query_on_wrong_shape_json_...` (`{}` store), `test_cli_verify.py::test_verify_wrong_shape_json_...` (package.json shape) — all subprocess-level, assert exit 1, `snapshot_unreadable`, no `"Traceback"`. Re-verified by re-running the exact repros (empty `{}`, package.json shape, and partial shape missing `as_of`): all three → named error, exit 1, no traceback. | **fixed** |

No Blockers. No security findings (local CLI, no PII, no network/auth surface —
NFR-8 N/A holds). No out-of-scope creep: registry ships zero entries (asserted),
`render` is a loud stub, PolicyPort stays null.

**Fix-mode summary (2026-07-30):** F1, F2, F3, F5 all fixed and re-verified by
re-execution; F4 accepted as-is per user decision. No open findings remain.

**Re-review (2026-07-30):** Re-verified by re-execution, not by trusting the
diff. F1's three named scenarios (`verify does-not-exist.json`, `diff a-missing.json
b-missing.json`, corrupt-JSON store for `query`) now all emit a named
`snapshot_unreadable` error, exit 1, no traceback — confirmed by running each. F2's
rewritten negative canary genuinely builds two real `Snapshot.seal(...)` objects and
byte-compares `canonical_json(to_dict())` — real substrate, not hollow. F3's guard
flags a planted hyphen-form violation via `_find_offenders()`. `SnapshotUnreadableError`
fits the taxonomy cleanly; the `_cmd_verify` reorder is sound (happy path green).
Full suite `uv run pytest -v` → **56 passed** (re-run here, not taken on faith);
`uv lock --check` → exit 0. **New finding F5** surfaced during the light pass:
the fix closed the read/parse traceback but left the handler-side `KeyError` path
open, so NFR-3 is still breached on a wrong-shape valid-JSON file. Gate stays
`changes-requested` on F5.

**Re-review round 2 (2026-07-30):** F5's fix read and re-executed, not trusted.
`require_snapshot_shape` (`store.py:43`) is called *before* any direct indexing in
both handlers — `_cmd_query` (`cli.py:87` before `data["facts"]` at :88) and
`_cmd_verify` (`cli.py:129` before `stored_data["provenance"]["as_of"]` at :131) —
order confirmed by read. Re-ran the exact repros: `insights verify` on a
`package.json`-shaped file and on a partial file missing `as_of`, and `insights query`
against a `{}` store — all three now emit a named `snapshot_unreadable` error, exit 1,
no traceback (the partial case exercises the second, `as_of` branch). New tests are
subprocess-level and non-tautological (assert exit 1, `snapshot_unreadable`, absence of
`"Traceback"`); store tests cover both reject branches and the positive case. Keeping
`require_snapshot_shape` as a separate function rather than folding it into
`read_snapshot_dict` is the right call — it preserves `diff`'s deliberate `.get()`
tolerance, and `diff` never emits a traceback anyway (NFR-3 not in play for it), so
leaving `diff` untouched is correct, not an oversight. F4 dead-code branch
(`cli.py:68-69`) is unchanged — still present, still `pragma: no cover`, neither
"fixed" nor reintroduced as a live path. Full suite `uv run pytest -v` → **60 passed**
(re-run here); `uv lock --check` → exit 0. All findings resolved; gate flips to `passed`.

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1/1.2/1.3 | `pyproject.toml`, `test_packaging.py` | ✅ met |
| AC-2.1 | `ports/graph.py:88`, integration test | ✅ met |
| AC-2.2 | `ports/graph.py:52-70` (`_check_version` before read/import) | ✅ met |
| AC-2.3 | `build.py:40` (`access=port.access_mode`) | ✅ met |
| AC-2.4 | `test_boundary.py` | ✅ met (F3 fixed) |
| AC-3.1/3.2 | `ports/policy.py`, `build.py:33-34` | ✅ met |
| AC-4.1 | `model/fact.py:16-19` (no person member) | ✅ met |
| AC-4.2 | `model/value.py:20-30` (both invariants; `value=0` allowed) | ✅ met |
| AC-4.3 | `model/provenance.py`, `build.py` (all fields passed in) | ✅ met |
| AC-4.4 | `test_build.py`, canary | ✅ met |
| AC-5.1/5.2/5.3 | `metrics/registry.py`, `test_registry.py` | ✅ met |
| AC-6.1/6.2/6.5 | `cli.py`, `test_cli_stubs.py`, `test_build.py` | ✅ met |
| AC-6.3 | `cli.py:82-89` | ✅ met (F5 fixed — wrong-shape input now named-errors) |
| AC-6.4 | `cli.py:126-140` | ✅ met (F5 fixed — wrong-shape input now named-errors) |
| AC-7.1 | `test_determinism_canary.py:39` | ✅ met |
| AC-7.2 | `test_determinism_canary.py:55` | ✅ met (F2 fixed — now byte-compares real snapshots) |
| NFR-1 | canary + `verify` | ✅ met |
| NFR-2 | `test_boundary.py` | ✅ met (F3 fixed) |
| NFR-3 | `serialization.py`, `errors.py`, `cli.py`, `store.py` | ✅ met — sort_keys ✅; F1 (missing/invalid-JSON) and F5 (wrong-shape) both fixed; no CLI path now emits a raw traceback (re-verified across all repros) |
| NFR-4 | `model/fact.py`, `model/value.py` | ✅ met |
| NFR-5 | `model/provenance.py` (complete provenance) | ✅ met |
| NFR-6/7/8 | — | ✅ N/A as specced |

Note (not a finding): `Fact.subject_id` is free-form `str`; the person-level
guardrail is enforced at the *kind* level (AC-4.1's scope), which is airtight.
A future metric could still put `"author:alice"` in `subject_id` — worth a
convention note for I2, but structurally out of AC-4.1's remit.

## 5. What Was Checked

- [x] Correctness: guardrails read directly — `MetricValue.__post_init__` refuses
      null-without-reason and value-with-reason; `value=0` correctly allowed;
      `SubjectKind` has no person member; pin-check fires before any graph read.
- [x] Non-functional: NFR-3 now fully met — F1 and F5 both fixed; no CLI path emits a raw traceback.
- [x] Error handling: build/diff/query/verify all clean; F1 and F5 fixed and re-verified by
      running each scenario (missing, corrupt, and wrong-shape valid-JSON inputs).
- [x] Security: no secrets, no injection surface, no PII; N/A holds.
- [x] Tests: real subprocess CLI tests (not mocked internals); integration runs
      against real sibling; canary byte-compares real snapshots on both halves (F2 fixed).
      F1/F3/F5 regression tests read and confirmed non-tautological. Suite re-run: 60 passed.
- [x] Readability: small, boring, well-commented; next dev will follow it.

## 6. Verdict

This passes. Across three rounds every finding was worked and each fix verified by
re-execution, never by trusting the diff. F1's named read/parse failures, F2's
formerly-hollow negative canary (now byte-comparing two real `Snapshot.seal(...)`
objects), and F3's boundary guard (hyphen-form pattern plus a planted-violation test)
were all confirmed in the prior pass and remain green. This round closed F5, the last
open finding: `require_snapshot_shape` (`store.py:43`) validates `facts`/`metrics`/
`provenance` and `provenance.as_of`, and is called in both `_cmd_query` and
`_cmd_verify` *before* any direct indexing — order I confirmed by read, not inferred.
I re-ran the exact repros that produced tracebacks last time — `verify` on a
`package.json`-shaped file, `verify` on a partial file missing `as_of`, and `query`
against a `{}` store — and all three now emit a named `snapshot_unreadable` error,
exit 1, no traceback, so NFR-3's "never a raw traceback" non-negotiable holds on every
CLI path. Keeping the check as a separate function rather than folding it into
`read_snapshot_dict` is the correct call on its own merits: `diff` uses `.get()`
throughout and can never raise `KeyError`, so it never violates NFR-3, and its
tolerance of partial input is a defensible deliberate design — leaving `diff` untouched
is right, not an oversight. F4's unreachable `parser.error` branch stays accepted per
the user's decision and was neither silently "fixed" nor reintroduced as a live issue.
Full suite is 60 green and `uv lock --check` is clean, both re-run here. No open
findings, no waivers needed. Ship it to QA.

**Fix-mode round 2 (2026-07-30):** F5 fixed — added `require_snapshot_shape()`
(`store.py`), a validation step centralized as its *own* function rather than
folded into `read_snapshot_dict`, so `diff`'s existing `.get()`-based tolerance
is untouched (a design choice, made deliberately per the finding's own framing).
Called from `_cmd_query` and `_cmd_verify` right after `read_snapshot_dict`.
Regression tests added: `test_store.py` (2), `test_cli_stubs.py::test_query_on_wrong_shape_json_...`,
`test_cli_verify.py::test_verify_wrong_shape_json_...` (using a `package.json`-shaped
file, mirroring the reviewer's own example). Manually re-reproduced the reviewer's
exact repro (`insights verify /tmp/.../package.json`) — now exits 1 with
`snapshot_unreadable`, no traceback. Full suite: 60 passed (up from 56);
`uv lock --check` clean.

---

## ✅ REVIEW GATE

- [x] No open Blocker findings
- [x] No open Major findings (F1/F2/F3/F5 all fixed & re-verified; F4 nit accepted by user)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated
      (NFR-3 "never a raw traceback" now holds on every CLI path — F5 fixed)
- [x] All plan deviations documented and accepted
- [x] Test suite runs green (60 passed, re-run this pass; the F5 wrong-shape path now has coverage)
- [x] Status set to `passed`
