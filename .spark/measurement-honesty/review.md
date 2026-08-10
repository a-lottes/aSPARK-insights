# Review Report: measurement-honesty

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Working-tree diff vs `HEAD` (`28a5bfd`), `.spark/measurement-honesty/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-09 |

## 1. Scope

Reviewed all uncommitted changes vs `HEAD`: 5 new files (`artifact_probe.py`,
`metrics/evidence.py`, `tests/test_artifact_probe.py`, `tests/test_evidence_rule.py`,
`tests/fixtures/no_qa_graph.json`) and 14 changed files (build/render/registry/
traceability/provenance/cli/`__init__`/pyproject/README + tests). Read each source
file in full plus surrounding context (`collectors.py`, `model/value.py`, `cli.py`).

**Tool scoping:** `aspark-graph query staleness --repo .` returned `stale: true`
(advice: "run aspark-graph build"). Per the tool's Review-slice "stale ⇒ absent"
rule, `impact`/`story_trace` were treated as absent and **not** cited; the New/
Changed sets and every location below were scoped by reading the code directly,
matching plan §2's own hand-scoping note.

**Not reviewed:** the sibling `aspark-graph` parser fix (out of scope, §6); live
browser/`getComputedStyle` contrast + 375px checks (NFR-4 — deferred to `/demo-day`
per plan §4; `.stale-cue` reuse is pre-verified in spec §8).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 probe | ✅ | `probe_artifacts` → frozen `ArtifactProbeResult`; one-level, symlink-refusing, zero-byte, sorted, curated `detail`. Matches DoD exactly. |
| T2 seal+render probe | ✅ | `Provenance.artifact_probe` always present; key-driven generic tail renders it on every report; `render` re-reads sealed field only. |
| T3 gate+reason+bump | ✅ | `EvidenceKind`/`gate`; `register(...evidence_kind=...)`; 5 metrics at `2.0.0`, `TRC-005-*` at `1.0.0`; build-loop invariant via `raise AssertionError`. |
| T4 caveat | ✅ | `_render_evidence_caveat` reuses `.stale-cue`, opens `NOT COMPUTED —`, count-first + ids + pointer, after stale cue, before provenance. |
| T5 canary+dogfood | ✅ | `no_qa_graph.json` (maps_to/implements, no verifies); populated-`.spark/` double-build byte-identical snapshot+report; real dogfood integration. |
| T6 help/verify/diff/ver | ✅ | `build --help` documents the `.spark/` read; `verify_mismatch` on pre-release snapshot; diff shows version+value; `__version__`/pyproject `0.5.0`. |
| T7 README | ✅ | Status/family table `v0.5.0`; render+MCP reality; new evidence-honesty section with word-first example, filename set, `verify_mismatch`. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Nit | `metrics/evidence.py:104-110`, `render.py:161-167` | Caveat discriminator `value is None and n` assumes a gated evidence-absent null always has `n>0`. True for all 8 current metrics (non-null ⇒ `n>0`), but a *future* metric returning a computed value with `n==0` would be gated to null-with-`n==0` and silently escape the caveat — and build.py's invariant only guards the metric's *raw* return, not the gated output. Documented as an assumption in plan decision 5; no current path hits it. Worth a spec question when I6 lands. | accepted — user accepted 2026-08-09, revisit if a future metric (e.g. I6) introduces this shape |
| F2 | Nit | `render.py:222-230` | The key-driven tail renders `artifact_probe.detail` as the literal `None` on every non-inconclusive report. Honest and consistent with the "verbatim, never summarized" provenance rule, but slightly noisy. Acceptable as-is. | accepted — user accepted 2026-08-09, consistent with the verbatim-provenance convention |

No Blocker, Major, or Minor findings. Nothing fixed by the reviewer (no obvious
low-risk defect found to fix).

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1/1.2 | `evidence.py:88-110`, `traceability.py` (8 kinds) | ✅ |
| AC-1.3 | `evidence.py:100-103` (returns `result` unchanged) + `test_evidence_rule.py:72-76` | ✅ |
| AC-1.4 | `evidence.py:100` (`result.value is None` no-op) + tests | ✅ |
| AC-1.5 | `test_graph_integration.py` (real dogfood: TRC-002/004-unverified null, rest computed) | ✅ |
| AC-1.6 | `registry.py:45-46` + `test_evidence_rule.py:153-169` (throwaway metric inherits) | ✅ |
| AC-2.1/D7 | `evidence.py:74-85` (always starts "no…"); every branch word-first | ✅ |
| AC-2.2/2.3 | `artifact_probe.py:50-59` (three distinct `disk_phrase`s) | ✅ |
| AC-2.4 | reasons carry no sibling version/unprobed filename + `test_evidence_rule.py:126-133` | ✅ |
| AC-2.5/4.6 | `provenance.py:46,57`, `build.py:113`, `render.py:218-230` (key-driven) | ✅ |
| AC-2.6 | `build.py:80` (probe at build only); render/query/verify read sealed field | ✅ |
| AC-3.1-3.8 | `artifact_probe.py` fully; `test_artifact_probe.py` one case per AC | ✅ |
| AC-4.1(i-v) | `render.py:170-185,265-268`; byte-offset order test | ✅ |
| AC-4.2 | `render.py:50-61` row `Not computed:` intact + test | ✅ |
| AC-4.3 | `render.py:177-178` empty return; empty-notice carve-out test | ✅ |
| AC-4.4 | `_esc` choke-point; `NOT COMPUTED` textual label; hostile-`<script>` test | ✅ |
| AC-4.5 | no JS/external ref; fixed section order test | ✅ |
| AC-5.1/5.2 | `traceability.py` registers only `2.0.0` (never `1.0.0`) for the 5; `test_traceability.py` supersession test | ✅ |
| AC-5.3/5.4 | `test_cli_diff.py`, `test_cli_verify.py` | ✅ |
| AC-6.1/6.2/6.3 | `README.md` (version, render/MCP reality, evidence section) | ✅ |
| NFR-1/5 | one-level `scandir`, no mtime/clock; 1000-dir <1s test; populated-`.spark/` canary | ✅ |
| NFR-2/3 | symlink refusal both levels, `_os_error_category` never `str(exc)`, no-leak scan test | ✅ |
| NFR-6 (cli lens) | `build --help` documents the read; stdout stays `canonical_json`; named errors intact | ✅ |
| NFR-7 (library lens) | zero new runtime deps (stdlib only); `__version__` bumped; one new public probe fn; README note | ✅ |
| NFR-4 (ux) | block-level `<p>` in band (1), no new heading, not inside `.table-wrap`, textual label | ⚠️ partial — live contrast/375px deferred to `/demo-day` per plan; source-checkable parts hold |

## 5. What Was Checked

- [x] Correctness: gate/discriminator/reason composition traced end to end; MAPS_TO
      evidence correctly gates both TRC-001 and the inverse TRC-004-orphan-tasks
      (repo-wide zero maps_to ⇒ honest null, not a fabricated "100% orphan").
- [x] Non-functional: determinism (sorted, clock-free), NFR-6/7 lens checks.
- [x] Error handling: probe never raises; every OSError path → curated inconclusive.
- [x] Security: symlink refusal at `.spark` and file level, one-level descent, no
      path/username/home leak, hostile `--repo` never raises. `-O` cannot strip the
      build invariant (uses `raise AssertionError`, not `assert`).
- [x] Tests: 254 pass; assertions are substantive (hostile inputs, byte-offsets,
      three-distinct-reasons), not tautologies; sibling graph never mocked.
- [x] Readability: names and structure clear; probe is a standalone non-`ports` seam.

## 6. Verdict

**Pass.** This is a disciplined, honest implementation that does exactly what the
spec and plan describe and nothing more. The three concerns the caller flagged for
independent scrutiny all hold up under re-derivation: the `null && n>0` caveat
discriminator is genuinely equivalent to "the gate fired" (enforced by a `raise
AssertionError` guard that `-O` cannot strip, checked before append); the probe's
hostile-input safety is real, not asserted — symlinks are refused at both levels,
`detail` is a curated errno-class string that never touches `str(exc)`, and every
OSError subtype falls through to a path-free class name; and the key-driven
provenance tail cannot reintroduce `policy_versions` (it is in the excluded known
set) nor crash on a snapshot missing `artifact_probe`. The metric version bump is
mechanically correct (one entry per id, `1.0.0` never registered for the five),
every composed reason is word-first, and the README's example reason string matches
the code's actual output byte for byte. The two findings are Nits: one latent
future-metric assumption already documented in the plan, one cosmetic. Test suite is
green (254) against the real, unmocked dogfood graph. Ready for `/demo-day`, where
NFR-4's live contrast/375px measurements remain the only outstanding verification.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated
- [x] All plan deviations documented and accepted
- [x] Test suite runs green
- [x] Status set to `passed`
