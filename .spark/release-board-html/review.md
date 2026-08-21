# Review Report: release-board-html

| | |
|---|---|
| **Phase** | Review (round 2 — re-review after fix-mode) |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Working-tree diff vs `HEAD` (`9b25f35`), `.spark/release-board-html/plan.md`, round-1 findings F1-F10 |
| **Status** | `passed` |
| **Date** | 2026-08-20 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report — including `/increment` in fix-mode, which is not this
     report's owner — updates it in the same edit that closes or re-rules a finding:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed` — REVIEW GATE closed, `/demo-day` may start.
- **Verdict:** Every round-1 fix was re-derived here from scratch, not read off the annotation:
  new inputs, live CLI runs against the real repo, and a mutation test per fix (each new test was
  shown to fail when its bug is reinstated). All eight hold. Three new findings this round, none
  gate-blocking.
- **Open:** `4 open (0 Blocker, 0 Major), 11 fixed` — open: F6 (Minor, unchanged, routed to
  `/demo-day` to rule on two decorative border pairs), F8 (Nit, pre-existing `--version` gap,
  own backlog item), F12 (Nit, library-only `ValueError` on a NUL-byte `--output`, unreachable
  from the CLI), F13 (Minor, plan.md text is stale in two places — for the EM, not the developer).
- **For `/demo-day`:** F6 is your call and needs `getComputedStyle` on `--border-line`/
  `--border-subtle`. Do **not** test plan T4's DoD claim that `v0.5.0` has one member — it is
  false (F13); the corrected datum is spec AC-2.3's `v0.7.0`/`git-native-mid-cycle-board`.
- **Binding ruling:** §3 Findings + §6 Verdict + the REVIEW GATE below — status column of §3 is the
  per-finding source of truth; this block is the summary.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a finding at the next `/peer-review` and proceed — don't stop on it.

## 1. Scope

Full working-tree diff against `HEAD` (`9b25f35`) — the feature is uncommitted.
**New:** `gitboard/releaseboard_report.py` (388 ln, was 320), `gitboard/releaseboard_logo.py`,
`tests/test_releaseboard_{render,cli,determinism}.py`, `assets/*.png`. **Modified:** `cli.py`,
`errors.py` (+`ReportUnwritableError`), `__init__.py`, `pyproject.toml`, `README.md`.
Round-2 context read for judgement: `releasemap.py:_pseudo_release`, `worktype.py:55-79`,
`spec.md` AC-2.3/§1/C7, `plan.md` T2/T4/§Handoff.

**Verified by execution, not by reading** (round 2): full suite **499 passed, 124 s** (498 before
the one test I added — the developer's claimed 498 is accurate); 5 hostile `--output` values through
the real installed CLI; a live `build_release_map()` + `git log` cross-check of every real-repo datum
the spec cites; the real page re-rendered (53 722 B, h-level sequence extracted by regex); the
truncation bound probed at its real value at 49/50/51/137; work-types order probed with scrambled and
reverse-insertion dicts; WCAG re-composited from scratch; byte-determinism across 3 fresh
interpreters. **Mutation-tested:** each F1/F2/F5/F7 fix was reverted in a scratch copy and the new
tests confirmed to fail — no tautologies. **Not reviewed:** browser `getComputedStyle`, 375 px
scroll, real offline load, visual logo render — correctly deferred to `/demo-day` by plan §4.
No tool file was passed.

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `--format html` + `--output` wired; `--format json` line byte-unchanged. |
| T2 | ✅ | Scaffolding all present; heading scheme now `h1→h2→h3→h4` with no skipped level (F4 closed). Plan text still says "`<h3>`-per-member" — the `<h4>` scheme is this review's own prescription, accepted; the stale plan wording is F13. |
| T3 | ✅ | `tag: null` discriminator, verbatim figures, true-zero sentence. |
| T4 | ✅ | Table markup, backtick strip, back-link, member headings all correct. DoD text carries a false real-repo datum — F13. |
| T5-T8 | ✅ | Unchanged this round; round-1 verification (incl. the byte-for-byte logo re-derivation) stands. |
| T9 | ✅ | Escaping, shape guard, determinism, version bump — and the `--output` half of the hostile-input checklist now genuinely holds (F1 closed). |
| Deviations | ✅ | `_STYLE`/`REPORT_FILENAME` rename recorded in plan §Handoff; `<h4>` member headings prescribed by F4 and accepted here. |

## 3. Findings

Round-1 rows are compacted to problem → fix → **my own re-derivation**. Original detail is in git
history of this file.

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | **Blocker** | `releaseboard_report.py:379-387` | `mkdir`/`write_text` sat outside any guard → raw `NotADirectoryError`/`PermissionError` traceback on a hostile `--output`, violating constitution §6 and NFR-2. **Fixed:** own `try/except OSError → ReportUnwritableError` (`errors.py`, `reason="report_unwritable"`). **Re-verified:** 5 live CLI runs (existing file; `/System/nope`; a path nested under a file; 300-char component → `ENAMETOOLONG`; a self-referential symlink → `ELOOP`) all give exit 1, `sort_keys` JSON `{"error": "report_unwritable", …}` on **stderr**, empty stdout, no `Traceback`. **Misattribution checked:** the two `try` blocks are disjoint — `:372-377` wraps only `render_release_board_html`, `:380-386` only the two write calls, and `Path(output)` sits between them. The render path is pure string work (`_esc` = `html.escape(str(v))`, logo is a module constant) and cannot raise `OSError`, so nothing shape-related can land in the write clause. **Mutation:** removing the guard fails all 3 F1 tests, including the CLI-level `"Traceback" not in stderr`. | fixed |
| F2 | **Major** | `releaseboard_report.py:187-223` | NFR-4's bound-with-disclosure clause was implemented nowhere. **Fixed:** both lists bounded at 50 with a `.truncation-note`. **Re-verified at the real constant, not monkeypatched:** 49 → 49 blocks/0 notes; 50 → 50/0 (correct boundary, no off-by-one); 51 → 50 shown + "Showing the first 50 of 51."; 137 → 50 shown + "…50 of 137." Arithmetic correct on both lists independently. The note sits inside `.release-card`, so its `--text-secondary`-on-`--bg-card` pair is already covered by an existing contrast test. **Mutation:** unbounding either slice fails its test. | fixed |
| F3 | **Major** | `spec.md:138` (AC-2.3), `spec.md:54-55` (§1), `spec.md:224` (C7); `tests/test_releaseboard_cli.py:121` | AC-2.3 asserted `v0.5.0` has one member (`measurement-honesty`); it has 2. **Fixed:** PO re-pointed AC-2.3 and §1 at `v0.7.0`/`git-native-mid-cycle-board`, logged as C7. **Independently re-derived, not read:** `git log --name-only v0.6.0..v0.7.0` touches exactly one `.spark/` directory (`git-native-mid-cycle-board`, across all 4 commits in range), and a live `build_release_map()` returns `members == ["git-native-mid-cycle-board"]`, `unattributed == []` for `v0.7.0`. I also re-checked the spec's two *other* real-repo claims while here: AC-2.2's `v0.3.0` → 3 members ✅, AC-2.4's `v0.6.0` → 1 unattributed commit `26e7f95` ✅. `v0.5.0` still genuinely has 2. The new CLI test asserts exact list equality against this repo. **Residual:** plan T4's DoD still repeats the false datum — F13. | fixed |
| F4 | Minor | `releaseboard_report.py:181` | Member names shipped as `<p class="member-name">` against a design-review finding routed to `/increment`. **Fixed:** promoted to `<h4>`. **Re-verified on a real render of this repo:** heading counts `{h1:1, h2:9, h3:18, h4:14}`, full level sequence `1,2,3,4,3,2,3,4,4,…`, **zero skipped-level jumps**, h1 first, and every `class="member-name"` element is an `h4` (no `<p>` survivor). `.member-name` still pins `font-size: 1rem; font-weight: 700`, so the change is semantic, not visual. | fixed |
| F5 | Minor | `releaseboard_report.py:226-243, 264` | Round 1 diagnosed this as "`build_release_map()` never emits `work_types`" and proposed striking AC-1.3 — **that diagnosis was wrong and was corrected**; the renderer was silently dropping a field that is present. **Fixed:** rendered in the pseudo-release stats line. **Independently re-derived:** `releasemap.py:_pseudo_release` ends with `if "work_types" in board: pseudo["work_types"] = board["work_types"]` — a real conditional pass-through; a live call on this repo returns `{"value": {"docs": 100}, "reason": null}` on the pseudo entry, and the page now reads `… 2 local branches. Work types: docs 100%.` **Order is genuinely fixed, not incidental:** a scrambled dict and a reverse-insertion-order dict both render `feat, fix, docs, test, unclassified`. **No silent drop:** `worktype.py:66,77` builds the distribution only from `RECOGNIZED_TYPES` + `unclassified`, so the renderer's order tuple is exhaustive by construction. Absent / `value: null` / empty-dict all render no clause. **Mutation:** forcing the clause empty, or switching to raw dict order, each fails a test. | fixed |
| F6 | Minor | `releaseboard_report.py:64-65` (`--border-subtle`, `--border-line`; used at `:82,88,93,99,109,111`) | NFR-5 says AA "on every color pair the page ships". Re-composited from scratch this round, tokens byte-unchanged: `rgba(255,255,255,.09)` → **1.22 / 1.26 / 1.28:1** on `--bg-primary`/`--bg-secondary`/`--bg-card`; `rgba(58,189,176,.15)` → **1.24 / 1.28 / 1.29:1**. WCAG 1.4.11 likely exempts a decorative border where structure is conveyed by markup (it is — real `<table>`/`<th scope>`), so this is probably not a true failure, but this repo filed a 2.85:1 gridline as a finding once already and no test covers non-text pairs. **Fix:** `/demo-day` measures both pairs via `getComputedStyle` and rules explicitly; record the ruling either way so a third occurrence isn't re-litigated. *(Location updated — the fix round shifted line numbers; the token values are unchanged.)* | open |
| F7 | Nit | `tests/test_releaseboard_render.py:255-262` | Test name claimed "both backgrounds", body asserted one. **Fixed:** asserts `#12121a` and `#16162a`. **Proved non-vacuous, not just present:** substituting `#0078ff` (4.55:1 on `--bg-secondary`, 4.34:1 on `--bg-card`) fails **specifically at line 262**, the new assertion — so the second background is load-bearing. Real hues on `--bg-card`: 7.69 / 7.32 / 11.79 / 7.01 / 5.28 — all clear 4.5:1. | fixed |
| F8 | Nit | `cli.py:29-33` | `insights --version` exits 2 with a usage error; no `--version` in `_build_parser`. Pre-existing across all 8 subcommands, correctly untouched — re-confirmed unchanged this round. **Fix:** `parser.add_argument("--version", action="version", version=__version__)` as its own backlog item. | open |
| F9 | Nit | `releaseboard_report.py:268-270` | Partly-escaped sentence concatenated with an unescaped tail. **Fixed:** one `_esc` wraps the whole sentence — re-confirmed on the current source, and the new `work_types` clause is inside that same wrap. | fixed |
| F10 | Nit | `releaseboard_report.py:57-62` | `--text-muted` declared with no guardrail. **Fixed:** CSS comment records the measured 3.90/3.51:1 and the large-text/non-text-only restriction; token is still referenced nowhere else. | fixed |
| F11 | Nit | `tests/test_releaseboard_render.py:406-418` | F5's fix claims a fixed render order, but the covering test passed a dict already in `RECOGNIZED_TYPES` order — it would have passed against raw dict iteration too, so the ordering half of the claim was untested. **Fixed by the reviewer** (own finding, test-only, zero production change): added `test_pseudo_release_work_types_render_in_fixed_order_not_dict_order`, which feeds reverse insertion order; it fails against a raw-`.items()` mutant and passes on the shipped code. Suite re-run after the edit: 499 green. | fixed |
| F12 | Nit | `releaseboard_report.py:383` | The write guard catches `OSError` only. A NUL byte in `output` makes `mkdir` raise `ValueError("embedded null character in path")` — a raw traceback. **Unreachable from the CLI** (`execve` truncates argv at NUL; I confirmed `--output $'/tmp/ab\0cd'` arrives as `/tmp/ab`), so this is not an F1 regression and not a constitution breach. It is reachable from the library surface, and the `library` lens is active plus this project's own house pattern anticipates a second adapter calling shared cores directly. **Fix:** `except (OSError, ValueError)` — the block contains only `mkdir`/`write_text`, so a `ValueError` there can only mean an invalid path. Left open rather than reviewer-fixed: widening an `except` clause is the developer's/EM's call, not a mechanical typo fix. | open |
| F13 | Minor | `plan.md:50` (T4 DoD), `plan.md:48` (T2), `plan.md:17` (§Handoff Deviation) | Two stale claims in plan.md, for the **EM**, not the developer. (a) T4's DoD still requires "`v0.3.0`'s 3 members and **`v0.5.0`'s single member** render exactly" — the exact false datum F3 corrected in the spec; `v0.5.0` has 2 members. A QA tester working from plan DoDs would file a false bug against correct code. (b) T2 still specifies "`<h3>`-per-member" while the shipped scheme is `<h3>` section / `<h4>` member — a deviation this review prescribed (F4) and accepts, but plan §Handoff's Deviation note still records only the `_STYLE` rename. **Fix:** EM re-points T4's DoD at `v0.7.0`'s single member (per spec C7) and adds the heading-level deviation to §Handoff. Not gate-blocking: the spec — the authoritative AC source — is correct, and the Handoff block above warns `/demo-day` directly. | open |

**Independently re-verified this round, not findings:**
- **Determinism survives the new clauses.** Three fresh interpreters (hash randomization on) render the real repo to an identical SHA-256, 53 722 B (up 533 B from round 1 — the work-types clause, `<h4>` tags and comments). NFR-6 holds.
- **Round-1 "not a finding" items re-spot-checked and unchanged:** badge background is still explicitly `--bg-secondary`, hue still keyed only to `_ARTIFACT_HUES[artifact]` from the fixed name tuple (no status-value branch), `--format json` stdout still the identical `print(canonical_json(release_map), end="")`, `--output ""` still falls back to `--repo`.
- **No new unbounded or unescaped surface.** The two new dynamic strings this round (`.truncation-note` counts, the work-types legend) are both `int`/vocabulary-derived and both sit inside an `_esc` wrap or a static template.

## 4. Requirements Traceability

Unchanged rows from round 1 (AC-1.1, AC-1.2, AC-1.4, AC-2.1, AC-2.2, AC-2.4, AC-2.5, AC-2.6,
AC-3.1, AC-3.2, AC-3.3, NFR-1, NFR-3, NFR-6, lens `library`) all remain ✅ and were spot-checked
against the current source. Changed this round:

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.3 | `releaseboard_report.py:246-270` (`_pseudo_stats_line` + `_work_types_clause`) | ✅ was ⚠️ — `work_types` now shown as-is, F5 closed |
| AC-2.3 | `spec.md:138` (corrected datum) + `tests/test_releaseboard_cli.py:121` (real-repo assertion) | ✅ was ⚠️ — F3 closed |
| NFR-2 | `render.py:79` choke-point; both guards in `run_release_board_report` | ✅ was ⚠️ — `--output` checklist now holds (F1); F12 is a library-only residue |
| NFR-4 | `releaseboard_report.py:30-31,187-223` | ✅ was ⚠️ — bound + disclosure implemented and probed at the real constant |
| NFR-5 | `_STYLE`, `_ARTIFACT_HUES`, heading scheme | ⚠️ text pairs all clear AA; heading hierarchy now correct (F4 closed); non-text borders still unruled (F6) and `getComputedStyle`/375 px deferred to `/demo-day` |
| Lens `cli` | `cli.py` | ⚠️ stdout/stderr, exit codes, `--help`, no-ANSI, error-on-stderr all ✅ (F1 closed); `--version` still missing (F8) |

## 5. What Was Checked

- [x] Correctness: logic does what the acceptance criteria demand — every Must AC now traces to code
- [x] Non-functional: applicable NFRs and constitution quality bars hold — NFR-5's non-text pairs remain `/demo-day`'s ruling (F6)
- [x] Error handling: failures are handled, not swallowed — the write path is now guarded and re-broken by hand to prove it
- [x] Security: no injected input trusted, no secrets in code
- [x] Tests: exist, are meaningful, and pass — 499 green; each new test mutation-tested rather than read
- [x] Readability: the next developer will understand this

## 6. Verdict

All six fixes hold under adversarial re-derivation, and two of them are better than the annotations
claimed. The Blocker is genuinely closed: five different hostile `--output` values — an existing
file, an unwritable system path, a path nested under a file, an over-length component, a symlink
loop — now all exit 1 with clean `sort_keys` JSON on stderr and nothing on stdout, and the guard
does not over-reach, because the render `try` and the write `try` are provably disjoint and the
render path cannot raise `OSError` at all. The NFR-4 bound triggers at its real value with correct
arithmetic and a correct boundary, not just at a monkeypatched one. F3's spec correction survives
the check I care about most — I re-derived `v0.7.0`'s single member from `git log` and from a live
`build_release_map()` rather than trusting the edited text, and re-checked the spec's two other
real-repo claims while I was there. F5 deserves particular credit: the fix round found my own
diagnosis wrong, proved it, and fixed the real bug instead of striking a correct AC — that is the
harder and right call, and the pass-through in `_pseudo_release` is exactly where they said it was.
Every new test was mutation-tested, not read: reinstate the bug and the test fails. One of them
didn't — F5's ordering claim was covered by a fixture already in canonical order — so I added the
missing case myself and proved it fails against a raw-dict-order mutant; the suite is 499 green, and
the developer's claimed 498 was honest. What remains is not gate-blocking: F6 is still `/demo-day`'s
ruling to make on two decorative borders, F8 is still a pre-existing backlog item, F12 is a
library-only `ValueError` that no CLI invocation can reach, and F13 is plan.md carrying two stale
sentences the EM should correct — including, awkwardly, the very `v0.5.0` claim F3 removed from the
spec, which is why the Handoff block warns `/demo-day` about it in as many words. The gate closes.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings — F1 closed and re-broken by hand to prove the guard is real
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here) — F2 and F3 closed on independent evidence; no waiver requested or needed
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — AC-1.3 and AC-2.3 now fully traced; "never a raw traceback" holds on every CLI-reachable path
- [x] All plan deviations documented and accepted — `_STYLE` rename in plan §Handoff; the `<h4>` member heading is this review's own F4 prescription, accepted here. plan.md's own text is stale in two places (F13, Minor, routed to the EM) — a documentation defect, not an undocumented deviation
- [x] Test suite runs green — **499 passed, 124 s**, run by the reviewer after the reviewer's own test addition (498 before it, matching the developer's claim)
- [x] Status set to `passed`
