# Review Report: git-native-mid-cycle-board

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Working-tree diff vs `HEAD` (3a8419a), `.spark/git-native-mid-cycle-board/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-18 |

## 1. Scope

Reviewed the entire working-tree diff attributed to this increment: the new
`src/aspark_insights/gitboard/` package (`__init__`, `gitread`, `worktype`,
`board`, `report`), the nine `tests/test_gitboard_*.py` modules, the `board`
subcommand in `cli.py`, the three new error classes in `errors.py`, `README.md`,
version bump (0.5.0→0.6.0), and the `render.py`/`test_render.py` changes. Read
enough surrounding code (`errors.py`, `store.py`, `cli.main`) to judge context.
No tool file was passed. Full suite run locally: **367 passed** (~90s), re-run
green after my two fixes. Active lenses applied: `cli`, `library`, `security`
(`ux` has no review row — informational, its pixel checks are `/demo-day`'s).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 walking skeleton | ✅ | `gitread`/`board`/CLI/import-guard test all present as specced |
| T2 hostile `--repo` | ✅ | fixed `-C` vector, empty rejected early, timeout→`GitUnavailableError`, table-driven test |
| T3 commits/N=50/privacy | ✅ | exact total + bounded shown; fmt strings carry no identity placeholder |
| T4 days-since-tag | ✅ | absent vs null-with-reason both correct; UTC-normalized |
| T5 work-type breakdown | ✅ | pure `worktype`; absent (no-tag/0-commit) decided in `board` before `breakdown` |
| T6 branches | ✅ | local refs only, age `as_of`-relative, null+reason on unreadable tip |
| T7 HTML skeleton | ✅ | block order, provenance `<dl>`, interim marker, answer sentence, stat cards |
| T8 listings + a11y | ✅ | branch `<table>`+`scope`+`caption`; commit `<dl>` 4 labels; confidence-mix; `_esc` |
| T9 determinism/integration/version/README | ✅ | real-git canary + `Co-Authored-By`/shallow integration; README `board` section |
| render.py "imported, not changed" | ❌ | **plan §2 says render.py is imported, not changed; the diff reworks the snapshot report — see F1** |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Major | `render.py:44-262`, `tests/test_render.py` | The diff bundled a full **snapshot-report scorecard rework** (`_render_metric_card`, `_render_confidence_mix`, `_render_metrics_scorecard`, `_render_metrics_full_table`, `_METRIC_META`, `_metric_percent`, `_format_share`) together with this feature's own changes, changing the output of the existing `insights render` command with no spec/plan/AC trace in this ceremony. **User routing: split into separate commits.** Executed: the scorecard rework was committed on its own (`26e7f95`, `feat: snapshot-report scorecard redesign…`, its own minor version bump 0.5.0→0.6.0) *before* this feature's commit, so `render.py` shows a **literal zero-line diff** against this commit's parent — plan §2's "imported, not changed" claim is now true as committed, not just as intended. This feature's own version becomes 0.7.0. | fixed (split) |
| F2 | Minor | `cli.py:230` | `_cmd_board`'s `--format html` branch carried a stale comment ("T7/T8 land the renderer; until then, report the gap honestly") directly above code that fully renders. Misleads the next reader. | fixed |
| F3 | Minor | `board.py:93-112` | `build_board`'s inner `try` now also catches `ValueError` alongside `GitCommandFailed`, wrapping either into `GitUnavailableError` — an exit-0 git call whose output doesn't parse (`int()` in `count_commits_since`, `datetime.fromisoformat` in `_whole_days`) can no longer escape as a raw traceback. Regression test: `test_unparseable_git_output_maps_to_named_error_not_a_traceback` (`tests/test_gitboard_security.py`). | fixed |
| F4 | Minor | `gitread.py:97-110` | `_parse_records` now peels off the first and last fields (hash/name, date — neither can contain `\x1f`) with single left/right splits, leaving the middle field (subject/tip_hash) to absorb any embedded `\x1f` byte intact instead of misaligning every field after it. Regression test: `test_subject_containing_the_field_separator_byte_does_not_misalign_fields` (`tests/test_gitboard_commits.py`). | fixed |
| F5 | Nit | `report.py:69` | Zero-commits answer sentence produced "…since v1.0.0, tagged, 6 days ago." (double comma), diverging from AC-4.8's example "…tagged 6 days ago." | fixed |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `gitread.count_commits_since`/`list_commits_since`, `board._build_commits` | ✅ met |
| AC-1.2 | `board._build_commits` (tag `None`→null+reason, exit 0) | ✅ met |
| AC-1.3 / NFR-3 | `gitread` fmt strings (no `%an/%ae/%cn/%ce/%b`); output-scan + fmt-scan tests | ✅ met |
| AC-1.4 | `gitread.ensure_git_repo`, `board.build_board`; `test_gitboard_security` (5 forms) | ✅ met |
| AC-1.5 | `gitread._run` `FileNotFoundError`→`GitUnavailableError` (distinct from AC-1.2) | ✅ met |
| AC-1.6 / NFR-5 | `canonical_json`; `_whole_days` pure `as_of`-relative; determinism canary | ✅ met |
| AC-1.7 | `report._esc` choke-point; subjects verbatim in JSON | ✅ met |
| AC-1.8 | `gitread.is_shallow` → `provenance.shallow`; real shallow-clone integration test | ✅ met |
| AC-1.9 | `board.build_board` `provenance.source="git-interim"` | ✅ met |
| AC-1.10 | `board._build_days_since_tag` (absent vs null+reason) | ✅ met |
| AC-1.12 | `worktype.breakdown` + `board._build_work_types` (absent c/d cases) | ✅ met |
| AC-2.1 / 2.2 / 2.3 | `board.build_board` (no graph/`.spark/`); AST import-guard test; `NotAGitRepoError` | ✅ met |
| AC-3.1 / 3.2 / 3.3 | `gitread.list_branches`, `board._build_branches` | ✅ met |
| AC-4.1 | `render_board_html` (no JS/external ref); test | ✅ met |
| AC-4.2 | `_render_stat_card` reuses `.metric-card--null`/`.null-value` | ✅ met |
| AC-4.3 | no red/green in stylesheet; test scans `<style>` | ✅ met |
| AC-4.4 | `run_board_report` + `--output` documented in `--help` | ✅ met |
| AC-4.5 | `_render_interim_marker` (neutral, distinct from `.stale-cue`, near top) | ✅ met |
| AC-4.6 / NFR-8 | `_render_provenance_section` `<dl>` field/value pairing, all trust fields | ✅ met |
| AC-4.7 | reuses `_STYLE` `.metric-card`/`.metric-bar`/`.confidence-*` | ✅ met (vocabulary added this cycle — see F1) |
| AC-4.8 | `_answer_sentence_text` (3 degenerate states in words, shallow qualifier) | ✅ met |
| AC-4.9 | `_render_stat_cards` absent/null/true-zero trichotomy | ✅ met |
| AC-4.10 | `_render_commits_section` scannable `<ul>`/`<li>` | ✅ met |
| AC-4.11 | `_render_work_types_section` `.confidence-mix`, fixed order, `unclassified` last | ✅ met |
| AC-4.12 | branch `<table>`+`scope`+`caption`; commit `<dl>` 4 labels; age numeric text | ✅ met |
| AC-4.13 | fixed block order, absent block omits `<h2>`; byte-offset test | ✅ met |
| NFR-1 | `cli._cmd_board` (stdout JSON / stderr named error / exit codes) | ✅ met |
| NFR-2 | `gitread._run` fixed `-C` vector, no `shell`, `cwd`-free; behavioral + source tests | ✅ met (see F4 delimiter edge) |
| NFR-4 | `MAX_COMMITS_SHOWN=50`, exact total, `truncated` disclosure | ✅ met |
| NFR-6 | zero new runtime deps; additive exports; underscore-private renames only | ✅ met |
| NFR-7 | semantic markup mechanisms present; pixel/contrast/375px deferred to `/demo-day` | ✅ structural |

Constitution §6 non-negotiables: **never person-level** — enforced at the git
seam (no identity placeholder) and confirmed by a real `Co-Authored-By`/`Signed-off-by`
integration scan of JSON *and* HTML; **never invent a number** — honest null+reason
and absent/null/true-zero trichotomy threaded consistently; **never a raw traceback**
— held for every tested path (residual latent gap noted as F3).

## 5. What Was Checked

- [x] Correctness: ACs traced to code; every Must AC has implementing code and a test
- [x] Non-functional: NFR-1/2/3/4/5/6/8 hold; NFR-7 structural (pixels → `/demo-day`)
- [x] Error handling: git failures reclassified into named errors; latent non-`InsightsError` gap flagged (F3)
- [x] Security: fixed argument vector, no shell, `_esc` choke-point, no identity/PII, hostile `--repo` matrix
- [x] Tests: exist, assert real behavior (not tautologies), run green; git never mocked
- [x] Readability: small pure seams, honest docstrings; one stale comment fixed (F2)

## 6. Verdict

The git-native board feature itself is strong, faithful work: every Must AC traces
to real code and a meaningful test, the hostile-input matrix is covered behaviorally
and by source inspection, the absent/null/true-zero trichotomy is threaded
consistently through JSON and all four HTML surfaces, the standalone proof (US-2) is
structural and enforced by an AST import-guard, and the person-level non-negotiable is
verified against a real trailer-bearing commit in both JSON and HTML. If the diff
contained only `gitboard/` plus its CLI/error/README wiring and the `_STYLE` additions,
this would pass. It does not: the same working tree bundles an unrelated, separately
"reviewed" snapshot-report scorecard rework of `render.py`/`test_render.py` that changes
the shipped `insights render` output with no spec, plan or AC trace in this ceremony
(F1) — a Major that only the user can waive or route. That, not any defect in the board
code, is why this gate returned **changes-requested**: the honest move is to split or
document the render rework before shipping, not to rubber-stamp two features under
one increment's evidence. F3/F4 were low-reachability robustness notes; F2/F5 were fixed.

**Post-review resolution:** the user chose to split (F1) and to fix F3/F4 now, rather than
waive. The scorecard rework now ships as its own commit (`26e7f95`, v0.6.0) landed *before*
this feature's commit, so `render.py` carries a literal zero-line diff in this feature's
own commit — plan §2's "imported, not changed" claim holds as committed. F3/F4 are fixed
with regression tests. Gate closes `passed`.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings
- [x] No open Major findings (F1 resolved by splitting into separate commits, `26e7f95` then this feature's commit)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated
- [x] All plan deviations documented and accepted (F1's render.py deviation resolved by the split; plan §2's claim now holds as committed)
- [x] Test suite runs green (369 passed, incl. F3/F4's new regression tests)
- [x] Status set to `passed`
