# Review Report: traceability-metrics (I2)

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Diff since `86b2beb` (foundation/I1 release), `.spark/traceability-metrics/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-01 |

## 1. Scope

Reviewed the I2 diff against `86b2beb` for exactly the files in scope: new
`metrics/{collectors,scope,traceability}.py`, edits to `build.py`, `cli.py`,
`model/value.py`, `model/provenance.py`, `.gitignore`, and the 10 test files +
`tests/fixtures/trace_graph.json`. Read the spec, plan, constitution, and the
three active lens files (`cli`, `library`, `security`). Ignored
`.spark/constitution.md`, `.spark/foundation/release.md`, `CLAUDE.md`
(unrelated prior-session work). Verified by execution: `uv run pytest -v` →
**128 passed**; `uv lock --check` clean; ran the real `aspark-graph query
staleness` and inspected both `.aspark-graph/graph.json` files and the
installed `aspark_graph.model.Confidence` enum to ground the
collector/staleness scrutiny.

## 2. Plan Conformance

| Task | As planned? | Note |
|---|---|---|
| T1 Collector | ✅ | One walk, plain-dict read, no `aspark_graph` import; sorted output. |
| T2 skeleton (`n`, provenance, TRC-001) | ✅ | Invariants preserved (see §4). |
| T3 TRC-002/003 | ✅ | Zero-denominator honesty in place. |
| T4 TRC-004 (two entries) | ✅ | Two `n`-bearing entries, never `open_findings`. |
| T5 TRC-005 | ✅ | Weakest-link correct and order-independent (verified by hand). |
| T6 ScopeFilter | ✅ | Plus F2 platform-determinism fix applied. |
| T7 staleness | ✅ | Plus F1 robustness fix applied. |
| T8 MTA-001 + append-only | ✅ | Cross-metric + re-register tests real. |
| T9 boundary guard | ✅ | Real-content planted-regression test; strong. |
| T10 canary + `--help` | ✅ | Non-empty catalog canary + negative test. |
| T11 real-graph integration | ✅ | Full `build_snapshot`→real-metric path, A3 caveat asserted. |

The three deviations in plan §6 are confirmed present and sound. Deviation #2
(TRC-002 pass-only) is the *more* correct choice: it makes TRC-002
complementary to TRC-004-unverified-acs (AC-2.1's explicit pass-only
predicate) and upholds the evidence-honesty non-negotiable — a failing QA
check must not read as "covered". See F4 for the one loose end it leaves.

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Major | `build.py:51` (`_collect_staleness`) | Caught only `InsightsError`. A returncode-0-but-non-JSON stdout from the staleness subprocess raises `json.JSONDecodeError` (a `ValueError`), and a non-executable binary raises `OSError` — both escaped `build_snapshot`, becoming a raw traceback (only `InsightsError` is caught in `cli.main`). Defeats AC-6.2 ("build never refuses") and the "never a raw traceback" non-negotiable — the exact bug class (B2/F1/F5 from foundation) the security lens is active for. | **fixed** — widened the catch to `(InsightsError, OSError, ValueError)` with a comment explaining why each is needed. Re-verified: full suite green after the fix. |
| F2 | Minor | `scope.py:33` (`_matches_any`) | `fnmatch.fnmatch` case-normalizes via `os.path.normcase` — case-insensitive on macOS/Windows, case-sensitive on Linux. The same graph filtered on two platforms could drop different nodes, breaking byte-identical reproducibility (NFR-1). | **fixed** — switched to `fnmatch.fnmatchcase`. Real node ids are exact-case, so results are unchanged on real data; tests still green. |
| F3 | Minor | `build.py:1-7,25` | Module docstring ("seal an empty-metrics snapshot", "empty catalog", stale `T12` ref) and the `METRIC_REGISTRY_VERSION` comment ("the shipped registry has zero entries") flatly contradicted reality post-I2 — misleads the next reader about whether metrics run. | **fixed** — rewrote the docstring and comment to describe the current Collector→registry→seal pipeline. |
| F4 | Minor | `metrics/collectors.py:54`, spec AC-1.2 | Code implements TRC-002 as pass-only (correct, per plan §6 deviation #2), but spec **AC-1.2 still literally reads "≥1 incoming `verifies` edge"** — no pass/fail qualifier. The approved plan documents the deviation, but the spec text was never reconciled, so spec and code now silently disagree on record. | **fixed** — AC-1.2 amended to explicitly state the pass-only requirement, logged as C7 in the spec's Clarifications table (2026-08-01). No code change; the shipped behavior was already correct, only the spec text was stale. |
| F5 | Nit | `build.py:53` | `_collect_staleness` records `{"available": True, **result}`, passing through the graph's full result including extra `advice`/`changed` fields — broader than plan T7's stated `{stale, files_checked, changed, missing}`. Harmless (fully disclosed provenance), just wider than planned. | accepted as-is — user's call: more disclosed provenance is strictly more honest, not less. |

**Verified non-issues** (probed, found sound): the collector's
`nodes.get(source, {}).get("result") == "pass"` correctly handles mixed
pass/fail QAChecks on one AC and a missing QACheck node (→ unverified, no
crash); `_weakest_confidence_per_story` picks the weakest tier across *all*
(task, file) pairs via `min`, order-independently (traced by hand against a
two-task, mixed-confidence case); ScopeFilter never touches the filesystem
and its hostile-input suite exercises every risky branch, not just the happy
path; the `_CONFIDENCE_RANK[...]` KeyError path is unreachable through the
sanctioned port because the sibling graph library validates every edge's
confidence to exactly `{inferred, extracted, declared}` at construction; the
no-clock guard (`test_model_no_clock.py`) globs `model/*.py` and so
automatically covers the two new provenance fields without needing an
update; no out-of-scope creep (no CLI scope-filter flag, no sixth metric, no
threshold/gating logic).

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 / AC-1.3 | `traceability.py` (`_trc_001...`, `_trc_003...`) + `collectors.py` | ✅ met |
| AC-1.2 | `traceability.py` (`_trc_002...`), `collectors.py` | ⚠️ met-as-tightened (F4) |
| AC-1.4 / AC-4.2 | zero-denominator branches, all TRC functions | ✅ met |
| AC-1.5 | `cli.py` `_cmd_query` prints `metrics` | ✅ met |
| AC-2.1 / AC-2.2 | `traceability.py` (`_trc_004_orphan_tasks`, `_trc_004_unverified_acs`) | ✅ met |
| AC-3.1 / AC-3.2 | `collectors.py` (`_weakest_confidence_per_story`), `traceability.py` (`_trc_005_confidence_tier`) | ✅ met |
| AC-4.1 (MTA-001, `n`) | `model/value.py` (`MetricValue.n`), every metric fn | ✅ met |
| AC-5.1 / AC-5.2 | `metrics/scope.py`, `model/provenance.py` (`ScopeFilterResult`) | ✅ met |
| AC-6.1 / AC-6.2 | `build.py` (`_collect_staleness`) | ✅ met (hardened by F1) |
| AC-7.1 / AC-7.2 / AC-7.3 | `test_graph_integration.py`, `test_determinism_canary.py` | ✅ met |
| NFR-1 (determinism) | canary tests + F2 fix | ✅ met |
| NFR-2 (evidence honesty) | null+reason enforced in `model/value.py` | ✅ met |
| NFR-3 (security lens) | `test_scope.py` hostile-input suite + F1 | ✅ met |
| NFR-4 (boundary) | `test_boundary.py` planted-regression test | ✅ met |
| NFR-5 (library lens) | `test_registry.py` / `test_traceability.py` append-only test | ✅ met |
| NFR-8 (cli lens) | `cli.py` `--help` text updated | ✅ met |

Constitution non-negotiables — no person-level subject kind added,
null-needs-reason intact, and "never a raw traceback" now holds on the new
staleness path (F1 fix). None violated.

## 5. What Was Checked

- [x] Correctness: logic satisfies each AC (TRC-002 tightened but sound; F4 is a spec-text reconciliation, not a logic error)
- [x] Non-functional: NFR-1/2/3/4/5/8 hold; F2 closed a cross-platform NFR-1 gap
- [x] Error handling: F1 closed the one over-narrow exception-catching gap; build is now genuinely best-effort as specified
- [x] Security (lens): ScopeFilter/staleness inputs pass the hostile-input checklist; no secrets; no raw-traceback path left open
- [x] Tests: real — assert actual behavior, exercise the registered production functions and the full `build_snapshot` → real-graph path; suite green (128)
- [x] Readability: F3 removed the misleading stale docstring/comment

## 6. Verdict

This is a strong increment that ships real numbers with the honesty
guarantees intact: the collector is a single clean walk, the null+reason and
no-clock invariants survive the model-core touch, the boundary and
determinism guards were genuinely extended (a planted-regression test and a
non-empty-catalog canary, not decoration), and the TRC-002 pass-only
tightening is the correct, coherent reading of the spec's own AC-2.1. I found
one Major robustness gap (F1) where a non-JSON or non-executable staleness
subprocess would have leaked a raw traceback and broken a build in violation
of AC-6.2 and a non-negotiable — now fixed and re-verified green — plus two
Minor fixes (F2 cross-platform filter determinism, F3 misleading docs), all
applied directly. F4 is now closed — AC-1.2 amended to match the shipped,
reviewed behavior. F5 accepted as-is per the user's call. No open Blockers,
no open Majors, no open Minors.

---

## ✅ REVIEW GATE

- [x] No open Blocker findings
- [x] No open Major findings (F1 fixed and re-verified)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated
- [x] All plan deviations documented and accepted (§6 deviations confirmed sound; F4's spec-text reconciliation now closed via C7)
- [x] Test suite runs green (128 passed, post-fix)
- [x] Status set to `passed` — F4 resolved (AC-1.2 amended), F5 accepted as-is, both per the user's explicit decision
