# Plan: foundation

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/foundation/spec.md` (`approved`) |
| **Status** | `approved` |
| **Date** | 2026-07-29 |

## 1. Architecture Decision

- **Context:** Empty, not-yet-`git init`-ed repo, 4th product in the aSPARK family.
  The spec fixes the non-negotiables (graph/insights boundary ADR-0, no ambient clock
  ADR-4, no person-level subjects, no invented numbers) and wants them *structural* before
  any real metric exists. The sibling `aspark-graph` (v0.7.0) lives locally with a clean
  Python API (`Graph.load(path).to_dict()` → canonical `nodes`/`edges`) and a C2 CLI
  (`query <name>`, JSON on stdout `sort_keys`, exit 1 + stderr on unbuilt graph). It ships
  **no `export` query yet** (G6 unshipped), so a library import is the only bulk read path.

- **Decision:** Boring family stack — Python ≥3.11, `uv`, `hatchling`, stdlib `argparse`,
  `pytest`, committed `uv.lock`. One `src/aspark_insights/` package. Siblings are reachable
  **only** through `ports/`: `GraphPort` (a `typing.Protocol`) with two concrete adapters —
  an interim library adapter (`import aspark_graph`, version-pinned, sunset = graph G6) and
  a CLI adapter (subprocess) — and `PolicyPort` with an inert null adapter. The core model is
  frozen dataclasses + enums that make the guardrails **unconstructible to violate**: a
  `SubjectKind` enum with no person member (AC-4.1), a `MetricValue` whose `value=None`
  path requires a non-empty `reason` (AC-4.2), a `Provenance` whose fields are all passed
  in — no clock read anywhere (AC-4.3). Metrics are a tiny `MetricRegistry` of pure
  `(facts, as_of?) → MetricValue` functions, keyed by `(id, version)`, shipping **zero**
  entries. The CLI wires `build|query|render|diff|verify` in the C2 idiom via one
  `canonical_json()` + named-error module. Determinism is proven by a CI canary (double
  build, byte-compare) against a **frozen fixture** `graph.json` + a **fixed `as_of`**.
  `aspark-graph` is a **path dependency** (`[tool.uv.sources]`) pinned `==0.7.0`; the interim
  adapter re-checks the pin at runtime via `importlib.metadata.version("aspark-graph")` and
  refuses on mismatch (AC-2.2).

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | Parse `.aspark-graph/graph.json` directly | Anti-corruption violation (NFR-2/AC-2.4), no expiry, breaks silently on format change. The library adapter behind a port with a sunset condition is the spec's explicit choice. |
  | Wait for graph's `export` query (G6) as the bulk path | Not shipped; would block I1 on a sibling change the spec deliberately routes around via the interim adapter. |
  | Pin-check via `aspark_graph.__version__` | **It is stale — reports `0.1.0` while packaging metadata is `0.7.0`.** Would pass a wrong-version import. Must use `importlib.metadata.version`. |
  | ABC base classes for ports | Heavier than a 2-method seam needs; `Protocol` gives the same contract without an inheritance ceremony. Boundary is enforced by CI grep (AC-2.4), not by the type mechanism. |
  | Document "don't emit person metrics" / "null needs a reason" as convention | A convention is a guess later grandfathered around. Enum-without-a-member and a constructor invariant make the violation *not typeable* — the point of doing this at foundation. |
  | Import-time `@metric` decorators for registration | Hides side effects at import; conflicts with "no I/O reachable from a metric" (AC-5.2). Explicit `register()` keeps the derivation path inspectable. |
  | `git` / PyPI dependency on `aspark-graph` | Not published; repo isn't even `git init`-ed. A `uv` path source + committed `uv.lock` is the reproducible local choice; runtime pin-check is the real guard. |

- **Consequences:** Easier — I2 adds registry functions and Collectors touching neither
  `ports/`, the model core, nor `cli.py`'s wiring; the guardrails cannot be bypassed by a
  careless metric; every snapshot self-documents its graph-access mode so the interim
  coupling's expiry stays visible. Harder — a real installed `aspark-graph` is required for
  the integration test (C4), so CI must install the sibling; the version pin is a small
  maintenance touchpoint each time the graph bumps.

## 2. Affected Components

No blast-radius query was run: `aspark-graph` is not built for this repo and the repo is
empty, so scope is **forward-looking design**, grounded by hand in the two architecture docs
and the sibling's actual API — not an analysis of existing code.

New files, all under `src/aspark_insights/`: `ports/graph.py`, `ports/policy.py`,
`model/{fact,value,provenance,snapshot}.py`, `metrics/registry.py`, `serialization.py`,
`errors.py`, `store.py`, `build.py`, `cli.py`; `tests/`; `tests/fixtures/graph.json`;
`.github/workflows/ci.yml`; `pyproject.toml`, `uv.lock`, `.gitignore`.

New dependencies (each a liability, justified):
- **`aspark-graph==0.7.0`** (runtime, path source) — the interim adapter's reason to exist;
  C4 mandates validation against a real pinned install, so a vendored stub is not an option.
- **`pytest`** (dev) — family standard; no runtime cost.
- No other runtime dependency: everything else is stdlib (`argparse`, `json`, `dataclasses`,
  `enum`, `importlib.metadata`, `subprocess`).

`.gitignore` ignores `.aspark-insights/` (derived, deletable) but **not** `.spark/` — Q1 is
resolved: `.spark/` is git-tracked and public.

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Package scaffold on the family stack | US-1 | AC-1.1, AC-1.2, AC-1.3 | – | `done` | `uv sync` resolves from committed lock (`uv lock --check` exits 0); `import aspark_insights` and its `ports`/`model`/`metrics`/`cli` submodules import clean; `pyproject.toml` has `requires-python>=3.11`, `hatchling` backend, `aspark-graph==0.7.0` with a `[tool.uv.sources]` path entry; `.aspark-insights/` gitignored, `.spark/` not — a test asserts the pyproject facts — files: pyproject.toml, uv.lock, .gitignore, src/aspark_insights/__init__.py, src/aspark_insights/ports/__init__.py, src/aspark_insights/model/__init__.py, src/aspark_insights/metrics/__init__.py, src/aspark_insights/cli.py, tests/test_packaging.py |
| T2 | Canonical JSON + named errors | US-6 | NFR-3 | T1 | `done` | `canonical_json(obj)` emits `sort_keys=True`, `ensure_ascii=False`, fixed indent, trailing newline (byte-stable); `errors.py` defines named error types (`GraphNotBuiltError`, `GraphVersionMismatchError`, `PolicyUnavailable`, `NotImplementedStub`, `VerifyMismatchError`) each carrying a machine-readable `reason`; a test proves same input ⇒ identical bytes — files: src/aspark_insights/serialization.py, src/aspark_insights/errors.py, tests/test_serialization.py |
| T3 | Core model with structural guardrails | US-4 | AC-4.1, AC-4.2, AC-4.3, NFR-4, NFR-5 | T1 | `done` | `SubjectKind` enum contains only system/feature/code-artifact members — a test enumerates it and asserts no person-level member exists; `MetricValue` with `value=None` and empty/absent `reason` raises at construction, a value-present case forbids a reason; `Provenance` requires `as_of`, `insights_version`, `metric_registry_version`, `graph_source(access, sealed)`, `policy_versions` all as args; `Snapshot.seal(...)` composes them; a grep test asserts no `datetime`/`time` import in `model/` — files: src/aspark_insights/model/fact.py, src/aspark_insights/model/value.py, src/aspark_insights/model/provenance.py, src/aspark_insights/model/snapshot.py, tests/test_model.py, tests/test_model_no_clock.py |
| T4 | Metric registry mechanism (zero entries) | US-5 | AC-5.1, AC-5.2, AC-5.3 | T1, T3 | `done` | `MetricRegistry.register(id, version, fn)` then lookup by `(id, version)` and `list()` in `sort_keys` order; a test registers a pure `(facts, as_of)->MetricValue` fn and exercises it; the **shipped** registry is empty and a test asserts zero catalog entries; registered fn signature exposes only `Fact`s and optional `as_of` — files: src/aspark_insights/metrics/registry.py, tests/test_registry.py |
| T5 | GraphPort: interim library + CLI adapters | US-2 | AC-2.1, AC-2.2, AC-2.3 | T1, T2, T3 | `done` | `GraphPort` Protocol; library adapter reads the whole doc via `aspark_graph.Graph.load(...).to_dict()` and matches canonical `nodes`/`edges`; version guard uses `importlib.metadata.version("aspark-graph")` vs a pinned `"0.7.0"` constant and raises `GraphVersionMismatchError` on mismatch (unit test monkeypatches the reported version); CLI adapter subprocesses `aspark-graph query <name>` and returns parsed JSON, raising `GraphNotBuiltError` on exit 1 instead of crashing; both surface `graph_source.access` (`"library-interim"` / CLI equivalent); the library adapter file header names graph G6 as its sunset condition — files: src/aspark_insights/ports/graph.py, tests/test_graph_port.py |
| T6 | Walking skeleton — `insights build --as-of` end to end | US-6 | AC-6.2, AC-4.4, NFR-1, NFR-5 | T2, T3, T4, T5 | `done` | `insights build --as-of <date>` reads the graph via GraphPort, builds an **empty-metrics** snapshot with sealed provenance, writes it under `.aspark-insights/`, and prints `canonical_json` to stdout; a missing/unbuilt graph writes a named error to stderr and exits 1 (no traceback); building the fixture twice with the same `as_of` yields byte-identical files — files: src/aspark_insights/build.py, src/aspark_insights/store.py, src/aspark_insights/cli.py, tests/test_build.py |
| T7 | GraphPort boundary CI guard | US-2 | AC-2.4, NFR-2 | T5 | `done` | A test greps the tree and fails if any file outside `ports/graph.py` reads `.aspark-graph/graph.json` or imports `aspark_graph`; wired into CI so `/peer-review` inherits it — files: tests/test_boundary.py |
| T8 | PolicyPort null adapter | US-3 | AC-3.1, AC-3.2 | T1, T2, T3 | `done` | `PolicyPort` Protocol + null adapter returns a well-formed "unavailable" result (never raises, never fabricates) naming the missing resolver; a snapshot built through it records `policy_versions` explicitly `null` (present, not omitted) — files: src/aspark_insights/ports/policy.py, tests/test_policy_port.py |
| T9 | CLI: help, `render` stub, `query` readback | US-6 | AC-6.1, AC-6.5, NFR-3 | T6 | `done` | `build|query|render|diff|verify --help` each print usage and exit 0; `render` exits 1 with a named `not_implemented` error (never silent empty output); `query` reads back raw stored Facts/Provenance from the last snapshot as `sort_keys` JSON (never a metric value) — golden-output tests assert stdout and exit codes — files: src/aspark_insights/cli.py, tests/test_cli_stubs.py |
| T10 | CLI: `diff <a> <b>` | US-6 | AC-6.3 | T6 | `done` | Prints a structural JSON diff of changed facts/provenance fields, exit 0; a snapshot diffed against itself yields an empty diff — golden-output test — files: src/aspark_insights/cli.py, tests/test_cli_diff.py |
| T11 | CLI: `verify <snapshot>` | US-6 | AC-6.4 | T6 | `done` | Recomputes the build from the snapshot's own recorded inputs, reports (JSON, exit 0) whether the recompute byte-matches the stored file, and exits 1 with `VerifyMismatchError` if not — test covers both a matching and a tampered snapshot — files: src/aspark_insights/cli.py, tests/test_cli_verify.py |
| T12 | Determinism canary + CI workflow + fixture | US-7 | AC-7.1, AC-7.2, NFR-1 | T6, T4 | `done` | A frozen `tests/fixtures/graph.json` + a fixed `as_of` constant drive two independent `insights build` runs whose outputs must be byte-identical (fails CI on any diff); a negative test registers a test-double fn calling `datetime.now()` and proves the canary **detectably fails** against it; CI workflow runs the canary, the boundary guard, `uv lock --check`, and the suite — files: tests/test_determinism_canary.py, tests/fixtures/graph.json, .github/workflows/ci.yml |
| T13 | Integration test vs real installed `aspark-graph` | US-2 | AC-2.1, AC-2.2 | T5 | `done` | Against a real pinned `aspark-graph` install, one bulk document read (library adapter) matches the graph's own canonical `nodes`/`edges`, and one CLI query returns the contract JSON; an unbuilt graph raises the named error — CI installs the sibling so this runs, not skips (C4) — files: tests/test_graph_integration.py |

## 4. Test Strategy

- **US-1:** `uv lock --check` in CI (AC-1.1); import smoke test (AC-1.2); pyproject assertion
  test (AC-1.3).
- **US-2:** unit tests against the frozen fixture for the library adapter and version-mismatch
  path; CLI-adapter test for the built/unbuilt cases; the **boundary grep** test (AC-2.4); the
  **integration** test against a real installed sibling for the riskiest coupling (C4/AC-2.1/2.2).
- **US-3 (Should):** unit test that the null adapter returns "unavailable" without raising and
  that provenance carries `policy_versions: null`.
- **US-4:** unit tests for the enum-has-no-person invariant, the null-without-reason
  construction failure, and full `Provenance`; a grep test forbids a clock import in `model/`;
  byte-identical double build (AC-4.4) is the canary's job too. Snapshot self-documentation
  (NFR-5) inspected live at `/demo-day`.
- **US-5:** unit tests for register/lookup/ordered-list and a pure test-only fn; an assertion
  that the shipped registry is empty (guards scope creep, C2/AC-5.3).
- **US-6:** golden-output CLI tests for every subcommand — help exit 0, build JSON `sort_keys`,
  diff self ⇒ empty, verify match/mismatch, `render` → `not_implemented`, `query` readback
  (NFR-3). Behaviour against a real family-repo graph is left to `/demo-day`.
- **US-7:** the canary itself is a test (double build byte-compare) **and** is proven to catch
  the regression class via the ambient-clock negative test (AC-7.2), run in CI on every commit.

Deliberately manual (`/demo-day`): inspecting a real sealed snapshot for self-documentation
(NFR-5) and running `build` against an actual freshly-built family-repo graph — the fixture
covers determinism, but a live graph is the honest end-to-end demo.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `aspark-graph` version drift — and `__version__` is stale (`0.1.0`) vs metadata `0.7.0` | Adapter reads a wrong-shaped graph, or falsely passes/fails the pin | Pin `==0.7.0`; check via `importlib.metadata.version`, never `__version__`; named `GraphVersionMismatchError`; `uv lock --check` in CI (T5, T1) |
| Scope creep into real metrics during I1 | Guardrail-first intent lost; a KPI ships unreviewed | Registry ships zero entries; a test asserts an empty catalog; only a test-only fn exercises the mechanism (T4) |
| Hidden `datetime.now()` in the derivation path | Non-deterministic snapshots; the exact failure ADR-4 exists to prevent | Canary + AC-7.2 negative test + grep-no-clock test in `model/` (T12, T3) |
| Interim library adapter outlives graph G6 | Permanent anti-corruption violation | `graph_source.access="library-interim"` in every snapshot; adapter header names G6 as sunset (T5) |
| Path dependency not reproducible off this machine | CI/other devs can't install the sibling; T13 silently skips | `uv` path source + committed `uv.lock`; CI installs `aspark-graph` explicitly so T13 runs, not skips (T13) |
| Fixture graph drifts or is unstable (A2) | Canary flaky or meaningless | Fixture is a **static** committed `graph.json` + a **fixed** `as_of` constant, captured once — never a live repo (T12) |

## 6. Deviations (recorded during /increment)

- **T8** wired `PolicyPort`'s null adapter into `build.py` (not listed among T8's files). The
  task's own DoD said "a snapshot built **through it** records `policy_versions` explicitly
  null" — satisfying that literally meant `build_snapshot()` calling `NullPolicyPort.resolve()`
  rather than merely hardcoding `None`. Small, in scope of US-3/AC-3.2, no architecture change.
- **CLI error surfacing** (T9 onward) prints the full `{"error": ..., "message": ...}` object to
  stderr (via `canonical_json(exc.to_dict())`), not just the human message. The plan's task DoDs
  said "a named error to stderr" without specifying shape; this reading was chosen to make
  NFR-3's "machine-readable named error" concrete and directly assertable in tests, rather than
  relying on substring-matching a prose message.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (or a conflict is recorded) — no constitution exists; family ADR-0/ADR-4 conventions honoured
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
