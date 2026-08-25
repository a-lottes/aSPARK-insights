# Review Report: release-metrics

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Uncommitted working-tree diff against `HEAD` (`1af5b5a`), `.spark/release-metrics/plan.md` |
| **Rounds** | 2 — original pass 2026-08-24, adversarial re-review of the fix round 2026-08-24 |
| **Status** | `passed` |
| **Date** | 2026-08-24 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report — including `/increment` in fix-mode, which is not this
     report's owner — updates it in the same edit that closes or re-rules a finding:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed` (header table authoritative for `Status`) — set at re-review, after every
  fix from the `/increment` fix-mode round was re-verified adversarially with the reviewer's own
  fresh fixtures rather than the developer's repros. `/demo-day` may start.
- **Verdict (current, re-review):** All three Major honest-null leaks (`F1`-`F3`) are genuinely
  closed, not merely patched — each survives fixture shapes the developer never tested, and each
  regression test provably fails when its fix is reverted. Two new low-severity findings surfaced
  *from the fix round itself* (`F14`, `F15`); both fixed by the reviewer in this pass.
- **Open:** `0 open` — 15 findings total. `F1`-`F3`, `F7`-`F13` fixed in `/increment` fix-mode and
  re-verified here; `F5`, `F6` fixed by the reviewer in round 1; `F14`, `F15` fixed by the reviewer
  in round 2; `F4` **waived by the user** (spec-level, follow-up tracked). Full suite green:
  665 (round 1) → 677 (post-fix-mode, re-run by the reviewer) → **679** (after the reviewer's
  round-2 fixes, which add 2 tests).
- **Binding ruling:** §3 Findings + the REVIEW GATE at the foot of this report.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a finding at the next `/peer-review` and proceed — don't stop on it.

## 1. Scope

Reviewed: the full working-tree diff against `HEAD` (`git diff HEAD` + `git status --short`) —
`releasemap.py` (+241), `releaseboard_report.py` (+258), new `scopecount.py`, `cli.py` help text,
version `0.10.0`→`0.11.0` (`__init__.py`, `pyproject.toml`, `uv.lock`), `README.md`, and all
8 new / 2 modified test files. Read in context: `board.py`, `worktype.py`, `gitread.py`,
`artifactstatus.py`, `artifactcontent.py`.

Verified by execution, not by reading: full suite (665 passed, twice — before and after my fixes);
a real `insights releases --format json` run against this repo; six purpose-built hostile/edge
fixture repos (partial-unreadable scope, unreadable mid-history tag date, all-zero gaps, 0/1/2/3
tags, a two-release feature, `<script>`-named and `'onload=`-named tags); a 21-case hostile
`spec.md` matrix against `read_scope_counts`; a HEAD-vs-working-tree performance and git-call
baseline via `git worktree`.

Not reviewed: live-browser measurements (`getComputedStyle`, 375 px `scrollWidth`, accessibility
tree, network-disabled load) — those are `/demo-day`'s, per plan §4. CSS contrast was checked from
the source tokens instead, and passes with margin (see §4/NFR-4).

**Re-review scope (round 2, 2026-08-24).** Verified by execution, adversarially, with fixtures
built from scratch rather than the developer's repros: `read_scope_counts` across 4998/4999/**5000**/
5001/5002/6789/50 000-line specs, including a 5000-line file whose *final* line is a `### US-N`
heading and a no-trailing-newline variant (F3); `_render_release_figures` across 7 delivering/
unreadable combinations plus asymmetric (`us` set, `acs` null), unicode, 300-char and 25-member
name sets (F1); `_render_cadence_strip` across 22 gap chains — unreadable gap first/middle/last,
scattered, **fully** unreadable (the `gap_max is None` path), 2/3/4-way ties, all-zero, zero-mixed
and negative gaps (F2/F7); a 0.10.0-shaped payload through `run_release_board_report` (F10). Each
fix was additionally **mutation-tested**: the fix reverted in `src/`, the cited regression test
re-run, and confirmed to go red. A live `insights releases --format html` run on this repo renders
byte-identically before and after the reviewer's round-2 edits.

**Tooling note.** `aspark-graph query staleness --repo .` returned `stale: true` with a non-empty
`changed` list, so per the tool's own rule (*stale ⇒ absent*) I treated the graph as unavailable,
cited no graph result as evidence, and scoped by hand from the diff plus the module reads listed
above. No `impact` or `story_trace` result informed any finding below.

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `_members_and_unattributed` widened to a 3-tuple (`releasemap.py:102`); `date`/`commit_count` at `:406-419`. Commit counts on this repo measured `[1,2,4,3,2,2,4,1,3,2]` — matches AC-1.2 exactly. |
| T2 | ✅ | `_release_work_types` (`:278`) mirrors `board._build_work_types`'s absent-key rule; +1 git call/release confirmed by my own counter (176→186 calls). |
| T3 | ✅ | Contract holds across 21 hostile inputs; the 5 000-line bound now refuses by name (**F3** fixed, re-verified at 4998/4999/5000/5001/50 000). **F5** fixed. |
| T4 | ✅ | JSON side exactly as planned; the DoD's "with `n` and that member named" now reaches HTML on both card and band (**F1** fixed, re-verified across 7 fresh combinations). |
| T5 | ✅ | Independently confirmed: `_document_plan`, `_display_order`, `_pseudo_stats_line`, `_work_types_clause` are **byte-identical** to `HEAD` (AST source-segment comparison). Renderer only reads `member["delivery"]`; computes no attribution. |
| T6 | ✅ | `figures` matches AC-3.1 on every value except `first_date` — see **F4**. |
| T7 | ✅ | Real `<dl>`, one `<h1>`, heading levels 1-4 only, no external fetch (one inline `data:` logo). |
| T8 | ✅ | One class, one hue — C8/NFR-5 genuinely honored. Null gaps now render as rows with their reason (**F2**) and ties/zeros no longer read "longest" (**F7**); both re-verified across 22 gap chains. |
| T9 | ✅ | Re-verified with my own hostile tags (`<script>alert(1)</script>` and `'onload=alert(2)`): no unescaped payload, no `alert` inside any HTML tag, exit 0. |
| T10 | ✅ | Single call site at `:645`; v0.6.0's real card shows all four AC-4.3 elements simultaneously. |
| T11 | ⚠️ | Version/help/README correct. NFR-8 disclosed but not met — **F4**, waived by the user. Plan's spec-gate note corrected (**F13**). |

**Disclosed deviations, independently verified rather than accepted:**
1. **UTC vs `%cs` for `v0.1.0`** — real and correctly bounded. I compared `%cs` against `%cI` for
   all 10 tags: `v0.1.0` is the *only* commit landing before 02:00 local in a `+02:00` offset, so
   it is genuinely the sole divergence, not a convenient carve-out. The UTC rule at
   `releasemap.py:274` is byte-for-byte the same normalization `board._whole_days:36` already
   ships. The T1 test still asserts blanket `%cs` equality for the other nine, so a second
   divergence would fire red. Accepted as a rule — but see **F4** for what is not disclosed.
2. **NFR-8 ~12.3 s** — attribution is accurate. My `git worktree` baseline: HEAD code 10.32 s /
   176 git calls; working tree 11.91 s / 186 calls. Directly instrumented, this feature's own
   additions are `tag_commit_date` 0.64 s over 11 calls and `read_scope_counts` 0.031 s over 18
   calls. So ~0.6 s is this feature's and ~10.3 s predates it — the plan's claim holds. The bar
   is still not met (**F4**).

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Major | `releaseboard_report.py:612-615` (also band, `:755-758`) | A release card's "Delivered scope" prints `scope["us"]/["acs"]` and drops `scope["n"]` and `scope["unreadable"]`. Fixture: release with delivering `alpha` (readable) + `beta` (no US heading) renders `Delivering: alpha, beta` / `Delivered scope: 1 US / 1 ACs` — an understated total presented as complete, on the very surface US-4 exists to make legible. Violates AC-3.6 ("never a silent zero folded into ... the total") and T4's own DoD ("with `n` and that member named"); the JSON carries both, the HTML discards them. Fix: render `… (n=1 of 2 delivering)` and append the `unreadable` names, mirroring the band's existing `Scope unreadable for: …` note; add the band's own `n` too. | **fixed** — per-release header now appends `(n=N of M delivering)` plus `; unreadable: <names>`; a new `figures.delivered_scope_n` field (computed once in `_build_figures`, ADR-0) drives the same disclosure on the band's "Delivered scope" label. Regression-pinned: `test_partial_unreadable_delivering_scope_discloses_n_and_names_unreadable`, `test_band_partial_unreadable_scope_shows_n_of_features_delivered` (`tests/test_releaseboard_figures.py`). **Re-review: holds.** My own fixtures (3-delivering-1-unreadable, 4-delivering-2-unreadable+1-trailing, all-unreadable, zero-delivering, asymmetric `us`-set/`acs`-null, unicode and 300-char names) all disclose `n` + the names on **both** card and band; `0 US / 0 ACs (n=0 of 0 delivering)` stays honestly distinct from the all-unreadable reason string; hostile names stay `_esc`-ed. Both regression tests go red when the fix is reverted. |
| F2 | Major | `releaseboard_report.py:793`, `:803` | `rows_data` filters out every release whose `gap_days` is `null`, with no row, no note and no `n` in the present state. Fixture (5 tags, one unreadable date): 4 real gaps, 2 unmeasurable → the strip renders **2 rows silently** and marks `5 d (longest)`, though the true longest is unknown. Violates AC-3.4 (one unreadable input shows `null`+reason, everything else still renders) and AC-3.7 (the present state shows *every* gap). Fix: emit a row per gap with the number cell carrying `gap_days_reason` and no bar; state measured-vs-total `n` in the caption; suppress the "longest" mark whenever any gap is unmeasured. | **fixed** — `_render_cadence_strip` rewritten to iterate every gap slot (`real[1:]`), not just measured ones; an unmeasured slot renders its `gap_days_reason` with no bar; caption states `(N of M measured)` when partial; "longest" is suppressed unless every gap is known. Regression-pinned: `test_unreadable_gap_renders_as_a_row_with_reason_not_silently_dropped`, `test_unreadable_gap_row_has_no_bar` (`tests/test_releaseboard_cadence.py`). **Re-review: holds.** Unreadable gap in first / middle / last / scattered positions all render a row with their reason and no bar, and suppress `longest`. The **fully** unreadable chain (every gap null, `gap_max is None`) renders sanely — all rows carry reasons, caption reads `(0 of N measured)`, nothing raises. Regression tests go red when reverted. |
| F3 | Major | `scopecount.py:70` | `lines[:_MAX_LINES_SCANNED]` truncates silently. A 20 001-line `spec.md` returns `{"us": 1, "acs": 4999, "reason": None}` — a wrong number with no reason, which constitution §6 ("Never invent a number") and AC-3.6 ("never an estimated count") both forbid outright. The bound itself is right; the silence is the defect. Not reachable on today's specs (largest real: 597 lines), which is why this is Major and not a Blocker. Fix: `if len(lines) > _MAX_LINES_SCANNED: return null + "spec.md exceeds 5000 lines; scope not counted"`. | **fixed** — exactly this guard added. Regression-pinned: `test_file_past_line_bound_returns_null_with_reason_not_a_truncated_count`, `test_file_exactly_at_line_bound_is_still_counted_normally` (`tests/test_scopecount.py`). **Re-review: holds.** My own oversized fixtures (5001/5002/6789/50 000 lines) all refuse by name; **exactly 5000** still counts normally, including when the 5000th line is itself a `### US-N` heading and when the file has no trailing newline. The refusal correctly wins over the `no US heading found` path. Test goes red when the guard is disabled. |
| F4 | Major | `.spark/release-metrics/spec.md` NFR-8, AC-1.1, AC-3.1 | Two approved Must-level statements the shipped code does not satisfy, both honestly disclosed in plan.md but never reconciled with the spec. (a) NFR-8 promises `--format html` under **5 s**; measured 13.6 s end to end (11.9 s in `build_release_map`), ~0.6 s of which is this feature's. (b) AC-3.1 states the span starts `2026-07-31`; the band renders `2026-07-30`, and AC-1.1's `%cs` verification is false for `v0.1.0`. Nothing on the page or in README tells a reader dates are UTC calendar dates, so the off-by-one against `git log` is unexplained. Fix: EM/PO amends NFR-8 (or opens a follow-up for `_members_and_unattributed`'s pre-existing 1+F cost) and AC-1.1/AC-3.1's literal values; developer adds a one-line UTC note beside the date figures. **A Major cannot be waived by any agent — only the user.** | **waived by user, 2026-08-24** — reason: both underlying facts (the 5 s bar, the UTC-normalized date) were already independently verified as accurate and honestly disclosed in `plan.md`; the shortfall's cause (`_members_and_unattributed`'s pre-existing cost) is out of this feature's scope to fix; the mismatch is between the spec's literal wording and measured reality, not a code defect. Waived to unblock `/demo-day` rather than block QA on a spec-wording gap; spec amendment (NFR-8, AC-1.1, AC-3.1 wording, and a one-line UTC note on the page) tracked as a follow-up, not done in this pass. |
| F5 | Minor | `scopecount.py:47-58` | `path.is_file()` was unguarded: an over-long path raised `OSError [Errno 63]` straight through, breaking the function's own documented "never raises" contract and turning one unreadable spec into a whole-report `SparkDirUnreadableError` instead of AC-3.6's `null`+reason. This is the exact escape hatch `artifactcontent.py:91-97` already documents from its own re-review. Wrapped in `try/except (OSError, ValueError)`; also widened the `read_text` guard, with `UnicodeDecodeError` (a `ValueError` subclass) reordered first so its specific reason is not swallowed. Re-verified on the original repro and the full 21-case matrix. | fixed |
| F6 | Nit | `releaseboard_report.py:525-527` | The unreadable-date branch of `_real_stats_line` did not terminate its sentence: `"tag commit date could not be read 1 commit."` Added the period. | fixed |
| F7 | Minor | `releaseboard_report.py:803` | `gap == gap_max` marks *every* tied row "longest". A 4-tag repo with all tags cut on one day renders three rows of `<strong>0 d (longest)</strong>` — noise that also defeats AC-3.2's "the longest gap is identifiable as such". Fix: skip the mark when `gap_max == 0` or when more than one gap ties; if kept for ties, word it "joint longest". | **fixed** — "longest" now shown only when every gap is known, there is exactly one maximum, and it is `> 0` (folded into the same F2 rewrite, since both touch the same loop). Regression-pinned: `test_tied_maximum_gaps_are_not_both_marked_longest`, `test_all_zero_gaps_are_not_marked_longest`, `test_single_unambiguous_maximum_still_gets_marked` (`tests/test_releaseboard_cadence.py`). **Re-review: holds.** 2-, 3- and 4-way ties all suppress the mark; all-zero suppresses; `[0,0,3]` and `[0,1]` correctly still mark the single positive maximum; all-negative chains (out-of-order tag dates) suppress and clamp bar width to 0% rather than emitting a negative width. Never more than one `longest` in any of 22 chains. |
| F8 | Minor | `releaseboard_report.py:617-618` | `wt_display` re-parses `_work_types_clause`'s prose by slicing `len("Work types: ")` off it, and maps *both* "key absent (zero-commit range)" and "`worktype.breakdown` returned an honest null" to the generic `"not classifiable for this range"`, discarding breakdown's own specific reason (`"2 of 5 commits carry a recognized Conventional Commit type; too few…"`). Weakens NFR-5's "non-empty, *specific* reason" and is brittle to any wording change upstream. Fix: read `release.get("work_types")` directly and print its `reason` when `value is None`. | **fixed** — extracted shared `_work_types_value(release)`, called directly by `_render_release_figures`; `_work_types_clause` now builds its sentence on top of the same helper instead of the reverse. Preserved by the existing `test_pseudo_release_work_types_*` suite plus `test_real_release_work_types_present_when_set`. **Re-review: behavior holds, coverage claim did not** — see **F15**. The specific-reason path is genuinely fixed (my fixture's `"2 of 5 commits carry a recognized Conventional Commit type…"` reaches the card verbatim, and an absent key still falls back correctly), but reverting the fix left all 677 tests green, so the cited tests never covered it. |
| F9 | Minor | `artifactcontent.py:4-10`; `releasemap.py:1-11` | Two module docstrings are now stale in a way that matters: `artifactcontent.py` still states the body-parsing ban is "a load-bearing promise **for the JSON path** (`build_release_map()`)", but `scopecount` now parses `spec.md` body headings/checkbox lines on that exact path; `releasemap.py`'s header still describes the map as status-only. The next developer will believe a promise that no longer holds. Fix: one-line amendment in each naming `scopecount` as the deliberate, plan-recorded exception. | **fixed** — both docstrings amended: `artifactcontent.py` now scopes its "load-bearing promise" claim to `artifactstatus.py` specifically and names `scopecount.py` as the separate, narrow, plan-recorded exception on the JSON path; `releasemap.py`'s header now lists the release-metrics fields it added. **Re-review: holds** — both docstrings read accurately against the code they describe; `build_release_map` still never imports `artifactcontent`. |
| F10 | Minor | `releaseboard_report.py:855` vs `:741` | `data['figures']` is a hard index in the non-empty branch while `_render_figures_band` uses `data.get("figures")`. `render_release_board_html` is a non-underscore, importable function whose accepted input shape narrowed (now requires `figures`, per-release `date`/`commit_count`/`delivered_scope`, per-member `delivery`/`scope`) across a **MINOR** bump — a `library`-lens semver concern. Mitigated: `run_release_board_report:892` wraps `KeyError` into `ReleaseMapUnreadableError`, so no traceback escapes. Fix: use `.get` consistently and state the same-version requirement in the docstring. | **fixed (documentation)** — the one remaining hard `data['figures']` index was removed as a side effect of F2's rewrite (`_render_cadence_strip` no longer takes `figures` at all). `render_release_board_html`'s docstring now states the `0.11.0` input-shape narrowing explicitly and points to `run_release_board_report` for callers wanting a named error instead of a raw exception — the existing safety net was already correct, so this is disclosure, not a behavior change. **Re-review: holds** — `data['figures']` is gone; the only remaining hard index is the pre-existing `data['releases']`. Verified end-to-end: five malformed/0.10.0-shaped payloads through `run_release_board_report` all raise `ReleaseMapUnreadableError`, never a raw traceback. |
| F11 | Nit | `releasemap.py:320-330`; `releaseboard_report.py:759` | `_median` always returns `float`, so an integral median renders `2.0 d` where AC-3.1 says `2 d`. Fix: format integral medians without the decimal (keep the JSON value a number). | **fixed** — display-only formatting in `_render_figures_band`; the underlying `float` in the JSON payload (`figures.gap_median`) is untouched. Regression-pinned: `test_integral_median_displays_without_trailing_decimal`, `test_fractional_median_still_displays_with_decimal` (`tests/test_releaseboard_figures.py`). **Re-review: holds** — `3.0`→`3 d`, `0.0`→`0 d`, `3.5` preserved. |
| F12 | Nit | `releaseboard_report.py:541`, `:614`, `:757` | `"1 ACs"` — no singular form, while commit counts correctly say `1 commit`. Fix: reuse the same pluralization idiom. | **fixed** — new shared `_scope_text(us, acs)` helper used at all three sites. Regression-pinned: `test_singular_ac_count_reads_ac_not_acs` (`tests/test_releaseboard_figures.py`). **Re-review: holds** — `1 AC` singular at all three sites; no `1 ACs` anywhere in the live render. |
| F13 | Nit | `plan.md:238-240` | The "Inherited spec-gate note" claims the spec's SPEC GATE has one unchecked clarify-pass box. All ten boxes in `spec.md`'s SPEC GATE are checked. Stale note; remove or correct it. | **fixed** — `plan.md`'s note corrected in place (not deleted) to record what happened: the checkbox was fixed before `/increment` started, but this note wasn't updated to match at the time. **Re-review: holds** — all 10 SPEC GATE boxes in `spec.md` counted checked, 0 unchecked. |
| F14 | Nit | `releaseboard_report.py:849-856` (as fixed) | **New, introduced by F2's fix.** The small-sample refusal read `Not enough measured gaps to show a cadence strip (n=1)`, but since F2's rewrite `n` counts gap *slots*, not measured gaps — with exactly 2 tags and one unreadable tag date it claimed `n=1` measured while **zero** were. A number overstating measurement on the one surface AC-3.3 governs. Fix: name what `n` counts. | **fixed by reviewer** — now `Not enough release-to-release gaps to show a cadence strip (n=N)`, accurate in both sub-cases. Both existing `n`-naming tests still pass; the live render is byte-identical (this branch is unreachable on a 10-tag repo). |
| F15 | Nit | `tests/test_releaseboard_figures.py` (F8's cited coverage) | **New, found by mutation-testing the fix round.** F8's §3 row claimed its fix was "preserved by the existing `test_pseudo_release_work_types_*` suite plus `test_real_release_work_types_present_when_set`" — but every one of those tests exercises only the *real-mix* or *absent-key* path. Replacing `wt["reason"]` with the generic string left all 677 tests green, so the specific-reason path F8 was actually raised about was unpinned, and the report asserted coverage that did not exist. Fix: pin the path; correct the claim. | **fixed by reviewer** — added `test_null_work_types_shows_breakdowns_own_specific_reason_not_a_generic_one` and `test_absent_work_types_key_still_falls_back_to_the_generic_reason`; both go red under their respective mutations. F8's row above corrected. Suite 677 → 679. |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `releasemap.py:260-276` (`_release_date`) | ⚠️ partial — correct UTC rule, but `%cs` equality fails for `v0.1.0` (F4) |
| AC-1.2 | `releasemap.py:112`, `:411` | ✅ met — measured `[1,2,4,3,2,2,4,1,3,2]` on this repo |
| AC-1.3 | `releasemap.py:278-289` | ✅ met — key absent on empty range, verified against a direct `worktype.breakdown()` call |
| AC-1.4 | `releasemap.py:268-276`; report `:522-527` | ✅ met — verified with a monkeypatched unreadable date; release still lists every other figure |
| AC-1.5 | report `:640-646` | ✅ met — pseudo-release card and stats line **byte-identical** to `HEAD`'s render; pseudo JSON subtree byte-identical |
| AC-2.1 | `releasemap.py:158-188` | ✅ met — machine-readable `delivery` field; renderer only reads it |
| AC-2.2 | verified on real repo | ✅ met — v0.6.0: 0 delivering, `measurement-honesty` trailing, `delivered_in: v0.5.0` |
| AC-2.3 | `releasemap.py:190-218` | ✅ met — v0.9.0 = 3/13, v0.3.0 = 7/24, v0.5.0 = 6/33 |
| AC-2.4 | `releasemap.py:176-181` | ✅ met — fixture feature first seen in the open window: `delivering:false`, `delivered_in:null`, named reason, zero contribution |
| AC-2.5 | report `:252` (unchanged) + `releasemap.py:158` | ✅ met — proven, not asserted: `_document_plan` body byte-identical; fixture shows docs home newest / delivery oldest simultaneously |
| AC-2.6 | report `:574-586` | ✅ met — exact wording, distinct from a `null`+reason state |
| AC-2.7 | report `:556-572` | ✅ met — note present in all three document states, names the tag, `_esc`-ed |
| AC-3.1 | `releasemap.py:337-387`; report `:766-820` | ✅ met (modulo waived F4) — every figure present with its denominator; scope now carries `n` (F1 fixed); `first_date` disputed only against the spec's literal text (F4, waived) |
| AC-3.2 | report `:782-820` | ✅ met — every gap a number in text; bar is decoration only |
| AC-3.3 | report `:849-856` | ✅ met — 1-tag and 2-tag fixtures both refuse with `n` stated; `n` now names the quantity it actually counts (F14) |
| AC-3.4 | report `:857-880` | ✅ met — an unreadable gap renders as its own row carrying `gap_days_reason` and no bar, in every chain position, while every other gap still renders (F2 fixed) |
| AC-3.5 | report `:740-742` | ✅ met — zero-tag repo shows the reason, `figures: null`, no zeros |
| AC-3.6 | `scopecount.py:34`, `:76-82`; `releasemap.py:194-221` | ✅ met — honest at all three layers now: JSON, the HTML card/band (F1), and the line bound, which refuses by name instead of truncating (F3). No silent zero and no invented count reproducible on any fixture I built |
| AC-3.7 | report `:829-888` | ✅ met — exactly two states: present shows **every** gap slot (measured or not), or absent with a reason naming `n`. The partially-drawn state is gone (F2) |
| AC-4.1-4.4 | report `:588-633`, single call site `:645` | ✅ met — v0.6.0's real card carries all seven figures and the full AC-4.3 combination |
| NFR-1 | `cli.py:118-125` | ✅ met — no new flag/subcommand/error class; `--help` unchanged apart from the corrected `--repo` line |
| NFR-2 | whole-payload diff vs `HEAD` | ✅ met — **fully additive**: only `provenance.insights_version` changed; every pre-existing key and value byte-identical, pseudo-release key set unchanged |
| NFR-3 | report `:526`, `:541`, `:562`, `:625`, `:806-808` | ✅ met — my own hostile tags (`<script>alert(1)</script>`, `'onload=alert(2)`) render inert everywhere; no `alert` in any tag; bar width is a clamped `int` (`:776-780`), never repo text; `read_scope_counts` raised nothing across 21 hostile inputs |
| NFR-4 | `_STYLE:154-171` | ✅ (source) — real `<dl>`/`<table>`, single `<h1>`, auto-fit grid; contrast computed: text 15.67:1 and 7.01:1 on `--bg-card`, bar 7.68:1 / 8.55:1 (bars ≥3:1 either background). Live 375 px + `getComputedStyle` remain `/demo-day`'s |
| NFR-5 | `_STYLE:170`; report `:857-880` | ✅ met — one class, one shipped token (`--accent-teal`), only `width` varies; standout is `<strong>` + "longest" text, now shown only when it is true. No trend/fit/projection anywhere. Denominator discipline closed at every figure (F1, F2, F3, F14) |
| NFR-6 | `releasemap.py` (no clock read) | ✅ met — no `datetime.now()`; determinism canaries green |
| NFR-7 | render output | ✅ met — one self-contained file, single inline `data:` logo, no external `src`/`href`; 0/1/2/3/10-tag repos all render |
| NFR-8 | measured | ❌ **not met, waived by the user** — 13.6 s vs a 5 s bar. Linearity half holds (+1 call/release). Attribution independently confirmed accurate; ~0.6 s is this feature's, ~10.3 s predates it (F4) |

## 5. What Was Checked

- [x] Correctness: logic does what the acceptance criteria demand — traced every Must AC to code and re-measured each stated figure against this repo
- [x] Non-functional: applicable NFRs and constitution quality bars hold — F1-F3's honesty gaps closed and re-verified; NFR-8 remains the one shortfall (F4, waived)
- [x] Error handling: failures are handled, not swallowed — one real gap found and fixed (F5); `build_release_map`'s outer wrap still catches every named class
- [x] Security: no injected input trusted, no secrets in code — hostile tag names and hostile `spec.md` bodies both re-tested with fresh inputs, not the reported repro
- [x] Tests: exist, are meaningful, and pass — **679 green**; every fix mutation-tested (fix reverted → its test goes red), which is how F15's unpinned path was found and closed
- [x] Readability: the next developer will understand this — F9's stale promises and F10's narrowed input shape both documented accurately

## 6. Verdict

**Round 2 (re-review) — `passed`.** I did not take the fix round on its word: for each finding I
built fixtures the developer had not, and then reverted each fix in `src/` to confirm its regression
test actually goes red. All three Major honesty leaks are genuinely closed, and closed at the level
of the rule rather than the reported symptom — a partially unreadable delivered scope now discloses
`n` and names the unreadable members on both the card and the band, including the shapes never
tested (asymmetric `us`-set/`acs`-null, unicode and 300-char names, an all-unreadable release, an
honest `0 of 0`); an unmeasurable gap renders as a row with its own reason wherever it sits in the
chain, including the fully unreadable chain where `gap_max` is `None` and the code could plausibly
have raised; and a spec past the line bound refuses by name while exactly 5000 lines still counts,
even when the 5000th line is itself a story heading. The "longest" mark survived 22 chains — 2-, 3-
and 4-way ties, all-zero, zero-mixed and negative gaps — never appearing more than once and never
on a value it could not justify. The fix round did leak two small things of its own, both found by
techniques the fix round did not use: F2's rewrite silently changed what the refusal notice's `n`
counts, leaving it claiming a measured gap where there was none (F14), and F8's fix was entirely
unpinned — reverting it left all 677 tests green while the report claimed coverage that did not
exist (F15). Both are Nits, both are fixed here, and both are exactly why "fixed code is new code"
is worth enforcing. What remains is F4, unchanged and untouched by this round: NFR-8's 5 s bar is
still missed by 2.7×, caused almost entirely by code this feature was told not to touch, and the
user has waived it with the spec amendment tracked as a follow-up. On the code this feature actually
owns, I can find nothing left that presents a number as complete when it is not — which was the one
thing standing between this and a pass. Suite green at 679.

**Round 1 (original pass) — `changes-requested`.** Retained for the record: the architecture was
right and all four things the plan told me to distrust survived adversarial testing, but
`build_release_map` computed the honest-null bookkeeping correctly and the renderer then threw it
away in three places (F1, F2, F3), and NFR-8's stated bar was measurably not met (F4).

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here) — F1, F2, F3 fixed and independently re-verified against fresh fixtures; **F4 waived by the user 2026-08-24**, reason recorded in its §3 row (spec-wording vs. measured reality, not a code defect; amendment tracked as a follow-up)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — AC-3.4/AC-3.6/AC-3.7 now met (F2, F1, F3); §6's "never invent a number" no longer breached at the line bound, the card, the band or the refusal notice
- [x] All plan deviations documented and accepted — both plan-disclosed deviations independently verified as accurately described; the spec's own AC-1.1/AC-3.1/NFR-8 wording remains unreconciled by the user's explicit waiver (F4), tracked as a follow-up rather than silently accepted
- [x] Test suite runs green — **679 passed**, re-run in full after the fix round and again after the reviewer's round-2 fixes; every fix additionally mutation-tested
- [x] Status set to `passed`
