# Review Report: feature-lens

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | The uncommitted working-tree diff against `cb8b664`, `.spark/feature-lens/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-26 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report — including `/increment` in fix-mode, which is not this
     report's owner — updates it in the same edit that closes or re-rules a finding:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed` (header table authoritative for `Status`) — set at re-review (2026-08-26)
  after every fix was re-broken with the reviewer's own fresh inputs, not confirmed by reading the
  patch. `/demo-day` may start.
- **Verdict (re-review):** All 7 original findings hold as fixed **in behavior**, verified
  adversarially: F1 reproduced clean on a new four-shape git fixture; F2's boundary caught **25 of
  25** malformed shapes (22 the developer never tested) with zero raw leaks; F3 proved genuinely
  order-independent at three scan positions, and the F3 rewrite did **not** regress AC-1.1/1.2 dedup
  or the first-occurrence `status` read. But two of the seven shipped with a regression test that
  did not actually pin the fix (**F10**, **F11**) — proven by reverting each fix and watching all 67
  featurelens tests stay green. Both closed by the reviewer, mutation-verified.
- **Open:** `0 open` — F1-F9 closed (F4/F5 by the reviewer in the original pass, the rest in
  `/increment` fix-mode); F10/F11 raised and closed by the reviewer at re-review. Full suite
  **re-run by the reviewer: 749 passed, 0 failed**.
- **Carry to `/demo-day`:** T8 is still `todo` by design — browser contrast, 375px scroll, DOM
  byte-order and the wall-clock split are unverified here and are QA's to measure.
- **Binding ruling:** §3 Findings and the REVIEW GATE below.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a finding at the next `/peer-review` and proceed — don't stop on it.

## 1. Scope

Reviewed: `git diff HEAD` + untracked, i.e. new `gitboard/featurelens.py`, `gitboard/featurelens_report.py`,
eight new `tests/test_featurelens_*.py`; modified `cli.py` (one subparser + `_cmd_features`),
`__init__.py`/`pyproject.toml`/`uv.lock` (0.11.0 → 0.12.0), `README.md`. Read `releasemap.py`,
`artifactstatus.py`, `releaseboard_report.py` (`_STYLE`/`_ARTIFACT_HUES`/`_render_masthead`) and
`render.py::_esc` as context. Full suite re-run by me twice: **746 passed** on the fix-mode round,
**749 passed, 0 failed** after my own three added tests. Only test files were edited by me; the two
`gitboard/` modules are byte-unchanged from what the developer shipped (`git status` confirmed).

Verified by **fresh inputs of my own**, not by re-reading the developer's tests. Original pass: a
six-stage git repo, a hostile repo with my own payloads (`"><svg onload=alert(1)>&amp;` as the feature
directory, `v0."><script>alert(2)</script>` as the tag), four CLI hostile-input probes, a git-subprocess
counter. Re-review adds: a new four-feature git repo (Date-less table, empty Date cell, Date-before-Status,
neither row); a 25-shape malformed-`release_map` sweep; nine synthetic release maps probing delivery scan
order; a real-HTML-parser parity check of every pipeline `<li>` against its own table row; and **five
mutation tests** that revert each fix in place and assert the suite goes red.

Not reviewed / deferred: **T8** (browser contrast, 375px scroll, DOM byte-order, wall-clock split) —
correctly left `todo` for `/demo-day`, matching `release-metrics`' precedent. **aspark-graph was not
used**: `aspark-graph query staleness` returns `"stale": true` with 20 changed files, so per the tool's
own rule I treated it as absent and cite no result from it; §2 scoping was done by hand from the diff.
Pre-existing and out of scope: no `insights --version` flag (a `cli`-lens gap across all nine
subcommands, not introduced here); `--output` accepting a path outside `--repo` (identical behavior in
`insights releases`, verified).

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | Skeleton + json branch correct; 11 features, each once, `canonical_json` on stdout — all reproduced. The NFR-8 import guard was partly tautological (F4, fixed). |
| T2 | ✅ | Ordering, verbatim pseudo-release reason and gate-evidence pairing all correct and reproduced. The missing degrade reason (F1) is fixed and now pinned end-to-end (F10). |
| T3 | ✅ | Independently reproduced with my own six-stage repo: `Spec`/`Increment`/`Review`/`QA`/`Released`/`Unknown` all correct, `Unknown` surfacing `spec`'s own reason. |
| T4 | ✅ | **Deviation accepted and independently verified.** The DoD's "interactive-element count equal to the release board's" would indeed have been false (`release-board.html` ships many `<a>` index links). I parsed my own render with `html.parser`: tag histogram contains **no** `a`/`button`/`input`/`select`/`textarea`/`details`, no `tabindex`, no `on*` attribute. The substituted claim is strictly stronger and true. |
| T5 | ✅ | Buckets, order, `Unknown`-only-when-present and `.empty-notice` parity all correct. F6 (hardcoded `/tmp`, unasserted count) and F7 (evidence-free pipeline label) both fixed; no `/tmp` write remains anywhere in `tests/`. |
| T6 | ✅ | Hostile-fixture half re-broken again. The "malformed release-map dict → named `InsightsError`" half is now met and **exceeded**: 25/25 malformed shapes raise `ReleaseMapUnreadableError`, zero raw leaks. |
| T7 | ✅ | Byte-identical across runs in both formats (I re-ran it), no `datetime.now`/`date.today`, no external reference (only a `data:` logo URI), all four edge repo shapes render. F8's two decorative assertions fixed and proven live by mutation. |
| T8 | — | `todo` by design, not a finding. |
| T9 | ✅ | Version bumped in both places + `uv.lock`; `--help` documents the write location and the no-commit-no-row rule; README section + Project Status entry present. F9's vacuous guard retargeted to `cb8b664` + `ls-files --others`. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Major | `src/aspark_insights/gitboard/featurelens.py:113` | `spec_date_reason` is `null` while `spec_date` is `null`. `read_artifact_status` sets `reason` **exactly when `status` is `None`** (`artifactstatus.py:30,44`), so a `spec.md` whose header table has a `**Status**` row but no `**Date**` row returns `{status:"approved", date:None, reason:None}` — the row then ships a reason-less null and the HTML date cell degrades to the generic word `unavailable` (`featurelens_report.py:100`). Reproduced end-to-end on a real git fixture, not a hand-built dict. Breaks NFR-5 ("`null` + a specific, non-empty reason"), AC-1.4 ("the specific named reason for whichever field failed") and constitution §1/§6's honest-null discipline, on this feature's own new field. **Fix:** derive the date reason independently — `spec_entry["reason"] or "no Date row found in header table"` — and drop the `"unavailable"` fallback for that cell; add a fixture with a Date-less header table. | **fixed, re-verified** — `featurelens.py:116` falls back to `spec_entry["reason"] or "no Date row found in header table"`. Re-broken on a **new** git repo (feature `midnight-audit`, status `` `in-review` ``, no Date row): `spec_date_reason` = `"no Date row found in header table"`, and a no-Status-row sibling still surfaces its own reason. On real data the fallback is always accurate: `read_artifact_status` leaves `reason` null only when a header table *was* parsed and a Status row *did* match, so a null date there can only mean a missing Date row. Regression test was absent → **F10**. |
| F2 | Major | `src/aspark_insights/gitboard/featurelens.py:62-126`; `tests/test_featurelens_security.py:117-121` | Plan §1.3 pinned "`build_feature_lens` catches `(KeyError, TypeError, AttributeError)` at its own boundary and raises the existing `ReleaseMapUnreadableError`". No try/except exists and `errors` is not imported: `build_feature_lens({})` raises a bare `KeyError: 'provenance'`, `build_feature_lens(None)` a bare `AttributeError` (both reproduced). Worse, the guard test is named `..._raises_named_error_not_traceback` but asserts `pytest.raises((KeyError, AttributeError, TypeError))` — it pins the **opposite** of its own name, so T6's DoD reads as covered when it isn't. Not CLI-reachable today (`build_release_map` always returns a well-formed dict) so not a Blocker, but `build_feature_lens` is public library surface and the `library` lens requires documented error behavior; the sibling `run_feature_lens_report` already does exactly this catch (`featurelens_report.py:180`). **Fix:** add the documented boundary catch; retarget the test to `pytest.raises(ReleaseMapUnreadableError)`. | **fixed, re-verified** — `featurelens.py:142-145` wraps the body in `try/except (KeyError, TypeError, AttributeError)` → `ReleaseMapUnreadableError`, exactly as plan §1.3 pinned; the guard test now asserts the named error and its name matches what it proves. I swept **25** malformed shapes, 22 beyond the two the developer tested (`releases` as str/dict/list-of-int/list-of-None, missing `members`/`name`/`status`/`delivery`/`tag`/`delivered_in`/`date`, `status` as list/None, `spec` entry None, an unhashable list `name`, `release_map` as list/str/int, and mixed-type `spec_date` tripping the sort comparator): **every one** raised `ReleaseMapUnreadableError`, zero raw leaks. Mutation-checked: neutering the `except` clause turns the guard test red. |
| F3 | Minor | `src/aspark_insights/gitboard/featurelens.py:87-102`; `tests/test_featurelens_gate.py:150-157` | `delivered_in` is **not** read from the delivering occurrence. The loop `continue`s on the first occurrence of a name and reads `release["tag"]` only if *that* occurrence carries `delivering: True` — i.e. the shipped oldest-occurrence rule re-expressed, which plan §1.1 and A4/ADR-0 explicitly forbade. Correct today only because `_attribute_delivery` (`releasemap.py:163-192`) happens to stamp the first occurrence. I fed it a release map whose delivering occurrence is second: it returns `delivered_in: null, delivered_in_reason: null` (a reason-less null again) and renders `unavailable`. The test named `..._read_from_delivering_occurrences_own_release_tag` uses a single-release map and cannot distinguish the two readings. **Fix:** scan a feature's occurrences for `delivery["delivering"] is True` and take that release's tag, else fall back to a trailing occurrence's own `delivery["delivered_in"]`; add a delivering-is-not-first fixture. | **fixed, re-verified** — `featurelens.py:95-109` is now an order-independent scan; `delivering: True` overwrites unconditionally and pops any earlier reason. Re-broken with fixtures unlike the developer's: delivering scanned **last of three** (trailing decoys carrying `v9.9.9`) → `v3.0.0`; delivering **4th of five** with the pseudo-release last → `v4`; delivering last where the earlier trailing carried a *wrong* tag → the delivering tag wins; reason-set-first-then-delivering exercises the `pop` path correctly. Reason-less-null hunt: a trailing-only occurrence whose own `reason` is `None` yields `"delivery status could not be determined"`, not a bare null. **No regression from the loop rewrite:** AC-1.1/1.2 dedup holds (one feature across 6 releases → 1 row; 3 interleaved features → 3 rows, correct tags; real repo 11 unique rows) and the `status` map is still read from the first occurrence only. The developer's new test did **not** pin this → **F11**. |
| F4 | Minor | `tests/test_featurelens_gate.py:52-66` | The NFR-8 import guard's `assert "gitread" not in imported` was a tautology: it collected only `module.split(".")[0]`, so every real form (`from aspark_insights.gitboard import gitread`, `from …gitread import x`, `import …gitread`) normalizes to `aspark_insights` and could never trip it — proved by running the collector over those four import forms. **Fixed:** now collects every dotted segment plus every imported name, and also bans `Path`/`os`. Mutation-verified — injecting a real `gitread` import into `featurelens.py` makes the test fail; restored afterwards. | fixed |
| F5 | Minor | `tests/test_featurelens_security.py:14-17` | `render_feature_lens_html` imported and never used — dead code in a security-critical test module. **Fixed:** import removed. | fixed |
| F6 | Minor | `tests/test_featurelens_pipeline.py:63-78` | Writes to a hardcoded `/tmp/fl-pipeline-check` instead of pytest's `tmp_path`: not isolated, not parallel-safe, leaves state between runs, and a pre-created symlink at that predictable path in a shared `/tmp` would redirect the write. Its name also claims "lists all eleven" but it never asserts eleven — only that exactly one bucket is populated. **Fix:** take the `tmp_path` fixture, and assert the eleven `<li>` names the name promises (or rename the test). | **fixed, re-verified** — now takes `tmp_path` and asserts all eleven named features appear in the `Released` bucket, matching its own name. `grep` confirms no `/tmp` write path remains anywhere under `tests/`. The eleven-name assertion is live, not decorative: mutating the `<li>` markup turns it red. |
| F7 | Minor | `src/aspark_insights/gitboard/featurelens_report.py:123-138` | The pipeline section renders a gate label (`<h3>Increment</h3>`) with bare feature names beneath it — the one place on the page a gate name appears without artifact evidence, against NFR-5's literal "never shown without the literal status string of the artifact it was derived from". AC-3.1 does design the buckets as plain headed groups and the table on the same page carries every feature's evidence, so the reading is defensible either way — but it should be decided here, not re-litigated at `/demo-day`. **Fix:** append `_gate_evidence_text(m["gate_evidence"])` to each `<li>` (one line), or record the accepted reading explicitly in this report. | **fixed, re-verified** — option 1 applied: `featurelens_report.py:141-145` calls the **same** `_gate_evidence_text()` the table's gate cell calls (`:92`), so there is one implementation, not two. Proven, not assumed: I parsed the real rendered page with `html.parser` and compared each of the 11 `<li>` evidence strings against that same feature's own `<td>` gate cell — **11/11 byte-identical**, 0 mismatches, and each feature appears in exactly one `<li>`. The T4 zero-interactive-element claim survives the change (tag histogram still has no `a`/`button`/`input`/`select`/`textarea`/`details`/`script`/`svg`/`iframe`/`form`). |
| F8 | Nit | `tests/test_featurelens_determinism.py:65-71,74-88` | Two decorative assertions. `test_page_has_no_external_reference…` omits T7's third DoD pattern (protocol-relative `//`). `test_edge_repo_shapes_render_without_error` asserts `"Traceback" not in html`, which can never be false — a failure raises before any HTML exists; the real check is "it didn't raise". **Fix:** assert the `//` pattern; replace the vacuous assert with a structural one (e.g. `html.startswith("<!DOCTYPE html>")`). | **fixed, re-verified** — both applied as suggested (`src="//"`/`href="//"` asserted; the vacuous `"Traceback"` assert replaced by `startswith("<!DOCTYPE html>")` + `endswith("</html>")`). Mutation-checked, not just read: injecting `<link href="//cdn.example.com/x.css">` into the page head turns the external-reference test red, so the new assertion is genuinely load-bearing. |
| F9 | Nit | `tests/test_featurelens_closeout.py:48-55` | The NFR-2 guard reads `git status --short`, so it becomes vacuously true the moment this increment is committed (a clean tree yields zero lines; the loop body never runs). NFR-2 genuinely holds — I verified it independently — but this test stops proving it after `/go-live`. **Fix:** diff against this feature's own merge-base instead, or drop the test and cite the diff in the release report. | **fixed, re-verified** — diffs against the fixed pre-increment commit `cb8b664` plus `git ls-files --others`, so it stays meaningful on either side of `/go-live`; `assert changed` makes it non-vacuous (it now fails if it finds nothing at all, which is what the old version silently did). Accepted trade-off, recorded not reopened: the first future increment that legitimately touches `gitboard/` will trip this guard and must retarget it — a loud, correct failure in exchange for a silent, vacuous pass. |

| F10 | Minor | `tests/test_featurelens_gate.py:199`, `tests/test_featurelens_fixtures.py:108` (both new) | **Raised at re-review.** F1's fix shipped with **no regression test at all** — the prescribed "add a fixture with a Date-less header table" was never added. Proven, not inferred: I reverted the fix to `spec_date_reason = spec_entry["reason"]` and re-ran **all 67** featurelens tests — all still green. So the exact NFR-5 hole this review escalated to Major could be reintroduced tomorrow with a clean suite. **Fix:** add a discriminating test at both levels. | **fixed by reviewer** — added `test_status_row_present_but_no_date_row_still_names_a_date_reason` (unit) and `test_spec_with_status_row_but_no_date_row_names_its_own_date_reason` (real git repo, the fixture F1 originally prescribed). Mutation-verified: both fail on the reverted code, both pass on the shipped code. |
| F11 | Minor | `tests/test_featurelens_gate.py:287`, new sibling at `:313` | **Raised at re-review.** F3's new test `test_delivering_occurrence_wins_even_when_scanned_after_a_trailing_one` **passes against the very bug it was added to pin**. Its trailing occurrence carried `delivered_in="v0.5.0"` — the same tag the delivering occurrence would yield — so the buggy first-occurrence-only read and the fixed scan return the identical value. I reconstructed the original loop exactly and ran all 67 featurelens tests: green, while my own probe showed the reverted code returning the *wrong* tag (`v9.9.9` instead of `v3.0.0`). This is the third guard in this feature that asserted less than its name claimed (cf. F2, F4). **Fix:** give the trailing occurrence a decoy tag so the two readings differ. | **fixed by reviewer** — trailing occurrence now carries `v0.1.0-decoy` with an explicit `!=` assertion, plus a new `test_delivering_occurrence_wins_when_scanned_last_of_three_occurrences` (delivering scanned last of three, both decoys) that also asserts the dedup invariant. Mutation-verified: both fail on the reverted loop. |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `featurelens.py:62-126`, `cli.py:298-315` | ✅ 11 features, each exactly once, own 5-artifact map verbatim; `.lens-table` wrap rule at `featurelens_report.py:46` |
| AC-1.2 | `featurelens.py:95-109` | ✅ ran it: `release-board-docs` → one row, `delivered_in: "v0.10.0"`, no `v0.11.0` entry. Re-checked after the F3 loop rewrite: real repo still 11 rows / 11 unique names, and 6-occurrence + interleaved-3-feature synthetic maps each dedup correctly |
| AC-1.3 | `featurelens.py:96-97` | ✅ my own post-tag fixture feature → `delivered_in: null`, reason `not yet delivered in a tagged release` verbatim |
| AC-1.4 | `featurelens.py:114-118` | ✅ now all four degrade paths name a reason — missing / unreadable / no-header-table / **Status-present-but-no-Date-row** (F1 fixed, re-broken on my own new git fixture, pinned by F10's two tests) |
| AC-1.5 | `featurelens_report.py:112-120` | ✅ real `<table class="lens-table">` in `.table-wrap`, 9 `<th scope="col">`, header `spec.md's own Date (last updated)` verbatim, order date-desc/name-asc/undated-last confirmed, reason only when status is null |
| AC-2.1 | `featurelens.py:25-48`, `featurelens_report.py:87-96` | ✅ all six values + evidence pairing reproduced on my own six-stage fixture (`plan: approved, review: file not found`, `spec: no header table found`, …) |
| AC-2.2 | real data | ✅ 11/11 gate `Released`, each with its own `release.md` literal status |
| AC-2.3 | fixture | ✅ approved `plan.md`, no `review.md` → `Increment` |
| AC-2.4 | `featurelens.py:47-48` | ✅ header-table-less `spec.md` → `Unknown` + its own reason, never guessed as `Spec` |
| AC-2.5 | `featurelens_report.py:45-56,87-96` | ✅ exactly one `.gate-badge` CSS rule, one non-artifact hue, no inline style, no `<progress>`/`<meter>`/track markup — parser-confirmed on a render containing all six values |
| AC-3.1 | `featurelens.py:132-140` | ✅ every feature in exactly one bucket; rendered markup is `<h3>` + `<ul>` only |
| AC-3.2 | `featurelens_report.py:123-148` | ✅ `Released` lists 11 (each now with its own gate evidence), every other bucket gets its own `<h3>` + `.empty-notice` sentence (contrast/type-scale measurement is T8) |
| AC-3.3 | fixture | ✅ each of the six buckets shows exactly its one expected feature |
| AC-3.4 | `featurelens_report.py:152` | ✅ single call site; removing it leaves the Must-level table path untouched |
| NFR-1 | `cli.py:133-148,298-315` | ✅ flags mirror `releases`/`board`; no new error class; `--format html` prints only `{"report": <path>}`; `--help` documents the write location |
| NFR-2 | diff | ✅ measured: `git status --short src/aspark_insights/gitboard/` lists only the two new files; `cli.py` purely additive; zero new deps; `uv.lock` is a version-only change; **749 tests green** |
| NFR-3 | `featurelens_report.py` via `render.py:79-81` | ✅ my own fresh hostile fixture through both formats: exit 0, no traceback; `html.parser` reports **no** `script`/`svg`/`iframe` tag and **no** `on*` attribute — payloads present only as escaped text |
| NFR-4 | `featurelens_report.py:45-56,112-120` | ⚠️ structural half met and verified (single `<h1>`, `h1→h2→h3` with no skip, real table, `scope="col"`, zero interactive elements, per-cell wrap); contrast + 375px are T8/`/demo-day` |
| NFR-5 | `featurelens.py`, `featurelens_report.py` | ✅ F1 and F7 both closed and re-broken: every degrade path names a reason (four `spec.md` shapes + two delivery shapes probed), and the gate is now paired with evidence in **both** surfaces — 11/11 pipeline `<li>` strings byte-match their own table cell under a real HTML parser. Date header verbatim, no derived duration, no person-level field read. Residual, not a finding: an artifact whose `**Date**` cell is literally empty renders an empty cell — the shipped release board (`releaseboard_report.py:242`) does the same, and rendering the artifact's own literal content is the read-never-re-derive rule, not an invented value |
| NFR-6 | `featurelens.py`, `featurelens_report.py` | ✅ measured: two runs byte-identical in both JSON and HTML (re-measured after the F3/F7 changes); no `datetime.now`/`date.today` in either module |
| NFR-7 | `featurelens.py:77-83`, `featurelens_report.py:146-147` | ✅ zero-tag / zero-feature / one-feature / full-history all render; empty cases state their own reason; only external reference is a `data:` URI logo |
| NFR-8 | `featurelens.py` | ✅ measured with a `subprocess.run` counter: `build_release_map` makes 214 git calls in 15.5 s, `build_feature_lens` adds **0** calls and 0.1 ms |

## 5. What Was Checked

- [x] Correctness: logic does what the acceptance criteria demand — every Must AC re-derived from my own fixtures, not from the developer's tests; every fix re-broken at re-review with fresh inputs
- [x] Non-functional: applicable NFRs and constitution quality bars hold — the honest-null gap is closed on all four `spec.md` shapes and both delivery shapes; ADR-0/ADR-4/ADR-5, §3 no-second-git-parser and §6 no-person-level-data all hold
- [x] Error handling: failures are handled, not swallowed — CLI paths named and clean; the promised library boundary now exists and caught 25/25 malformed shapes I threw at it
- [x] Security: no injected input trusted, no secrets in code — `cli` + `security` lenses traced; escaping verified with a real HTML parser on my own payloads; re-parsed after the F7 markup change (still zero script/svg/iframe/interactive elements)
- [x] Tests: exist, are meaningful, and pass — 749 green, and I stopped trusting names: five mutations reverting each fix proved F2/F6/F7/F8's guards live, and exposed two that were not (F10, F11), now fixed and mutation-verified
- [x] Readability: the next developer will understand this — docstrings tie each function to its AC and now record *why* the delivery scan is order-independent rather than restating the old first-occurrence rule

## 6. Verdict

This is a genuinely well-built increment and it survived the adversarial passes this project's own
CLAUDE.md demands. I did not take a single claim on the developer's word: I built my own six-stage git
repo and got all six gate values with correct evidence pairing; I built my own hostile fixture with
different payloads and parsed the output with a real HTML parser rather than grepping for `<script`,
finding zero dangerous tags, zero `on*` attributes and zero interactive elements — which independently
confirms the T4 deviation is not just defensible but strictly stronger than the DoD it replaced; I
confirmed the developer's `/`-in-a-directory-name reasoning by accidentally reproducing the failure
mode myself; and I counted git subprocess calls to show NFR-8's "zero extra calls" is literally true
(214 → 214, 0.1 ms of added work), which is the kind of claim that usually goes unmeasured. The
architecture holds: nothing shipped was touched, and both views really are one computation.

**Re-review (2026-08-26): this passes.** Every one of the seven fixes holds in behavior, and I
established that by trying to route around each one rather than by reading the patch. F1: a brand-new
git repo with four hostile `spec.md` shapes — Date-less table, Date-before-Status, empty Date cell,
neither row — and the Date-less feature now reports `no Date row found in header table`, never a
reason-less null. F2: I threw 25 malformed shapes at `build_feature_lens`, 22 of them beyond the two
the developer tested, including `releases` as a string, an unhashable list as a feature name and a
mixed-type sort comparator; all 25 raised `ReleaseMapUnreadableError` and nothing leaked raw. F3: the
scan is genuinely order-independent, not fixed for one case — delivering last of three, fourth of five,
and delivering-last-with-a-wrong-tag-decoy all return the delivering release's own tag. The structural
rewrite of that loop did **not** cost anything it wasn't meant to: dedup still holds (real repo 11
unique rows; a feature spanning six releases still yields one), and the `status` map is still read from
the first occurrence only. F7 I checked the way it should be checked — not "is a span present" but
whether the pipeline text is the *same* text: parsed with `html.parser`, all 11 `<li>` evidence strings
are byte-identical to their own row's gate cell, because both call one `_gate_evidence_text`.

The honest part. Two of the seven fixes shipped with a regression test that did not actually pin them,
and I only found that because I reverted each fix and re-ran the suite instead of trusting the green
tick. F1 had no test at all — all 67 featurelens tests stayed green with the fix removed. F3's new test
passed against a faithful reconstruction of the original bug, because its trailing occurrence carried
the same tag the delivering one would yield, so the two readings were indistinguishable. That is the
third and fourth guard in this feature asserting less than its name claims (after F2's and F4's), which
is a pattern worth carrying into the release report as a process item, not just four separate rows. I
closed both myself — test-only, no design impact, and each mutation-verified to go red on the reverted
code. `749 passed, 0 failed`. Nothing shipped was touched; the two `gitboard/` modules are byte-for-byte
what the developer wrote. T8 remains genuinely unverified and is `/demo-day`'s to measure: contrast
ratios, 375px scroll behavior and DOM byte-order are not things this review has any evidence about.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings — none were ever raised
- [x] No open Major findings — **F1** and **F2** were the only two, both fixed and independently re-broken at re-review (fresh git fixture; 25/25 malformed shapes caught). No waiver was needed or given
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — AC-1.4 is now ✅ on all four degrade paths; "never a raw traceback" holds on every CLI path I probed, and now on the library boundary too
- [x] All plan deviations documented and accepted — T4's interactive-element deviation independently verified and accepted (and re-verified after F7's markup change); T8 correctly deferred to `/demo-day`; plan §1.3's error boundary now implemented as written
- [x] Test suite runs green — **749 passed, 0 failed**, re-run by the reviewer after their own three added tests
- [x] Status set to `passed`
