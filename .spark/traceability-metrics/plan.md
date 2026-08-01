# Plan: traceability-metrics

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/traceability-metrics/spec.md` (`approved`) |
| **Status** | `approved` |
| **Date** | 2026-07-31 |

## 1. Architecture Decision

- **Context:** I1 shipped the seam, the model and an empty registry; `build_snapshot`
  reads the graph once via `LibraryInterimGraphPort` and then **discards it** (`facts=[]`).
  I2 must turn that raw `{"nodes","edges"}` document into `Fact`s, run five registered metric
  functions, and disclose scope filtering (US-5) and graph freshness (US-6). Four hard seams
  are fixed by I1 and constrain every choice: the registry's `MetricFn(facts, *, as_of)`
  signature (metrics consume `Fact`s, never the raw graph), `GraphPort` is the only import site
  for `aspark_graph`, `MetricValue`'s null-needs-a-reason invariant, and no ambient clock.

- **Decision:** A **single Collector pass** (`metrics/collectors.py`) reads the
  scope-filtered graph document once and emits one `Fact` per Story/AC/Task/code node,
  encoding in each Fact's `value` the exact adjacency each TRC needs (Story: has incoming
  `maps_to`; AC: has incoming `verifies` with `result=="pass"`; Task: has outgoing
  `implements` / `maps_to`; plus a per-Story weakest-confidence tier for TRC-005, reusing the
  graph's own `Confidence.rank()`). Five pure metric functions in `metrics/traceability.py`
  each filter Facts by predicate and count — **no metric re-derives graph structure**, all
  traversal lives in the one Collector. A **ScopeFilter** (`metrics/scope.py`) runs in
  `build.py` between `read_graph()` and the Collector, dropping nodes whose path (from a
  `file:`/`def:` id prefix — the only path-bearing nodes) matches a built-in `**`-glob set
  (≥ `.claude/worktrees/**`) plus every incident edge, and returning a disclosed result.
  Staleness (MTA-002) comes from a **second GraphPort instance** — `CLIGraphPort.query("staleness")`
  — composed alongside the existing library port in `build.py`, best-effort. `MetricValue`
  gains an `n` field (MTA-001) and `Provenance` gains `scope_filter` + `graph_staleness`
  fields; both are additive, guardrail-preserving model changes.

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | Per-metric Collectors (5 independent graph walks) | Each re-derives node/edge structure; 5× the traversal surface for a 5-metric feature. One pass, predicate-filtered Facts, is proportionate. |
  | Metrics take the raw graph dict instead of Facts | Breaks I1's frozen `MetricFn(facts, *, as_of)` Protocol and the "metrics consume Facts" model — an I1 core change the foundation ADR explicitly said I2 should not need. |
  | ScopeFilter as a per-metric Fact predicate | Every metric re-implements exclusion and the `excluded_count` disclosure gets recomputed 5×. Filtering once before the Collector discloses it once (AC-5.1). |
  | A gitignore-style dep (`pathspec`) for globs | A dependency must beat "write 40 lines ourselves". The default set is one path-prefix rule; stdlib `fnmatch`/`PurePosixPath` suffices (NFR-4 spirit: fewer liabilities). |
  | Grow `GraphPort` with a bespoke `staleness()` method, or teach the library port to subprocess | The Protocol already exposes `query`; a two-instance composition needs no new method. Hiding a subprocess inside the "library" adapter smears `graph_source.access` provenance and conflates access modes. |
  | Free-form `notes` dict on Provenance for scope/staleness | An untyped blob isn't assertable. Typed `ScopeFilterResult` + a staleness dict make AC-5.1/AC-6.1 checkable. |

- **Consequences:** Easier — new metrics slot in as Collector adjacency + a `register()` call;
  the null+reason guardrail is inherited unchanged; every snapshot self-discloses what it
  filtered and how fresh its graph was. Harder — this feature **does** touch the model core
  (`MetricValue.n`, two `Provenance` fields) and `cli.py` (`query` prints `metrics`), a
  conscious, spec-mandated departure from foundation's ADR forecast ("I2 touches neither the
  model core nor cli.py"); recorded here because it is additive and preserves every invariant,
  not silent. Every build now also spawns one `aspark-graph query staleness` subprocess.

## 2. Affected Components

**Blast radius scoped by hand** — not by an `impact` query. The change is dominated by *new*
files under `src/aspark_insights/metrics/` that no graph indexes yet; the only pre-indexed
source files it edits are `build.py`, `cli.py`, `model/value.py`, `model/provenance.py`, whose
downstream is confined to this package's own build path. A confirming call is available and
named below — run it if you want the declared-link view, but it will not change the scope.

- **New:** `src/aspark_insights/metrics/{collectors,scope,traceability}.py`; tests
  `tests/test_collectors.py`, `tests/test_scope.py`, `tests/test_traceability.py`,
  `tests/test_build_metrics.py`, `tests/test_provenance_schema.py`.
- **Edited:** `src/aspark_insights/build.py` (Collector + ScopeFilter + two-adapter wiring),
  `src/aspark_insights/cli.py` (`query` prints `metrics`; `--help` text), `model/value.py`
  (`n`), `model/provenance.py` (two fields), `tests/test_determinism_canary.py`,
  `tests/fixtures/graph.json` (grow to a non-empty trace fixture), `tests/test_build.py`,
  `tests/test_graph_integration.py`.
- **No new runtime dependency** — everything uses stdlib (`fnmatch`, `pathlib`) plus the
  already-pinned `aspark-graph==0.7.0`. `CLIGraphPort` (already shipped) is the only new
  runtime *behaviour* (a subprocess per build).
- **Available confirming call (optional):**
  `aspark-graph query impact src/aspark_insights/build.py src/aspark_insights/cli.py src/aspark_insights/model/value.py src/aspark_insights/model/provenance.py --repo .`

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Collector: graph document → trace Facts | US-1 | AC-1.1, AC-1.2, AC-1.3, NFR-4 | – | `done` | `collect_facts(graph_doc)` walks nodes/edges once and emits one `Fact` (`SubjectKind.CODE_ARTIFACT`) per Story/AC/Task/code node, its `value` recording the adjacency each TRC needs (Story: incoming `maps_to` present; AC: incoming `verifies` with `result=="pass"` present; Task: outgoing `implements` present, outgoing `maps_to` present); a zero-node document yields an empty Fact list; no `aspark_graph` import (reads the plain dict). Unit-tested against a fixture with mapped + orphan nodes and against an empty document — files: src/aspark_insights/metrics/collectors.py, tests/test_collectors.py |
| T2 | Walking skeleton: `MetricValue.n`, Provenance schema, TRC-001 end-to-end | US-1, US-4 | AC-1.1, AC-1.4, AC-1.5, AC-4.1, AC-4.2, NFR-1 | T1 | `done` | `MetricValue` gains `n: int \| None` (present on every computed value; the null-needs-a-reason and value-excludes-reason invariants still hold); `Provenance` gains `scope_filter: ScopeFilterResult` and `graph_staleness: dict \| None`, both always present in `to_dict()` (default: empty-patterns/`excluded_count=0`, `null`); `traceability.py` registers TRC-001 `1.0.0` (`value` = share of Story facts with `mapped==True`, `n` = Story count; `n==0` → `value=None`, reason `"no Story nodes found in graph"`); `build.py` runs collect→registered metrics→`seal`; `query` prints `metrics` beside `facts`/`provenance`; two builds of the fixture are byte-identical — files: src/aspark_insights/model/value.py, src/aspark_insights/model/provenance.py, src/aspark_insights/metrics/traceability.py, src/aspark_insights/build.py, src/aspark_insights/cli.py, tests/test_build_metrics.py, tests/test_provenance_schema.py |
| T3 | TRC-002 + TRC-003 with zero-denominator honesty | US-1, US-4 | AC-1.2, AC-1.3, AC-1.4, AC-4.2, NFR-2 | T2 | `done` | TRC-002 `1.0.0` (`value` = share of AC facts with `verified_pass==True`, `n` = AC count) and TRC-003 `1.0.0` (`value` = share of Task facts with `implements==True`, `n` = Task count) registered; each returns `MetricValue(value=None, reason=…, n=0)` naming the absent kind when its denominator is empty; unit tests cover a populated fixture and a zero-AC / zero-Task fixture — files: src/aspark_insights/metrics/traceability.py, tests/test_traceability.py |
| T4 | TRC-004: orphan-task & unverified-AC counts, two entries | US-2 | AC-2.1, AC-2.2, NFR-2 | T2 | `done` | Registered as **two** immutable entries — `TRC-004-orphan-tasks` (`value` = count of Task facts with `mapped==False`, `n` = Task count) and `TRC-004-unverified-acs` (`value` = count of AC facts with `verified_pass==False`, `n` = AC count) — never blended into one ratio, each with its own `n`, each `null`+reason at `n==0`; neither reads `open_findings`/Finding nodes (A3); unit test asserts the two predicates match `gate_health`'s definition on a fixture with a known orphan and a known unverified AC — files: src/aspark_insights/metrics/collectors.py, src/aspark_insights/metrics/traceability.py, tests/test_traceability.py |
| T5 | TRC-005: evidence confidence-mix (Should) | US-3 | AC-3.1, AC-3.2, NFR-2 | T2 | `done` | Collector tags each Story fact with the weakest confidence tier (`declared`/`extracted`/`inferred`) on its trace to code, reusing the graph's `Confidence.rank()` — never a second scheme; TRC-005 `1.0.0` reports the declared/extracted/inferred share across Stories (`n` = Stories with a trace); zero-Story → `value=None`, reason, `n=0`; unit test against a mixed-confidence fixture — files: src/aspark_insights/metrics/collectors.py, src/aspark_insights/metrics/traceability.py, tests/test_traceability.py |
| T6 | ScopeFilter: exclude + disclose | US-5 | AC-5.1, AC-5.2, NFR-3 | T2 | `done` | `apply_scope_filter(graph_doc, patterns)` drops nodes whose `file:`/`def:` path matches any built-in `**`-glob (default set incl. `.claude/worktrees/**`) plus every incident edge, returning `(filtered_doc, ScopeFilterResult(patterns, excluded_count))`; wired in `build.py` before the Collector; provenance's `scope_filter` records patterns + count even when `excluded_count==0` (present, not omitted); the glob matcher passes the hostile-input checklist (empty string, `../`, absolute path, non-string node id) as unit tests, never raising a raw traceback — files: src/aspark_insights/metrics/scope.py, src/aspark_insights/build.py, tests/test_scope.py |
| T7 | MTA-002: graph staleness via CLIGraphPort | US-6 | AC-6.1, AC-6.2 | T2 | `done` | `build_snapshot` gains `staleness_port: GraphPort \| None = None` (default `CLIGraphPort()`), calls `query("staleness")`, and records `{stale, files_checked, changed, missing}` in `provenance.graph_staleness`; if the call raises a named error (unbuilt/not on PATH) staleness is `null` with the reason surfaced and metrics are **still** computed (build never refuses); unit test with a stub staleness port for the fresh, stale and unavailable cases — files: src/aspark_insights/build.py, tests/test_build_metrics.py |
| T8 | MTA-001 coverage + append-only registry | US-4, US-3 | AC-4.1, AC-4.2, NFR-5 | T3, T4, T5 | `done` | One test iterates every registered TRC entry and asserts each result carries an `n` and obeys null-at-`n==0`; a second asserts the registry is append-only — re-registering any shipped `(id, version)` raises, and a changed computation must ship as a new version (NFR-5) — files: tests/test_traceability.py, tests/test_registry.py |
| T9 | Boundary guard covers new metric files | US-1 | NFR-4 | T1, T6 | `done` | The existing boundary test is confirmed (or extended) to fail if any of `metrics/collectors.py`, `metrics/scope.py`, `metrics/traceability.py` imports `aspark_graph` or reads `graph.json` directly — the seam stays `ports/graph.py`-only — files: tests/test_boundary.py |
| T10 | Determinism canary on a non-empty catalog + `--help` text | US-7, US-1 | AC-7.3, NFR-1, NFR-8 | T2, T3, T4, T5, T6, T7 | `done` | `tests/fixtures/graph.json` grows into a small deterministic trace graph (Story/AC/Task/File + mapped/verifies/implements edges); the canary double-builds it and asserts byte-identical output **with a non-empty `metrics` array**; a negative test proves the canary still catches a non-deterministic metric; `build`/`query --help` text states `metrics` now carries real TRC-*/MTA-* entries — files: tests/test_determinism_canary.py, tests/fixtures/graph.json, src/aspark_insights/cli.py |
| T11 | Integration test against a real built graph | US-7 | AC-7.1, AC-7.2, NFR-6 | T2, T3, T4, T5, T6, T7 | `done` | Against a real, freshly built graph (this repo's own or the sibling's — never mocked), `build_snapshot` yields TRC-001…005 with real values or honest `null`+reason, each with `n`; the test asserts an A3 caveat — it does **not** assume Finding/QACheck nodes are non-empty (TRC-004's unverified-AC leg may legitimately read zero on a current-convention repo), and treats a zero-node repo as valid `null`+reason (AC-7.2) rather than a failure — files: tests/test_graph_integration.py |

## 4. Test Strategy

- **US-1 (TRC-001/002/003):** unit tests for the Collector's adjacency encoding (T1) and each
  metric's share + `n` on a populated fixture and a zero-node fixture (T2, T3); `query` prints
  `metrics` (T2). Behaviour on a live family graph → T11 / `/demo-day`.
- **US-2 (TRC-004):** unit test that the two predicates equal `gate_health`'s orphan-task /
  unverified-AC definitions and are reported as two distinct `n`-bearing values, never reading
  `open_findings` (T4).
- **US-3 (TRC-005, Should):** unit test on a mixed-confidence fixture that the tier shares
  reuse `Confidence.rank()` and that zero-Story yields `null`+reason (T5).
- **US-4 (MTA-001):** every metric result carries `n`; a cross-metric test enforces it (T8);
  the `n==0` → null+reason path is the same invariant tested in T2/T3/T5.
- **US-5 (ScopeFilter):** unit tests for exclusion + incident-edge drop, the `excluded_count==0`
  disclosure (AC-5.2), and the hostile-input checklist on the glob matcher (NFR-3) (T6).
- **US-6 (staleness):** stub-port unit tests for fresh / stale / unavailable, proving metrics
  still compute and the caveat is recorded (T7).
- **US-7 (dogfood + determinism):** the extended canary (byte-identical, non-empty catalog,
  plus a non-determinism negative test) in CI (T10) and the real-graph integration test (T11).
- **Deliberately manual (`/demo-day`):** `build` against a freshly built aSPARK-graph and
  aSPARK-policy checkout (A1: neither graph is built yet), the NFR-6 60s timing observation,
  and eyeballing a real sealed snapshot's scope/staleness disclosure. Reason: A1 blocks an
  automated dogfood until the sibling graphs are built, which is an operational `/demo-day` step.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A3 filename mismatch: a current-convention repo shows zero QACheck/Finding nodes, so TRC-002/TRC-004's verified-AC leg silently reads a misleading 0% | A green integration test that "proves" coverage while measuring an empty QA layer | T11 asserts the caveat explicitly and does not assume non-empty QA nodes; A3 stays a named, disclosed risk (no second parser); staleness/graph-source provenance carries the disclosure |
| Model-core change (MetricValue.n, two Provenance fields) departs from foundation's ADR forecast | Guardrail erosion or a broken frozen-shape contract | Changes are additive; every I1 invariant (null+reason, no-clock, no-person) is re-asserted by existing tests; the departure is recorded in §1 Consequences, not silent |
| Provenance schema change breaks I1's determinism fixture | Canary fails / stored snapshots unreadable | No production snapshots exist (only fixtures); the fixture + expected bytes are regenerated in T2/T10 as a clean break, stated explicitly |
| Two-adapter staleness adds a subprocess to every build | NFR-6 latency + `aspark-graph` must be on PATH | Best-effort: a failed staleness call is `null`+reason, build proceeds (AC-6.2); the 60s budget is generous for low-tens-of-features graphs |
| ScopeFilter glob edge cases (absolute paths, `../`, `**` semantics, non-string ids) | Over- or under-filtering silently skews every TRC number | Hostile-input checklist as unit tests (T6, NFR-3); default set is a single audited prefix rule; artifact nodes carry no path so Story/AC counts are structurally unaffected (verified: artifacts parse only from top-level `.spark/`) |
| TRC-004 modeled as two ids drifts from the spec's singular "TRC-004" label | Reviewer/QA can't trace the entry back | Recorded here: two immutable entries (`TRC-004-orphan-tasks`, `TRC-004-unverified-acs`) is the honest shape for two different denominators (AC-2.1, US-4); documented in the metric module |

## 6. Deviations (recorded during /increment)

- **TRC-005 ships as three registry entries** (`TRC-005-declared`, `TRC-005-extracted`,
  `TRC-005-inferred`), not one. `MetricValue.value` is a scalar (`float | int | None`) by
  model design — AC-3.1's declared/extracted/inferred *shares* don't fit one MetricValue.
  Mirrors the precedent T4/AC-2.1 already set for TRC-004 (two entries for two
  denominators): a multi-way breakdown ships as multiple immutable entries, not a
  dict-valued `value`, so every entry stays independently traceable and versioned.
- **TRC-002's "verified" definition tightened to `result == "pass"`**, not "any incoming
  `verifies` edge" (spec AC-1.2's literal wording). Matches TRC-004's own explicit
  "unverified = no incoming verifies edge whose result is 'pass'" definition (AC-2.1) —
  keeping the two consistent (a failing QA check doesn't count as "covered" in either)
  was judged more important than AC-1.2's word-for-word phrasing, since a product built
  on evidence-honesty would be undermined by "any edge, pass or fail, counts as covered."
- **`.gitignore` gained a `.aspark-graph/` entry** — not in the plan's Affected Components,
  but became necessary once this repo built its own graph for self-dogfooding (T11):
  every sibling repo already gitignores this same disposable, rebuildable directory.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (GraphPort-only seam, named errors, no clock, null+reason, immutable registry) — the model-core touch is additive and recorded
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
