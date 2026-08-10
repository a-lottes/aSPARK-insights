# Plan: measurement-honesty

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/measurement-honesty/spec.md` (status `approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-04 |

## 1. Architecture Decision

- **Context:** Two QA-evidence metrics (`TRC-002`, `TRC-004-unverified-acs`) divide over a
  `verifies`-from-passing-`QACheck` evidence layer that the pinned `aspark-graph` never extracts for
  this filename convention, producing a confident fabricated `0.0`/`41-of-41`. The fix is a
  registry-wide *null-on-absent-evidence* rule (A6/C2), a bounded filesystem probe that turns "we
  can't measure this" into "here's the file we failed to parse" (C1), a top-band caveat that reaches
  the HTML reader (US-4), and a major version bump on the metrics whose contract changed (A5). Five
  implementation locations are left to this plan.

- **Decision (the five open calls):**
  1. **Evidence rule = a registration-time declaration + a shared post-computation gate in the
     build loop.** Each metric declares an `EvidenceKind` at `register(...)`; a single `gate()` in a
     new `metrics/evidence.py` runs in `build.py`'s existing metric loop *after* the metric function
     returns. If the function already returned null (`n==0`, denominator-absent) the gate is a no-op
     (AC-1.4 precedence). If it returned a value **but** the declared evidence kind is absent from
     the facts, the gate overrides to `value: null` + a composed reason, preserving `n`. A new metric
     inherits this by declaring a kind — nothing to restate (AC-1.6).
  2. **The probe = a standalone module `artifact_probe.py`**, not a `ports/` member: `ports/` holds
     seams to *sibling systems* (`GraphPort`, `PolicyPort`); this reads the repo's own `.spark/` and
     must be visibly *not* a second graph read (ADR-0, §6).
  3. **Probe return = a frozen `ArtifactProbeResult`** with three outcomes (`present`/`absent`/
     `inconclusive`), a `matched_file_count`, a sorted `matched_filenames` (subset of the built-in
     set), a `feature_dir_count`, and a **sanitized** `detail` for the inconclusive cause — counts
     and flags only, no absolute path/username (AC-3.6). Its `to_dict()` seals into provenance; its
     `disk_phrase()` supplies the reason's on-disk half.
  4. **US-5 versioning = bump the string, never register the old.** No new registry primitive: the
     five metrics whose reachable null-condition changed register only `2.0.0`; `1.0.0` is never
     registered, so `list()` already has exactly one entry per id (AC-5.2). A `deregister` primitive
     is a library-surface change with no caller — deferred (YAGNI).
  5. **The notice = a new `_render_evidence_caveat()`, separate from `_render_top_stale_cue()`**,
     reusing the `.stale-cue` CSS class for box geometry but opening with a constant `NOT COMPUTED
     —` token (AC-4.1 iv). **The trigger needs no per-metric marker and no model change:** an
     evidence-absent null is *exactly* a null with `n > 0` (the gate only overrides non-null results,
     which only exist when `n > 0`); a denominator-absent null always has `n == 0`. Render derives
     the affected set as `[m for m in metrics if m.value is None and m.n]`. This equivalence holds by
     construction for all 8 current metrics *and* is enforced for future ones by a build-loop
     invariant (see T3) — a metric function's own return is never null-with-truthy-`n`; only the gate
     may produce that shape.

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | Rule as a wrapper `registry.register` applies (decorating `fn`) | The reason's on-disk half needs the probe result, which lives in `build.py`, not at import time — the wrapper would have no probe to compose with. The build-loop gate has both facts and probe in scope. |
  | Rule restated inside each of the 8 metric functions | Violates AC-1.6 (a new metric would have to restate it) and duplicates the check 8×. |
  | Probe under `ports/` (e.g. `ports/artifacts.py`) | Reads as a third external-system seam competing with `GraphPort`; blurs the ADR-0 boundary the spec draws a line under (§6). |
  | A `reason_kind` field on `MetricValue` to mark evidence-absent nulls | Changes the model's public shape and every metric dict; the `null && n>0` discriminator (build-loop-enforced) already carries the same information with zero surface change. |
  | Seal an explicit `affected_metric_ids` list in provenance for the notice | Redundant — render reconstructs it from the sealed metrics deterministically; a second source of truth risks drift. |
  | New hue/class for the caveat block | Unverified contrast → a new `/demo-day` measurement burden (NFR-4); reusing `.stale-cue` ships contrast-safe (pre-verified ≈6.97:1/≈7.48:1, §8), distinguished by the leading label token per AC-4.1(iv). |
  | Bump only the two QA metrics | The gate is registry-wide (A6); `TRC-001`/`TRC-003`/`TRC-004-orphan-tasks` gain a *reachable* new null-condition too, so A5's "exactly the metrics whose behavior changes" is five, not two. `TRC-005-*`'s gate is a no-op (evidence == denominator) so it stays `1.0.0`. |

- **Consequences:** Easier — one gate covers every present and future metric (I6 inherits it); the
  probe is a small, pure, independently testable seam; render gains no probe dependency. Harder —
  `build.py` now depends on the probe and threads it into the metric loop; a new provenance field
  ripples into determinism, verify (AC-5.4 is now *expected*), diff, and render's key-driven rows;
  five metric versions move together and must be kept in lockstep.

## 2. Affected Components

<!-- Hand-scoped by design: the coordinator ran `aspark-graph query staleness --repo .` first and it
     returned stale: true (build.py, cli.py, store.py, ports/graph.py and others changed since the last
     graph build), so per this project's own "stale ⇒ absent" convention the impact result is not cited
     as evidence; render.py was also unknown_files (no node). The New/Changed lists below are scoped by
     reading the code directly, not from the graph. -->

- **New:** `src/aspark_insights/artifact_probe.py`, `src/aspark_insights/metrics/evidence.py`,
  `tests/test_artifact_probe.py`, `tests/test_evidence_rule.py`,
  `tests/fixtures/no_qa_graph.json` (ACs + `maps_to`/`implements` but **zero** `verifies` — the
  evidence-absent-with-`n>0` case this repo actually hits).
- **Changed:** `build.py` (run+seal probe, apply gate, enforce the null-with-`n>0` invariant),
  `metrics/registry.py` (store/expose `evidence_kind`), `metrics/traceability.py` (declare kinds,
  bump 5 versions to `2.0.0`), `model/provenance.py` (+`artifact_probe`), `render.py` (caveat +
  key-driven provenance tail), `cli.py` (`build --help` text), `__init__.py` (version bump),
  `README.md` (US-6), and the tests named per task.
- **Dependencies:** zero new runtime deps (NFR-7) — the probe uses `os`/`pathlib` from stdlib only.

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Bounded, safe, deterministic artifact probe | US-3 | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, NFR-1, NFR-2, NFR-3 | – | `done` | `probe_artifacts(repo_root)` returns a frozen `ArtifactProbeResult` (`outcome` in `present`/`absent`/`inconclusive`, `matched_file_count`, sorted `matched_filenames` ⊆ built-in `("qa.md","review.md")`, `feature_dir_count`, sanitized `detail`); descends exactly one level, follows no symlink (`scandir(follow_symlinks=False)`), reads zero bytes, sorts traversal, reads no clock/mtime; every hostile `--repo` case and `.spark`-is-a-file/symlink/unreadable case returns a result (never raises) — proven by `test_artifact_probe.py` — files: src/aspark_insights/artifact_probe.py, tests/test_artifact_probe.py |
| T2 | Seal probe into provenance + render it key-driven (walking skeleton) | US-2, US-4 | AC-2.5, AC-2.6, AC-4.6, NFR-5, NFR-8 | T1 | `done` | `Provenance` gains `artifact_probe: dict`, always present; `build_snapshot` runs the probe once from `--repo` and seals `to_dict()`; `_render_provenance` renders any top-level provenance field beyond the known scalars via a generic key-driven tail (nested dicts expanded like `graph_staleness`), so `artifact_probe` shows on **every** report and a future field cannot vanish; `render` re-reads the sealed field only (no probe) — build→render end to end, a test asserts the record renders with no `.spark/` present — files: src/aspark_insights/model/provenance.py, src/aspark_insights/build.py, src/aspark_insights/render.py, tests/test_provenance_schema.py, tests/test_render.py |
| T3 | Registry-wide null-on-absent-evidence rule + reason composition + version bump | US-1, US-2, US-5 | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.6, AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-5.1, AC-5.2 | T1, T2 | `done` | `metrics/evidence.py` defines `EvidenceKind` (`present(facts)`, `graph_phrase(facts)`, `uses_disk_probe`) and `gate(result, kind, facts, probe)`; `registry.register` takes an optional `evidence_kind` and exposes `evidence_kind(id,ver)`; `traceability.py` declares a kind on all 8 metrics and registers `TRC-001/002/003/004-orphan-tasks/004-unverified-acs` at `2.0.0` (never `1.0.0`), `TRC-005-*` unchanged at `1.0.0`; `build.py` applies `gate` in its metric loop and asserts each metric function's *own* return is never null-with-truthy-`n` (only the gate may produce that shape — keeps render's caveat discriminator exact); gate no-ops on `n==0` (AC-1.4) and on evidence-present (value/`n` byte-identical, AC-1.3), else nulls with a word-first reason (`reason[0].isdigit() is False`) naming the graph count and, for the QA kind, the probe's disk half; `list()` has exactly one entry per id; a throwaway registered metric inherits the null — files: src/aspark_insights/metrics/evidence.py, src/aspark_insights/metrics/registry.py, src/aspark_insights/metrics/traceability.py, src/aspark_insights/build.py, tests/test_evidence_rule.py, tests/test_traceability.py, tests/test_registry.py |
| T4 | Top-band evidence caveat notice | US-4 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, NFR-4 | T3 | `done` | `_render_evidence_caveat(metrics)` renders a block-level `<p>` reusing `.stale-cue` geometry, opening with `NOT COMPUTED —`, stating count-of-affected against total, then the affected `metric_id`s, then "see the Metrics table below"; triggers iff ≥1 metric has `value is None and n` (evidence-absent), never on denominator-absent nulls; placed after summary and **after** the stale cue, before `<section id="provenance">`; every string escaped via `_esc`; the affected row still shows its `Not computed:` reason (AC-4.2 untouched); a denominator-absent-all-null snapshot renders no caveat and still renders `.empty-notice`; byte-offset test asserts stale-`<p>` < caveat-`<p>` < `id="provenance"` — files: src/aspark_insights/render.py, tests/test_render.py |
| T5 | Determinism canary + dogfood integration coverage | US-1, US-3 | AC-1.5, AC-3.8, NFR-5 | T3, T4 | `done` | New `tests/fixtures/no_qa_graph.json`; the determinism canary double-builds a `tmp_path` repo with a populated `.spark/<feature>/qa.md` tree and asserts byte-identical snapshot **and** `report.html`; an integration test against this repo's real `.aspark-graph/graph.json` asserts `TRC-002`+`TRC-004-unverified-acs` are `null` (n>0) while `TRC-001`/`TRC-003`/`TRC-004-orphan-tasks`/`TRC-005-*` carry values — files: tests/test_determinism_canary.py, tests/test_graph_integration.py, tests/fixtures/no_qa_graph.json |
| T6 | CLI help, verify + diff, package version | US-5 | AC-5.3, AC-5.4, NFR-6, NFR-7 | T2, T3 | `done` | `build --help` documents that `build` also *reads* `<repo>/.spark/` for artifact presence (a read, never a write); `insights verify` against a pre-release snapshot exits 1 with `verify_mismatch` and no traceback (existing path, new test); `insights diff` across the change shows the `metric_version` change together with the value change (existing structural-diff path — add an assertion); `__version__` bumped to `0.5.0` (behavior changed) — files: src/aspark_insights/cli.py, src/aspark_insights/__init__.py, tests/test_render.py, tests/test_cli_verify.py, tests/test_cli_diff.py |
| T7 | README truth patch | US-6 | AC-6.1, AC-6.2, AC-6.3 | T6 | `done` | README status banner + family table state `v0.5.0` (== `__version__`); the "Not yet implemented — render" block and "Dashboards — planned" item are replaced by shipped reality (`render` writes `report.html`; MCP `serve` shipped); one new section documents the null-on-absent-evidence rule with a real word-first example reason, the built-in artifact filename set, and the AC-5.4 `verify_mismatch` consequence — files: README.md |

## 4. Test Strategy

- **US-1 / US-2 (evidence rule) — unit, `tests/test_evidence_rule.py` + `tests/test_traceability.py`:**
  gate no-ops at `n==0` (AC-1.4); gate overrides a non-null result to null when the kind is absent
  (AC-1.2); **byte-identical value/`n`** when the kind is present, using `trace_graph.json` (it has a
  passing `verifies` edge so `TRC-002`=0.5,n=2 must be unchanged) (AC-1.3); a throwaway metric
  registered with a kind nulls on facts lacking it (AC-1.6); the build-loop invariant rejects a
  native null-with-truthy-`n` (keeps the caveat discriminator exact); reason strings are word-first,
  name the graph count, and never contain a sibling version or an unprobed filename (AC-2.4, D7); the
  three disk outcomes yield three materially different reason strings (AC-2.1/2.2/2.3); `list()` has
  one entry per id and the five bumped ids are `2.0.0`, `TRC-005-*` still `1.0.0` (AC-5.1/5.2).
- **US-3 (probe) — unit, `tests/test_artifact_probe.py`:** the 8 hostile/edge cases as one case
  each — absent `.spark/` → `absent` exit-safe (AC-3.1); `.spark` a file / broken symlink / symlink
  → `inconclusive`, no follow (AC-3.2); unreadable dir → `inconclusive` with sanitized cause
  (AC-3.3); empty/huge/invalid-UTF-8 matched file counted, zero bytes read (AC-3.4); depth exactly
  one, `.spark/a/b/c/qa.md` not counted (AC-3.5); result has no absolute path/username/foreign
  filename (AC-3.6); paths composed only from `--repo`+built-in set, `--repo` hostile checklist
  (empty/`../`/absolute/nonexistent) never raises (AC-3.7); sorted, mtime-free traversal (AC-3.8).
- **US-4 (notice) — unit, `tests/test_render.py`:** trigger on `null && n>0`, no trigger on the
  denominator-absent all-null fresh-repo snapshot (AC-4.1 i / AC-4.3); count-first content + ids +
  pointer (AC-4.1 iii); byte-offset order stale < caveat < provenance (AC-4.1 v); `.empty-notice`
  still present in the negative case (AC-4.3); `<script>` reason escaped and page still renders
  (AC-4.4); section order + no external ref unchanged (AC-4.5); row-level `Not computed:` reason
  intact (AC-4.2). NFR-4 contrast/375px-wrap/`focusableEls==0` are **deferred to `/demo-day`** with
  `getComputedStyle` (only if `/increment` introduces a new hue — reusing `.stale-cue` is
  pre-verified in §8), per this project's "measure, don't eyeball" precedent.
- **US-5 — `tests/test_cli_verify.py` + `tests/test_cli_diff.py`:** verify against a pre-release
  snapshot → `verify_mismatch`, exit 1, no traceback (AC-5.4); `diff` shows version+value change
  (AC-5.3). `build --help` golden text for the new read (NFR-6, in `tests/test_render.py`'s CLI
  helper style).
- **Determinism (NFR-5/AC-3.8) — `tests/test_determinism_canary.py`:** double-build with a populated
  `.spark/` → byte-identical snapshot and `report.html`; the existing clock-canary half is untouched.
- **AC-1.5 dogfood — `tests/test_graph_integration.py`:** against the real pinned sibling graph
  (never mocked, per CLAUDE.md), the two QA metrics null and the rest compute.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Genericizing `_render_provenance` reorders existing rows and breaks byte-output / render tests | Medium | Keep the known scalar rows explicit and in order; append a **generic tail** only for top-level keys beyond the known set (T2), so existing output is unchanged and only `artifact_probe` (and future fields) are added. |
| A future (I6) metric hand-writes a native `null` with truthy `n`, silently mistriggering the caveat | High (wrong page) | The gate is the only *intended* producer of null-with-`n>0`; T3 adds a **build-loop invariant** asserting a metric function's own return never has that shape, so the render discriminator is enforced, not merely conventional — asserted in `test_evidence_rule.py` and guarded in `build.py`, not just documented. |
| Bumping five versions vs A5's two-metric success signal read as over-reach | Medium — **resolved** | User confirmed at the plan gate (2026-08-04): five metrics bump (`TRC-001/002/003/004-orphan-tasks/004-unverified-acs` → `2.0.0`), matching the registry-wide reading of A5/A6 — every metric wrapped by the gate gains a *reachable* new null-condition, not only the two that flip on this repo's own graph. `TRC-005-*` stays `1.0.0`. |
| Sanitized `detail` for inconclusive still leaks a path via `str(exc)` | High (NFR-3/AC-3.6) | `detail` is a curated category string built from the relative `.spark/` token + errno class only — never `str(exc)`; asserted by an AC-3.6 test that scans the whole result for `/`, `$HOME`, and the username. |
| Probe descends into a 1,000-feature `.spark/` and slows `build` | Low (NFR-1) | One-level `scandir`, no content read, no stat-for-mtime; `/demo-day` timing on a synthetic 1,000-dir tree (AC-3.5). |
| `verify` failing on old snapshots read as a regression, not the intended disclosure | Low | AC-5.4 test asserts it is `verify_mismatch` (expected); documented in README (T7/AC-6.3). |

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (or a conflict is recorded)
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user (2026-08-04)
