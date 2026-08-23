# Review Report: release-board-docs

| | |
|---|---|
| **Phase** | Review (round 2 — adversarial re-review after fix-mode) |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | Working-tree diff vs `HEAD` (`385c1ea`), `.spark/release-board-docs/plan.md`, round-1 `review.md` |
| **Status** | `passed` |
| **Date** | 2026-08-23 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report — including `/increment` in fix-mode, which is not this
     report's owner — updates it in the same edit that closes or re-rules a finding:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed`. REVIEW GATE closed at re-review; `/demo-day` may start.
- **Verdict:** Every one of F1–F15 was re-verified by execution against freshly built
  inputs, not by reading the fix or trusting the annotation. F1 (Blocker) and F3 (Major)
  genuinely hold. Re-review found and fixed three residual defects the fix-mode round
  introduced or left behind (F16–F18) and left one non-blocking Nit open (F19).
- **Open:** `1 open (Nit F19), 18 fixed`. F19 — `read_artifact_document`'s `allowed_root`
  containment control defaults to `None` (opt-in), so a future second caller silently
  reopens F1's hole; only production caller passes it today, so this blocks nothing.
- **What re-review changed:** F8's fix was **incomplete** — `{"releases": 42}`, a NUL in a
  feature name and a >NAME_MAX name still raised (F16, fixed here). F11's and F7's fixes
  shipped with **no regression test at all** — both mutants survived the full 582-test
  suite (F17/F18, tests added here). Suite is now **585 green**, and every fix in this
  feature is mutation-verified (see §5).
- **Binding ruling:** §3 Findings and the REVIEW GATE below — status column of §3 is the
  per-finding source of truth; this block is the summary.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a finding at the next `/peer-review` and proceed — don't stop on it.

## 1. Scope

Round 1: full working-tree diff against `HEAD` (`385c1ea`) — new `gitboard/artifactcontent.py`,
`gitboard/markdownlite.py`, `tests/test_{artifactcontent,markdownlite,releaseboard_docs}.py`;
modified `gitboard/releaseboard_report.py`, `cli.py`, `README.md`, `__init__.py`,
`pyproject.toml`, `tests/test_releaseboard_{cli,render}.py`. Round 2 re-read every hunk the
fix-mode round touched, in full. No tool file was passed; scoping done by hand.

**Round-2 verification, all by execution:** the original F1 exploit rebuilt from scratch in a
fresh throwaway repo (canary file + `/etc/passwd` symlinks) — **zero leaked bytes**, plus three
attack shapes neither round had tried (symlinked feature *directory*, two-hop symlink chain,
`.spark` itself a symlink); a 60-member F3 repro plus a 7-case boundary matrix (0 dead anchors
in every one); a best-fit budget fixture; 28 link-scheme cases; 27 italic word-boundary cases;
**4,096 brute-forced heading sequences**; 17 malformed collector shapes; **16 source mutants**
run against the suite to prove each regression test actually fails when its fix is removed;
full suite **585 green**; the real repo re-rendered twice (byte-identical, 1,314,196 bytes,
497 headings / 1 `<h1>` / 0 skips, 36 internal anchors / 0 dead).
**Not reviewed:** live-browser behaviour (`<details>` keyboard operability, glyph tofu, 375px
scroll, `getComputedStyle`) — plan §4 defers these to `/demo-day`.

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `_display_order` partitions on `tag is None`, never position; index and detail cards share one `order`; JSON order re-verified unchanged (`v0.1.0…v0.9.0, None`). |
| T2 | ✅ | Dedup holds (45 distinct doc ids, 0 duplicates on the real repo). F3 and F13 both closed: the home block always exists and the non-home link now targets `#member-N-M`. "Byte-identical to T1's output" is no longer literally true (member blocks gained `id=`) — intended, needed for T5's back-links; noted, not a finding. |
| T3 | ✅ | Missing / stat-fail / oversize / undecodable / permission / **escapes-`.spark/`** each return a distinct named `reason`; empty is its own flag. |
| T4 | ✅ | Bounds hold and are honest. F6 closed; F7 closed by adding the page-level `.truncation-note` **and** amending plan §3 T4's own DoD to describe best-fit — plan and code now agree. |
| T5 | ✅ | `.doc-content` visually unlike `.release-card`; provenance label carries the real repo-relative path; back-link resolves to a real `member-N-M` id. |
| T6 | ✅ | The symlink-escape control this task named now exists (`artifactcontent.py:78-98`) and is proved by an end-to-end exploit, not just a unit test. Escaping remains airtight under fresh hostile probes. |
| T7 | ✅ | F4/F5/F12 all closed. Link allowlist casefolded and `//`-rejecting; unterminated comments render visibly; heading levels come from a real outline stack. |
| T8 | ✅ | Real `<table>`/`<th scope="col">`/`<caption>`, 60-char truncated, omitted when absent; ragged rows tolerated. |
| T9 | ✅ | `.sr-only` rule present in `_STYLE` and mutation-verified; 611 prefixes now genuinely hidden. |
| T10 | ✅ | One `<h1>`, no skipped level page-wide, re-proved on the live render. |
| T11 | ✅ | `--help` now names the document read and scopes it to `--format html`; README, `__init__`, `pyproject` and `uv.lock` all at `0.10.0`; weight test writes to `tmp_path`. |
| §1 alt. (c) | ⚠️ | Unchanged from round 1 and accepted as-is: the "new arbitrary-write surface" claim used to reject alternative (c) is overstated — `releasemap.py:70-75` already gates those names. The rejection stands on its other two grounds. Recorded, not re-litigated. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Blocker | `artifactcontent.py:78-98` | `read_artifact_document` followed symlinks with no containment: a `.spark/<feature>/spec.md` symlinked outside the repo was read and embedded verbatim. **Re-verified by rebuilding the exploit from scratch** (fresh repo, canary file + `/etc/passwd`): 0 occurrences of any target byte, both documents return `reason: "document path escapes .spark/"`, rendered as a visible honest notice beside the real provenance path. Also proved no over-reach — an *internal* alias (`hostile/review.md -> ../normal/spec.md`) still reads normally. Three further shapes blocked: symlinked feature directory (dropped by `releasemap`), two-hop symlink chain, `.spark` itself a symlink. Mutant (containment check deleted) is caught by `test_symlink_escaping_spark_directory_is_rejected`. | fixed |
| F2 | Major | `releaseboard_report.py:_STYLE` | `.sr-only` was emitted 611× with no CSS rule. Rule present; mutant (rule deleted) caught. | fixed |
| F3 | Major | `releaseboard_report.py:250` | `_document_plan` iterated all members while only 50 render, homing a feature to a block that never exists. **Re-verified with the original 60-member repro**: `f55`'s documents now render exactly once, under the older release at `member-0-0`, a block that genuinely exists. A 7-case boundary matrix (shared at slot 5 / past 50 in one / past 50 in both / only release / exactly 50 / 51st shared) gives **0 dead anchors and 0 documents homed nowhere** in every case. Mutant caught. | fixed |
| F4 | Minor | `markdownlite.py:228-249` | Unterminated `<!--` no longer swallows to EOF: it renders as visible escaped text and the rest of the document (heading, table) renders normally; text after a same-line `-->` is emitted. Both halves mutation-verified. | fixed |
| F5 | Minor | `markdownlite.py:74-80` | Casefold + `//` rejection verified over 28 hrefs: `HTTP://`/`HTTPS://`/`MAILTO:`/`Http://` now allowed; `JAVASCRIPT:`, `JavaScript:`, `Data:`, `DATA:`, `VBSCRIPT:`, `FILE://`, `//evil.example.com`, whitespace/tab variants and unicode casefold traps (`JAVASCRİPT:`, `HTTPｓ://`, zero-width) all still rejected. `[t](JavaScript&#58;x)` is blocked too — `_esc` escapes the `&`, so the entity never re-decodes into a scheme. Both mutants caught. | fixed |
| F6 | Minor | `releaseboard_report.py:285-289` | Both-caps case now states both (`"…first 1 of 12 lines (100 of 300000 bytes)…"`); line-only and byte-only wordings unchanged. Mutant caught. | fixed |
| F7 | Minor | `releaseboard_report.py:556-576`, `plan.md` T4 | Resolved as described, and both halves independently confirmed: a fixture where a 2 MB feature fits, a 2 MB one is skipped and a tiny later one still fits produces a page-level `.truncation-note` (`"1 feature's documents were not embedded… .spark/b-giant/"`) positioned **above the first release card**, alongside the per-member notice; plan §3 T4's DoD now explicitly says "best-fit, not a hard stop" and cites F7, so plan and code agree. (T4's *description* column still reads "after which documents are not embedded" — ambiguous rather than contradictory once the DoD in the same row is read; recorded, not raised.) | fixed |
| F8 | Minor | `artifactcontent.py:171-181` | Original three shapes are total — but the fix was **incomplete**; see **F16**. Now genuinely total over 17 shapes. | fixed |
| F9 | Minor | `cli.py:121` | `--repo` help now names the document-content read and scopes it to `--format html`. Confirmed in live `--help`. | fixed |
| F10 | Minor | `tests/test_releaseboard_cli.py:100-104` | Test passes `--output tmp_path`; the repo's own `.aspark-insights/release-board.html` mtime was unchanged by my two full suite runs. | fixed |
| F11 | Minor | `markdownlite.py:42` | Word boundary verified over 27 cases: 9 snake_case shapes (`_leading`, `trailing_`, `mid_dle`, `__dunder__`, `a_b_c_d`, `_word_s`, `1_word_`, …) are untouched, and 7 legitimate italics that abut punctuation/brackets/quotes (`_word_.`, `(_word_)`, `[_word_]`, `"_word_"`, `_word_, then`, `_multi word phrase_`) still emit `<em>` — no over-reach. Shipped with no test; see **F17**. | fixed |
| F12 | Nit | `markdownlite.py:262-274` | Stack algorithm verified on the untried alternating case `# a / ## b / # c / ## d / ### e / ## f` → `h5, h6, h5, h6, aria-7, h6` (siblings reuse, no skip), and brute-forced over **all 4,096** source-level sequences of length 6 over `#`–`####`: **0 skipped levels, 0 sibling-reuse violations**, max emitted level 8. The original symptom (`#### A/B/C/D/E`) is now `h5×5`. Mutant caught by two tests. | fixed |
| F13 | Nit | `releaseboard_report.py:265,357-365` | Non-home link now emits `href="#member-1-2"`, which resolves to the target member's own block (`<h4>shared</h4>`), not the release card. Mutant caught. | fixed |
| F14 | Nit | `releaseboard_report.py:333-336,586-590` | `documents={}` now renders `"document not collected for this render"`; the string `"not read"` is gone from the page and the docstring's "unaffected" claim is corrected. `documents=None` still emits zero `<details>`. Mutant caught. | fixed |
| F15 | Nit | `markdownlite.py:43-51` | Recorded as a deliberate non-fix with the reasoning inline. Justification independently confirmed: `[a](http://u1) and [b](http://u2)` renders as two correct separate links, which matching to the last `)` would break. | fixed |
| F16 | Minor | `artifactcontent.py:171,174,82,87` | **New at re-review — F8's fix was incomplete.** `data.get("releases") or []` only catches a *falsy* wrong type, so `{"releases": 42}` still raised `TypeError: 'int' object is not iterable` — exactly the "non-list `releases`" case the new docstring claims to skip. Separately, `path.resolve()` raises `ValueError` (not `OSError`) on an embedded NUL, and `Path.is_file()` does **not** swallow `ENAMETOOLONG`, so both escaped `read_artifact_document`'s unconditional "Never raises" contract. Not reachable from `build_release_map()` (no real directory can be named either way), but the constitution's "Never a raw traceback" is asserted unconditionally by both docstrings. Fixed here: `isinstance(..., list)` guards, `except (OSError, ValueError)` on resolve, and a guarded `is_file()`; 17 shapes now total, with a regression test and three mutants caught. | fixed |
| F17 | Minor | `tests/test_markdownlite.py:26` | **New at re-review — F11 shipped with no regression test.** Reverting the word-boundary lookarounds reproduces the original defect verbatim (`test_releaseboard_render` → `test<em>releaseboard</em>render`) and **all 582 tests still pass**. Same class as F2's round-1 tautology. Fixed here: two tests (identifiers never italicised, real boundary-touching italics still work); mutant now caught. | fixed |
| F18 | Minor | `tests/test_releaseboard_docs.py:252` | **New at re-review — F7's page-level notice shipped with no regression test.** Deleting `_render_page_budget_notice(plan)` from the page left the suite green; only the per-member notice was covered, so the headline half of F7's fix was unguarded. Fixed here: a test pinning the page-level count, the `.spark/<feature>/` path, its position above the first release card, and the best-fit behaviour; both mutants (notice removed, best-fit → hard stop) now caught. | fixed |
| F19 | Nit | `artifactcontent.py:54` | `allowed_root: Path | None = None` makes F1's containment control **opt-in**: a future second caller that forgets the kwarg silently reopens an arbitrary-file-read hole, with no test or type failure. The module's own `_is_valid_feature_name` docstring argues for defence in depth at this exact boundary. Only the one production caller exists today, so nothing is currently exposed — left open rather than fixed because making it required touches the unit-test seam and is a design call. Fix: make `allowed_root` a required keyword and have tests pass an explicit root (or a named `UNCHECKED` sentinel). | open |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `releaseboard_report.py:532-546` | ✅ met — real render: pseudo, `v0.9.0` … `v0.1.0` |
| AC-1.2 | one `order` drives index and detail | ✅ met |
| AC-1.3 | `cli.py:271-275` (html branch only) | ✅ met — JSON order re-verified unchanged |
| AC-1.4 | member iteration untouched | ✅ met |
| AC-2.1 | `releaseboard_report.py:295-341` | ✅ met (after F3) — 0 dead anchors across a 7-case boundary matrix |
| AC-2.2 | `artifactcontent.py:52-151`, `releaseboard_report.py:333` | ✅ met (after F14/F16) — every failure mode a distinct named reason |
| AC-2.3 | `artifactcontent.py:94-104` | ✅ met |
| AC-2.4 | `markdownlite.py` (every leaf via `_esc`) | ✅ met — re-probed with fresh hostile inputs; 0 `<script>` on the real page |
| AC-2.5 | `artifactcontent.py:117-148`, `releaseboard_report.py:272-292,556-576` | ✅ met (after F6/F7) |
| AC-3.1 | `markdownlite.py:262-274` | ✅ met — 497 headings, 0 skips, one `<h1>`; 4,096 sequences brute-forced |
| AC-3.2 | `markdownlite.py:130-156` | ✅ met |
| AC-3.3 | `markdownlite.py:180-188` + `_STYLE` `.sr-only` | ✅ met (after F2) |
| AC-3.4 | `markdownlite.py:228-249,320-325` | ✅ met (after F4) |
| NFR-1 | `cli.py:118-133` | ✅ met (after F9) — one file, documented |
| NFR-2 | `artifactcontent.py:78-98`; `markdownlite.py:74-80` | ✅ met (after F1/F5) — exploit reproduced and blocked, 0 leaked bytes |
| NFR-3 | additive optional args only, zero new deps | ✅ met — `0.10.0` in `pyproject`, `__init__`, README **and** `uv.lock` |
| NFR-4 | `artifactcontent.py:23-31`, `releaseboard_report.py:40` | ✅ met — 1,314,196 bytes measured (26% of ceiling); budget is a hard bound |
| NFR-5 | `_STYLE` `.doc-*` | ✅ met from the source — all six new pairs 7.01–16.43:1; live measurement is `/demo-day`'s |
| NFR-6 | `artifactcontent.py:183` (sorted), `_document_plan` | ✅ met — two consecutive real renders byte-identical |

## 5. What Was Checked

- [x] Correctness: every AC re-traced by execution against freshly built inputs, not by reading the fix or the annotation
- [x] Non-functional: NFR-2 now holds (exploit reproduced and blocked); "Never a raw traceback" holds after F16
- [x] Error handling: `read_artifact_document` total over missing/dir/perm/undecodable/oversize/escaping/NUL/over-length; `collect_release_documents` total over 17 malformed shapes
- [x] Security: original exploit rebuilt from scratch and blocked with zero leaked bytes; three fresh attack shapes also blocked; the containment fix does not over-reach onto internal aliases; 28 link schemes and the `&#58;` entity bypass re-probed
- [x] Tests: **585 green**, and every fix mutation-verified — 16 mutants run, 14 caught immediately, the 2 survivors (F11, F7) fixed here with tests that now catch them
- [x] Readability: docstrings carry the *why* and, after F16, no longer assert a contract the code does not keep

## 6. Verdict

The fix-mode round did the work, and the two findings that mattered most genuinely hold up
under fresh hostile input rather than merely being present in the diff. I rebuilt the symlink
exploit from scratch in a new throwaway repo and it is dead — zero bytes of the canary file or
`/etc/passwd` anywhere in the page, an honest `document path escapes .spark/` notice in their
place — and the containment check does not over-reach, since an alias that stays inside
`.spark/` still reads normally; three attack shapes I had not tried before (symlinked feature
directory, two-hop chain, a symlinked `.spark` root) are blocked too. F3's 60-member repro now
renders `f55`'s documents under a member block that actually exists, with zero dead anchors
across seven boundary cases. F12's outline stack survived all 4,096 heading sequences I could
generate, and F11's word boundary survived 27 cases in both directions. But the round was not
clean, and three things only surfaced because I refused to take the annotation's word: F8's
"genuinely never raises" was still false for a truthy non-list, a NUL and an over-length name,
and F11's and F7's fixes shipped with **no test at all** — I reintroduced each defect verbatim
and the full 582-test suite stayed green, the same tautology class F2 was in last round. I
fixed all three, added the missing tests, and mutation-verified every fix in the feature so
this cannot recur silently. What remains is one Nit: the containment control is still opt-in
by default, which is a trap for the next caller rather than a live hole. The gate is closed
and `/demo-day` may start — with the standing note that browser-surface claims (contrast,
375px scroll, `<details>` keyboard operability) are still unmeasured and are QA's to prove.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings — F1 re-verified fixed by end-to-end exploit reproduction, zero leaked bytes
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here) — F2, F3 both re-verified fixed and mutation-guarded; none waived
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — all 14 ACs and 6 NFRs met; "Never a raw traceback" holds after F16
- [x] All plan deviations documented and accepted — T4's DoD amended in `plan.md` itself (F7); T2/T6/T9/T11 deviations now implemented as planned; plan §1 alt. (c)'s overstated rationale recorded in §2 and accepted as-is
- [x] Test suite runs green — **585 passed** (`python -m pytest -q`, run by the reviewer), including 4 tests added this round; 16 mutants confirm the suite fails when any fix is removed
- [x] Status set to `passed` — one Nit (F19) remains open and does not gate
