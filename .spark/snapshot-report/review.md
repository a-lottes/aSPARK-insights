# Review Report: snapshot-report

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Uncommitted working-tree diff vs `HEAD` (`3382942`), `.spark/snapshot-report/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-04 (re-review same day) |

## 1. Scope

Reviewed: all uncommitted changes vs `HEAD` — new `src/aspark_insights/render.py`,
new `tests/test_render.py`, edits to `cli.py` (`_cmd_render` real body + `render`
subparser `--repo`/`--output`, `NotImplementedStub` import dropped) and
`tests/test_cli_stubs.py` (old stub test removed). Read surrounding context in
`query.py`, `store.py`, `model/value.py`, `cli.py` `main`. `.spark/snapshot-report/`
spec+plan reviewed but not part of the code diff. The `constitution.md` `ux`-lens
amendment is prior-approved context, not re-litigated.

Not reviewed by me directly (deferred to `/demo-day` per NFR-1/NFR-4/NFR-7): WCAG-AA
contrast of the CSS palette, real offline browser render, and the 375px no-scroll
behavior — all visual/rendered properties a source read cannot prove. I flag two
palette values below for QA to measure, not as review findings.

**Tooling:** `aspark-graph query staleness` reports `stale: true` (9 changed files,
incl. `cli.py`). Per the stale⇒absent rule I treated its `impact` signal as absent
and relied on the plan's hand-scoping — sound here: `render.py` is a new file the
graph never indexed, and `cli.py`'s only downstream is this package's own dispatch.
Full suite run locally: **189 passed** (render+stub subset: 41 passed).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `render_html` pure, `run_render` returns `.resolve()` absolute path; skeleton correct; old stub test removed. |
| T2 | ⚠️ | Top-level named errors reused correctly (AC-2.1/2.2 met). But reuse of `require_snapshot_shape` does **not** cover sub-key shape — render indexes deeper than `query`, opening a raw-traceback path `query` never had (F1). |
| T3 | ✅ | Canonical sort keys match AC-1.2; `<th scope="col">`+`<caption>`; single `_esc()` choke-point. |
| T4 | ✅ | Provenance verbatim, fixed section byte-order, two-place non-color stale cue, `<h2>` hierarchy. |
| T5 | ✅ | `n` beside value; distinct `Not computed:` null shape; styled `empty-notice` block for zero-facts. |
| T6 | ✅ | Summary is a label:value `<ul>` under `<h1>`; counts match rendered rows. |
| T7 | ✅ | XSS escaping + byte-identical determinism proven by non-vacuous tests. |
| Deviation | ✅ | `<meta viewport>` + `.table-wrap overflow-x:auto` present; regression test guards viewport meta. Credible, in-scope. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Blocker | `render.py:137` (also `:62`, `:99–102`, `:193–194`) | A snapshot that is valid JSON and passes `require_snapshot_shape` (has top-level `facts`/`metrics`/`provenance` + `provenance.as_of`) but whose entries are the wrong sub-shape — a metric dict missing `value`/`reason`/`n`, a fact missing `subject_kind`…, or `facts`/`metrics` not a list — makes `render_html` raise a raw `KeyError`/`TypeError` that escapes `main`'s `except InsightsError`, printing a **raw traceback** to stderr. Reproduced through the real CLI (metric `{"metric_id","metric_version"}` only → `KeyError: 'value'`). Violates the constitution non-negotiable "never a raw traceback … on any input," NFR-9's C2 idiom, and the §4 security hostile-input bar ("a dict missing expected keys"). `query` survives the same input (it returns the lists un-indexed); **render introduced new traceback surface**, exactly the class of bug foundation's QA found (B2/F1/F5). Fix: validate each fact/metric sub-shape (raise `SnapshotUnreadableError`) — either extend `require_snapshot_shape` or, matching the CLAUDE.md "don't over-generalize onto callers that never asked" nudge, catch `(KeyError, TypeError)` in `run_render` and re-raise as `SnapshotUnreadableError`; add a partial-shape test. | **fixed — verified (re-review)** — `run_render:227–238` wraps `render_html` in `except (AttributeError, KeyError, TypeError)`, re-raising `SnapshotUnreadableError`. I re-derived the coverage adversarially: missing sub-keys → `KeyError`; non-list/non-dict-element/non-iterable → `TypeError`; null/non-dict `provenance`·`graph_source`·`scope_filter`·`graph_staleness` → `AttributeError`; mixed-type sort keys → `TypeError`. No integer-position indexing on snapshot data (no `IndexError` path) and every value exits via `_esc(str(...))` (no `ValueError`). `query.py`/`cli.py:_cmd_query`/`_cmd_verify` never call `run_render` — untouched, confirmed. 4 new tests are non-vacuous (all assert `InsightsError`/`reason=="snapshot_unreadable"`, which the pre-fix `KeyError`/`TypeError` would fail). |
| F2 | Nit | `render.py:54` | `_render_metric_value_cell` shows a non-null `value` with **no** `n` when `n is None` — a bare value, which AC-3.1 says to avoid. Model permits `value` set with `n=None` (`MetricValue.n` defaults `None`), so this is reachable in principle. Likely never fires if every collector sets `n` for a computed value; confirm that invariant, or render an explicit `(n=?)`/`(n unavailable)` marker. | **fixed — verified (re-review)** — `render.py:59` renders `(n unavailable)` when `value is not None and n is None`. Independently confirmed all 12 `MetricValue(...)` constructions in `metrics/traceability.py` (TRC-001..005, computed and null branches) pass `n` explicitly — claim holds. New test `test_render.py:355–361` asserts `"42 (n unavailable)"` present and `"<td>42</td>"` absent, which the pre-fix bare-value output would fail. |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `render.py:219–226`, `cli.py:142–144` | ✅ (absolute path via `.resolve()`, tested) |
| AC-1.2 | `render.py:41–47,84–117,192–194` | ✅ (sort keys match; no rows dropped) |
| AC-1.3 | `render.py:156–189` | ✅ (verbatim; `graph_staleness` keys deterministically sorted) |
| AC-1.4 | `render.py:149–153,177–179` | ✅ (two textual non-color STALE cues) |
| AC-1.5 | `render.py:20–33,198–216` | ✅ (no external ref; scan test) |
| AC-1.6 | `render.py:198–216` | ✅ (h1→summary→stale→provenance→metrics→facts) |
| AC-2.1 | `query.py:21–23`, `cli.py:117–119` | ✅ (`no_snapshot`, empty stdout, exit 1) |
| AC-2.2 | `store.py:49–63` | ✅ for top-level shape; see F1 for the sub-shape gap |
| AC-3.1 | `render.py:49–56` | ⚠️ met except F2 `n=None` edge |
| AC-3.2 | `render.py:56` | ✅ (`Not computed:`, distinct shape) |
| AC-3.3 | `render.py:84–94` | ✅ (styled empty-notice; all-null fixture test) |
| AC-4.1 | `render.py:36–38` + all call sites | ✅ (single `_esc`, every dynamic value routed; hostile tests) |
| AC-4.2 | `test_render.py:399–404` | ✅ (hostile input renders, exit 0) |
| AC-5.1/5.2 | `render.py:136–146` | ✅ (distinct figures; counts match rows) |
| NFR-2 | `render.py:36–38` | ✅ (choke-point holds; no bypass found, incl. `object`-typed `fact["value"]`) |
| NFR-3 | `render.py:18,223` | ✅ (fixed `report.html`; no new flag) |
| NFR-4 | `render.py:20–33,72–116,181–185` | ✅ structurally; contrast → QA |
| NFR-5 | `render.py:192–216` | ✅ (pure, no clock/nonce; byte-identical tests) |
| NFR-7 | `render.py:24,203` | ✅ structurally; 375px → QA |
| NFR-9 | `cli.py:75–86,142–144` | ⚠️ met except F1 (raw traceback path) |
| NFR-10 | `render.py` exports | ✅ (`render_html`/`run_render` public; helpers `_`-prefixed; `REPORT_FILENAME` an intentional constant; zero new deps) |

## 5. What Was Checked

- [x] Correctness: every Must AC traced to code; sort keys, section order, path, stale cue verified against AC text
- [x] Non-functional: NFR-2/3/4/5/7/9/10 traced; contrast/375px correctly deferred to `/demo-day`
- [x] Error handling: F1 — a wrong-sub-shape snapshot escapes as a raw traceback (Blocker)
- [x] Security: XSS choke-point read line-by-line, no bypass incl. `object`-typed `fact["value"]`; write path fixed; no secrets
- [x] Tests: exist, non-vacuous (XSS/determinism/sort spot-checked); gap — no partial-sub-shape test (F1)
- [x] Readability: house shape followed; helpers small and named; constitution non-negotiable "never invent/reformat a number" upheld (raw value shown, no `%` transform)

## 6. Verdict

This is careful, well-tested work that lands nearly every load-bearing claim: the
single `_esc()` XSS choke-point genuinely has no bypass I could find (including the
`object`-typed `fact["value"]`, which is stringified-then-escaped), the canonical
sorts and section order match the AC text byte-for-byte, the absolute-path trap the
plan flagged was actually avoided, determinism is structural and proven, and the
design-review guidance (null shape, distinct-figure summary, styled empty-state,
`th scope`/`caption`/`h2` hierarchy, viewport+table-wrap) all landed, not just the
AC letter. It does **not** pass as-is: F1 is a real Blocker — a snapshot that is
valid JSON and passes `require_snapshot_shape` but carries a wrong sub-shape entry
(a metric missing `value`, a non-list `facts`) makes `render_html` emit a raw
traceback, reproduced through the live CLI. That breaks a named constitution
non-negotiable and is exactly the malformed-input class this project's own QA has
been bitten by before; `query` tolerates the same input, so render regressed the
guarantee rather than inheriting it. Fix F1 (and settle the F2 `n=None` edge),
add the missing partial-shape test, and this is ready to re-review. Recommendation:
back to `/increment`.

### 6.1 Re-review verdict (2026-08-04)

Both fixes hold. F1's `except (AttributeError, KeyError, TypeError)` in `run_render`
genuinely closes the raw-traceback hole: I re-derived the exception every malformed
sub-shape produces rather than trusting the annotation, and each one lands in the
three caught classes — missing keys are `KeyError`, non-list/non-dict-element/
non-iterable `facts`·`metrics` and mixed-type sort keys are `TypeError`, and null or
non-dict `provenance`/`graph_source`/`scope_filter`/`graph_staleness` are
`AttributeError`. I tried to route around it (list-of-non-dicts, `None` elements,
int `metric_id`, null `provenance`, non-dict `graph_staleness`) and could not: there
is no integer-position indexing on snapshot data (so no `IndexError`) and every
value exits through `_esc(str(...))` (so no `ValueError`); the only non-raising
malformed inputs degrade gracefully to an empty sub-table, never a traceback. The
fix is correctly scoped — `query`/`verify` do not call `run_render` and are
untouched, matching the CLAUDE.md "don't over-generalize onto callers that never
asked" nudge. The 4 F1 tests and 1 F2 test are non-vacuous and would fail if the
respective fix were reverted. F2's `(n unavailable)` fallback is real, and I
confirmed the "every `MetricValue` passes `n`" claim against all 12 constructions in
`traceability.py` myself. Full suite re-run: **194 passed** (189 + 5), fully green.
No new findings. Nothing in the narrow diff touched the first-pass verifications
(XSS choke-point, deterministic sorts, absolute path, offline output, section order,
viewport/table-wrap). No open Blocker or Major remains; per this ceremony's rule I
do not set `passed` myself — this is ready for the user to close the gate.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings — **F1 fixed and re-verified (re-review 2026-08-04)**
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — **"never a raw traceback" now upheld; F1 close re-derived, not taken on faith**
- [x] All plan deviations documented and accepted
- [x] Test suite runs green (**194 passed**; +4 F1 partial-shape tests, +1 F2 `n=None` test, all non-vacuous)
- [x] Status set to `passed` by the user (2026-08-04)
