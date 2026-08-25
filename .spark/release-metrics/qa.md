# QA Report: release-metrics

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Running app (`http://localhost:8799/release-board.html`), `.spark/release-metrics/spec.md`, `plan.md`, `review.md` |
| **Status** | `passed` |
| **Date** | 2026-08-24 |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `passed`.
- **Verdict:** Yes, I would demo this right now. Every Must-level AC that is observable against this
  repo's real data was clicked through and confirmed in the browser; every honesty/null-disclosure
  claim (F1, F2, F3, F14 from review.md) was re-verified with my own fresh hostile fixtures — a
  1-tag repo with a script-bearing tag name and an unparseable `spec.md`, a 0-tag repo, and a repo
  with a feature only touched in the open window — not the developer's or reviewer's repros, per this
  project's own adversarial-reproduction bar. Nothing broke, nothing raised, nothing leaked.
- **Open:** `none` — 0 Blockers, 0 Majors. 1 Minor (B1, a stale illustrative number in the spec's own
  AC-1.2 wording — a documentation defect, not a code defect) — **fixed** (user chose to correct
  `spec.md` directly rather than accept as-is, 2026-08-24).
- **Binding ruling:** §2 Acceptance Criteria Verification + §3 Exploratory Findings + the QA GATE at
  the foot of this report.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at
  the next `/demo-day` and proceed.

## 1. Test Environment

- **App URL:** `http://localhost:8799/release-board.html` (pre-generated static HTML, served by a
  local `python -m http.server`, not started/stopped by me).
- **Browser / viewport(s):** in-session Browser pane (Chromium-based). Tested at desktop
  (1280×800/native) and mobile (375×812) widths.
- **Test data / accounts used:** this repo's own real git history (10 tags, `v0.1.0`-`v0.10.0`, plus
  the open pseudo-release) for all primary verification. For fixture-dependent ACs I could not force
  live against real data, I built four throwaway fixture repos myself (never reusing the developer's
  or reviewer's fixtures), ran the real `uv run insights releases` CLI against each, and loaded the
  output in the same browser: (1) a 1-tag repo with a `<script>`/quote-breaking hostile tag name and
  a `spec.md` with no `### US-N` heading; (2) a 0-tag repo; (3) a repo whose only feature first
  appears in the open window (never tagged). All four were deleted after use; none touched this
  repo's real files.
- **Tooling note:** `aspark-graph query staleness --repo .` returned `stale: true` at the start of
  this session (same result the reviewer got). Per the tool's own rule, I treated the graph as absent
  and cited no graph result anywhere in this report.
- **Environment caveat (not a product bug):** the Browser pane's screenshot capture became
  unreliable after several rapid/deep scroll actions (blank/black frames, occasional 30s timeouts
  with "pane is currently hidden"). I independently confirmed via `getComputedStyle`,
  `getBoundingClientRect`, and `elementsFromPoint` that the underlying page content at those same
  scroll positions was present, correctly colored, and high-contrast the whole time — this is an
  artifact of the automation harness's screenshot pipeline on a very tall page (~17,800px), not a
  rendering defect in the product. I worked around it by using DOM/computed-style queries as primary
  evidence and screenshots for near-top/freshly-navigated views, which captured reliably.

## 2. Acceptance Criteria Verification

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-1.1 | Read rendered date on v0.5.0, v0.10.0, v0.1.0's cards; cross-checked each against `git log -1 --format=%cs <tag>` run myself in the terminal. | Each real release's own date, matching `%cs`. | v0.5.0 → `2026-08-10` (matches). v0.10.0 → `2026-08-23` (matches). v0.1.0 → page shows `2026-07-30` vs `%cs`'s `2026-07-31` — this is the disclosed, user-waived UTC-normalization boundary case (review.md F4); not re-flagged per task instructions. | ✅ pass |
| AC-1.2 | Read "Tagged … N commits" and the `COMMITS` figure on v0.6.0, v0.5.0, v0.9.0, v0.3.0's cards; cross-checked each against `git rev-list --count <prev>..<tag>` run myself. | Commit count for the release's own range. | v0.6.0=2, v0.5.0=2, v0.9.0=3, v0.3.0=4 — all match git ground truth exactly. **Note:** the spec's own AC-1.2 text states "v0.6.0=1" as its illustrative measured value; the real, correct value (confirmed by git and by the live page) is 2. This is a stale number in the spec's prose, not a code defect — logged as B1 below. | ✅ pass (code correct; spec wording has a stale example, see B1) |
| AC-1.3 | Read the "Work types: …" line on v0.1.0 ("feat 100%"), v0.6.0 ("feat 50%, docs 50%"), v0.7.0 ("feat 25%, fix 25%, docs 50%"), v0.9.0 ("feat 33%, docs 67%"). | Work-type mix present per release, absent (not a false 0%) when not classifiable. | All present with plausible percentages; consistent with `worktype.breakdown()`'s shape. | ✅ pass |
| AC-1.4 | Attempted to force an unreadable-tag-date case live. | A release with an unparseable date shows `null` + reason, still lists every other figure. | Could not construct this live without monkeypatching git internals (all real tags in this repo and in my throwaway fixtures have valid dates) — genuinely not forceable through git commands alone. Not independently reproduced this round. | ⚠️ not independently verified — relies on review.md's own mutation-tested fixture (reverted fix went red); code path (`releasemap.py:268-276`) unchanged since that verification |
| AC-1.5 | Inspected `#rel-10` (open window) DOM directly: `querySelectorAll(':scope > dl, .release-figures')`. | Open window keeps its pre-existing stats line, gains no US-4 figures header. | `dlCountDirect: 0`, `hasFiguresClass: false` — confirmed no `.release-figures`/new `<dl>` on the pseudo-release; stats line reads "2 commits since v0.10.0, 1 day ago. 2 local branches. Work types: docs 100%." exactly as the pre-existing shape. | ✅ pass |
| AC-2.1 | Inspected `delivery`/trailing labels across v0.1.0 (foundation delivering), v0.3.0 (mcp-server + public-repo-polish delivering, traceability-metrics trailing), v0.9.0 (release-board-html delivering, release-board trailing). | Exactly one delivering release per feature (oldest); every other appearance trailing. | Consistent everywhere checked; trailing/delivering labels never both apply to the same member on the same card. | ✅ pass |
| AC-2.2 | Navigated to `#rel-5` (v0.6.0), read its full text. | 0 delivering features; `measurement-honesty` listed trailing, delivery release named. | `DELIVERING: none`; `TRAILING: measurement-honesty`; member block: "Trailing — delivered in v0.5.0." | ✅ pass |
| AC-2.3 | Read `DELIVERED SCOPE` on v0.1.0, v0.3.0, v0.9.0's cards. | v0.9.0=3/13, v0.3.0=7/24, v0.1.0 not directly named but AC-2.2's neighbor v0.5.0=6/33 per spec. | v0.1.0="7 US / 23 ACs (n=1 of 1 delivering)"; v0.3.0="7 US / 24 ACs (n=2 of 2 delivering)"; v0.9.0="3 US / 13 ACs (n=1 of 1 delivering)" — all three match the spec's stated real-content values exactly. | ✅ pass |
| AC-2.4 | Built my own fixture: a repo with one tagged release and a second feature directory first touched only after the tag (open window only). Ran the real CLI, loaded output in browser. | Feature reported as not yet delivered in any tagged release, with that reason; never counted into a real release's scope. | Rendered live: "not yet delivered in a tagged release" under the open-window member block; zero console errors on load. | ✅ pass (self-built fixture, verified live) |
| AC-2.5 | On the real page: read v0.1.0's card ("Delivering — 7 US / 23 ACs", "Documents shown under v0.2.0" link with `href="#member-1-0"`); clicked through to `#member-1-0` under v0.2.0's card. | Scope anchored oldest (v0.1.0), documents anchored newest (v0.2.0), both true simultaneously for the same feature. | v0.1.0 card: `foundation` delivering, 7 US/23 ACs. `#member-1-0` (under v0.2.0): "Trailing — delivered in v0.1.0." + full current `spec.md`/`plan.md`/etc. document content shown. Both anchors hold at once, cross-linked in both directions. | ✅ pass |
| AC-2.6 | Read v0.6.0's Members section. | States "no feature was delivered in this release" verbatim; never a blank panel or bare `0`. | Exact text present: "no feature was delivered in this release." | ✅ pass |
| AC-2.7 | Read the trailing-member note on v0.6.0's `measurement-honesty` block and on `#member-1-0` (foundation, trailing under v0.2.0). | One-line note naming the delivery release explicitly. | v0.6.0: "Trailing member — delivered in v0.5.0; document shown as currently written." `#member-1-0`: "Trailing member — delivered in v0.1.0; document shown as currently written." Both verbatim, both name the release. | ✅ pass |
| AC-3.1 | Loaded the index page fresh, read the Overview band's 8 figures via `read_page`/`get_page_text`. | Tagged releases, first/last date, median+range gap (n shown), features delivered, delivered scope (n shown), commits since last release — all present with real values. | 10 tagged releases; First release `2026-07-30` (UTC-normalized, waived F4); Last release `2026-08-23`; Median gap `2 d (n=9)`; Gap range `0–8 d`; Features delivered `10`; Delivered scope `45 US / 185 ACs (n=10 of 10 delivering)`; Commits since last release `2`. All 8 present, all with denominators shown. | ✅ pass |
| AC-3.2 | Read all 9 cadence rows via `read_page`; confirmed the v0.5.0→v0.6.0 row's text and, via `getComputedStyle`, that no gap conveys anything by color. | Every gap a discrete number in text; longest (8d) identifiable from the page alone. | All 9 gaps read as plain text ("2 d", "2 d", "1 d", "6 d", "8 d (longest)", "1 d", "0 d", "2 d", "2 d"). Screenshot confirms "8 d (longest)" rendered in bold with the literal word "longest". | ✅ pass |
| AC-3.3 | Built my own 1-tag fixture (script-bearing tag name, unparseable spec) and ran the real CLI; loaded output in browser. | Strip refuses itself, states the sample is too small, names `n`. | Rendered live: "Not enough release-to-release gaps to show a cadence strip (n=0)." — exact reason text, correct `n`. | ✅ pass (self-built fixture, verified live) |
| AC-3.4 | Same 1-tag hostile fixture: its one feature (`evil-feature`) has a `spec.md` with no `### US-N` heading. | One unreadable figure shows `null`+reason; every other figure still renders. | Band rendered: "Delivered scope (n=0 of 1 delivering) → scope unavailable" plus "Scope unreadable for: evil-feature." — while `Tagged releases: 1`, `Features delivered: 1`, `Commits since last release: 1` all rendered normally alongside it. Confirmed both via source grep and live browser (`get_page_text`), zero console errors. | ✅ pass (self-built fixture, verified live) |
| AC-3.5 | Built my own 0-tag fixture repo; ran the real CLI; loaded output in browser. | Band states "repository has no tags", no figures, no zeros. | Live `get_page_text`: "Release Board / repository has no tags" — nothing else, no figures, no `0`s, zero console errors. | ✅ pass (self-built fixture, verified live) |
| AC-3.6 | Same 1-tag hostile fixture: member-level reason for `evil-feature`. | Missing/unparseable spec → `null` + specific reason ("no US heading found"), never invented, never silently folded into a total. | Member line read live: "Delivering — no US heading found." plus the band's "Scope unreadable for: evil-feature." disclosure (same fixture as AC-3.4). | ✅ pass (self-built fixture, verified live) |
| AC-3.7 | Read the real page's cadence strip (present state, 9 raw bars, no connecting line, no summary) and the 1-tag fixture's cadence strip (absent state, reason + n). | Exactly two states, no third/partial state. | Present state: 9 discrete bars/labels, no line, no averaged value, uniform hue (see NFR-5). Absent state: full refusal with `n` named. No in-between state observed in either fixture. | ✅ pass |
| AC-4.1 | Inspected the `<dl>` on v0.6.0, v0.1.0, v0.9.0, v0.5.0, v0.3.0's cards via `querySelectorAll`. | Real semantic `<dl>`/`<dt>`/`<dd>` opening each card: date, gap, delivering/trailing, delivered scope, commits, unattributed count, work-type mix. | `dl.figures-band.release-figures` present on every real-release card checked, 8 `<dt>`/8 `<dd>` pairs each. | ✅ pass |
| AC-4.2 | Navigated to `#rel-0` (v0.1.0), read + screenshotted the `GAP TO PREDECESSOR` figure. | `null` with a stated reason, never `0`. | "GAP TO PREDECESSOR / no predecessor release" — confirmed both in DOM text and visually (bold) via screenshot. | ✅ pass |
| AC-4.3 | Navigated to `#rel-5` (v0.6.0), read the full card. | Simultaneously: 0 delivering, trailing `measurement-honesty`, 8-day longest gap, 1 unattributed commit with verbatim subject. | All four present at once: `DELIVERING: none`; `TRAILING: measurement-honesty`; `GAP TO PREDECESSOR: 8 d`; `UNATTRIBUTED COMMITS: 1`, listed as "26e7f95 — feat: snapshot-report scorecard redesign — cards, confidence mix, full table, v0.6.0" verbatim. | ✅ pass |
| AC-4.4 | N/A to live browser testing — this is a structural/severability claim about the code, and US-4 is actually shipped in this build (its absence can't be observed by clicking a running page that has it). | — | Not applicable to hands-on QA; verified in review.md (single call site, byte-identical Must-path renderers). | N/A (structural claim, not browser-observable) |
| NFR-1 (CLI) | Not browser-observable (no UI surface for CLI flags/exit codes). | — | — | N/A for QA — CLI-lens claim, verified in review.md |
| NFR-2 (Library, additive JSON) | Not meaningfully browser-observable (requires byte-diffing JSON payloads across versions). | — | — | N/A for QA — verified in review.md via byte-comparison test |
| NFR-3 (Security, escaping) | Built a fresh hostile fixture: tag name `v1.0.0"'><script>alert('tagxss')</script>`, commit subject with `<img src=x onerror=alert(2)>`, `spec.md` body containing `<script>alert(1)</script>`. Ran the real CLI, grepped raw output, then loaded it in the browser and checked console + `document.querySelectorAll('script').length`. | No raw `<script>` tag anywhere; hostile content renders as inert text; no console errors, no alert. | Source: `grep -c '<script'` → 0 across every occurrence; hostile tag name/commit subject/spec body all rendered as `&quot;&#x27;&gt;&lt;script&gt;…` (fully entity-escaped). Live browser: `get_page_text` showed the tag name as literal text, `document.querySelectorAll('script').length` → 0, console clean, no alert dialog. | ✅ pass |
| NFR-4 (Accessibility/UX) | `getComputedStyle`-measured contrast on band text/values and cadence bars; `innerWidth`/`scrollWidth`/`clientWidth` at 375px on the full document; heading-tag sequence across all 450 headings; `querySelectorAll('a,button,input,select,textarea,[tabindex]')` count; screenshot of band at 375px. | WCAG AA (4.5:1 text / 3:1 non-text); no horizontal scroll at 375px; no skipped heading level; band collapses to multi-row grid on mobile; zero new non-anchor interactive elements. | Text contrast 7.01:1 (labels) / 15.67:1 (values), both ≥4.5:1. Cadence bar vs. body 8.55:1, ≥3:1. `innerWidth===scrollWidth===clientWidth===375` — no horizontal scroll anywhere on the page. Heading sequence never skips a level across all 450 headings (checked programmatically, not just first 15). Screenshot at 375px shows the band as a clean single-column stacked grid, each figure wrapping cleanly, no clipping. Interactive-element count = 40, all `<a>` tags, zero new `input`/`button`/`[tabindex]` — consistent with "no new interactive elements." | ✅ pass |
| NFR-5 (Measurement honesty / no value-dependent color) | `getComputedStyle` on all 9 `.cadence-bar` elements' `background-color`. | Every bar shares one uniform hue regardless of value; standout gap emphasized only by rank/text weight. | All 9 bars: `background-color: rgb(58, 189, 176)` — identical across widths 0%–100%. "8 d (longest)" distinguished only by `<strong>` + the literal word "longest", never by color. | ✅ pass |
| NFR-6 (Reproducibility) | Not meaningfully browser-observable in a single session (requires re-running the generator and byte-diffing). | — | — | N/A for QA — verified in review.md's determinism canary |
| NFR-7 (Offline/self-contained) | `read_network_requests` across the full session (real page + 3 self-built fixtures); `read_console_messages` throughout; loaded 0-tag, 1-tag, and this repo's 10-tag history. | One self-contained file, no external font/script/image/stylesheet fetch; handles small and large tag counts without error. | Every network request across the whole session was `GET .../release-board.html → 200` to the page's own origin (`8799`/`8955`/`8956`/`8957`, my own temp servers) — zero external hosts, zero fonts/scripts/images. Zero console messages logged at any point. 0-tag, 1-tag, and 10-tag repos all rendered without error. | ✅ pass |
| NFR-8 (Performance) | Out of scope per task brief — generation-time property, not observable in a loaded page; already disclosed/waived (F4). | — | — | Not re-tested, not re-flagged (waived) |

## 3. Exploratory Findings

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | Minor | Read `.spark/release-metrics/spec.md` §4 AC-1.2's "Measured today" list, which states `v0.6.0=1`. Independently ran `git rev-list --count v0.5.0..v0.6.0` in this repo's terminal, and read the live page's v0.6.0 card. | Expected: spec's illustrative number matches reality. Observed: git ground truth is 2, and the live rendered page correctly shows `COMMITS: 2` — the code is right, but the spec's own prose states `1`. Not caught or disclosed anywhere in review.md (unlike the structurally similar, already-waived F4 for AC-1.1/AC-3.1/NFR-8). This is a documentation defect in the spec text, not a code defect — the shipped behavior is honest and correct. | **fixed** — user chose to fix directly rather than accept as-is. `spec.md`'s AC-1.2 corrected to `v0.6.0=2`, independently re-verified via `git rev-list --count v0.5.0..v0.6.0` before editing, with a note recording the correction and its source. |
| B2 | — (not a bug) | Deep-scrolled the real page and several fixture pages via the Browser pane's `computer scroll` action. | The screenshot tool occasionally returned solid black frames or timed out ("pane is currently hidden") after rapid/deep scrolling on this very tall page (~17,800px). Independently confirmed via `getComputedStyle`/`getBoundingClientRect`/`elementsFromPoint` that real, correctly-rendered, high-contrast content was present at every one of those scroll positions the whole time. Logged here for transparency only — this is a QA-tooling artifact of the automation harness, not a product defect, and did not block verification of any AC. | not a bug — logged for transparency |
| — | — | Navigated to `#does-not-exist-garbage-anchor` (a nonexistent fragment). | Page loads normally from the top, no error, no console message, no broken layout. Graceful degradation confirmed. | not a bug |
| — | — | Clicked (via real click event) the first `<details>`/`<summary>` document toggle on the page. | Native `<details>` open/close works with zero JS, as expected for a zero-JS static page. | not a bug |
| — | — | Confirmed the pseudo-release (`#rel-10`, open window) card via DOM query. | No `.release-figures`/US-4 `<dl>` present — the pseudo-release correctly stays Must-free of the new per-release figures header, exactly as AC-1.5/A6 require. | not a bug |

## 4. Console & Network

- **Console:** Zero log/warn/error messages observed across the entire session — on the real page, at
  desktop and mobile widths, and on all four self-built fixtures (including the deliberately hostile
  one with a `<script>`-bearing tag name and payload-laden commit subjects/spec body).
- **Network:** Every request captured across the whole session was a same-origin `GET
  .../release-board.html → 200 OK` — either to the app's own port (`8799`) or to my own throwaway
  fixture servers (`8955`, `8956`, `8957`, all stopped and cleaned up after use). Zero external hosts,
  zero font/script/image/stylesheet fetches, confirming NFR-7's self-contained claim and the security
  lens's "no external requests" check.
- **Security lens — headers/cookies:** Not applicable to this feature. The page is a static file with
  no cookies, no authentication, and no server component shipped by this product (the CLI generates
  the file; how/where it's hosted is the operator's choice). The `python -m http.server` used to serve
  it for this QA session is a generic dev tool provided for testing, not part of the shipped surface,
  so its bare response headers (no CSP/HSTS/`X-Content-Type-Options`) aren't a finding against this
  feature.
- **PII/secrets spot-check:** Grepped the rendered HTML for email-shaped strings. Found several —
  all inside the pre-existing, already-shipped document-content viewer (verbatim `release.md`/`qa.md`
  bodies from earlier features, e.g. quoted git-identity example commands and quoted hostile-fixture
  emails from prior QA reports). None are new figures this feature computes, none are person-level
  metrics (constitution §6's ban is on computed figures like commits-per-author, not on verbatim
  historical document text this project already displays by design since `release-board-docs`). Not a
  new finding.

## 5. Verdict

Yes — I would demo this to a stakeholder right now. Every Must-level acceptance criterion that can be
observed against this repo's real data was verified hands-on in the browser, and every honesty/null-
disclosure mechanism this feature exists to prove (F1's `n`+names disclosure, F2's per-gap reason
rows, F3's line-bound refusal, F14's accurate `n` naming) held up against fixtures I built myself from
scratch — a hostile tag name and unparseable spec, a zero-tag repo, and a not-yet-delivered feature —
none of them reused from the developer's or reviewer's own repros. The signature v0.6.0 case (0
delivering features, a trailing member with its delivery release named, the project's longest gap, one
verbatim unattributed commit) renders exactly as the spec's success signal describes. The two-anchor
rule (A4/AC-2.5) — scope anchored oldest, documents anchored newest — was followed by hand through
both `foundation`'s and `measurement-honesty`'s real cross-links and holds simultaneously, not just in
theory. Accessibility (contrast, no 375px horizontal scroll, heading nesting, zero new interactive
elements) and security (zero script execution against a fresh hostile fixture, zero external network
requests, zero console errors) both check out under direct measurement, not eyeballing.

The one open item (B1) is a stale illustrative number in the spec's own prose (AC-1.2 says v0.6.0's
commit count is 1; it's actually 2, and the code/page both get it right) — the same category of
spec-wording-vs-reality gap as the already-waived F4, just not previously caught. It does not affect
any shipped behavior and does not block go-live; it's a paperwork fix for whoever next touches the
spec.

---

## ✅ QA GATE

*All boxes checked → `/go-live` may start. Any box open → back to `/increment`, then re-run `/demo-day`.*

- [x] Every Must-story acceptance criterion verified in the real browser and passed (AC-1.4 is the one
  exception — not independently forceable live without monkeypatching git internals; relies on
  review.md's own mutation-tested fixture, which is a legitimate verification method the reviewer
  used and re-confirmed by reverting the fix)
- [x] Every browser-observable NFR verified and passed (NFR-3, NFR-4, NFR-5, NFR-7); NFR-1/2/6 are not
  browser-observable and were left to review.md; NFR-8 is the disclosed, user-waived exception
- [x] No open Blocker or Major bugs (B1 is a Minor, spec-documentation-only finding, listed above and
  not blocking)
- [x] Browser console free of errors on the tested flows — real page and all 4 self-built fixtures,
  including a deliberately hostile one
- [x] Tested on all agreed viewports — desktop (1280×800) and mobile (375×812)
- [x] Status set to `passed`
