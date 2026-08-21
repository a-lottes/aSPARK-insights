# QA Report: release-board-html

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Running app (`http://localhost:8792/release-board.html`), `.spark/release-board-html/spec.md`, `.spark/release-board-html/review.md` (status `passed`, verified myself before starting) |
| **Status** | `passed` (round 1: 2026-08-20; round-2 re-test after fix-mode, B1+B2 independently re-verified: 2026-08-20) |
| **Date** | 2026-08-20 |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `passed`.
- **Verdict:** Yes, I'd demo this right now. Every Must-story AC was clicked through and observed, including
  the three states no real-repo click-through can reach (zero-tags index, true-zero pseudo-release,
  >50-item truncation) — I built three throwaway synthetic repos and rendered real pages from them
  rather than reasoning about the code path. No Blocker or Major found.
- **Open:** `0 open, 2 fixed — both independently re-verified live in a second `/demo-day` pass
  (2026-08-20), not taken on the fixer's annotation alone`. B1: `v0.7.0`'s real `qa` Status cell
  read fresh from the live DOM now shows zero leading backtick, the Date cell's `` `8b4f9ff` ``/
  `` `99e4aae` `` backticks are untouched, and a plain single-word status (`v0.1.0`'s `spec` →
  "approved") still strips clean. B2: all 14 `<caption>` elements on the page read the literal text
  "Artifact status" (a `Set` of distinct caption texts has size 1), every one measured
  `scrollWidth === clientWidth` at 375px (zero clip, including the longest real member name,
  `git-native-mid-cycle-board`, whose `<h4>` above the table still renders the full name
  unclipped). Both fixed in one round at the user's explicit "fix both now" routing.
- **F6 ruling (mine, independently re-derived):** Legitimate WCAG 1.4.11 exemption, not a failure.
  See §2 NFR-5 row and §5.
- **Binding ruling:** §2 (AC table) + §3 (exploratory) + §5 (verdict) + the QA GATE below.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at
  the next `/demo-day` and proceed — don't stop on it.

## 1. Test Environment

- **App URL:** `http://localhost:8792/release-board.html` (real repo data, 8 tags `v0.1.0`-`v0.8.0`
  + pseudo-release, served by an already-running `python3 -m http.server 8792`).
- **Browser / viewport(s):** Claude Browser pane (Chromium). Desktop (native, ~1280px) and mobile
  375×812, both reloaded after resize.
- **Test data / accounts used:** This repo's real git history (no login, no accounts — a static
  offline page). Additionally, three throwaway synthetic git repos built and rendered live during
  this pass to exercise states the real repo's 9-entry board cannot reach:
  - `/tmp/rbh-zerotags` — one commit, zero tags (AC-3.1).
  - `/tmp/rbh-zerosince` — one tag, zero commits since (AC-3.2), plus a member with no `.spark/`
    artifact files at all (extends AC-3.3's reason coverage: `"no header table found"`, `"file not
    found"`).
  - `/tmp/rbh-bigdata` — one tag, 60 unattributed commits (NFR-4's >50 truncation boundary).
  All three were rendered with the real installed CLI (`python -m aspark_insights.cli releases
  --format html --output ...`), served on throwaway local ports, opened in the browser, verified,
  then torn down (servers killed) before writing this report. Only port 8792 (the app under test)
  is still running.

**Known tool quirk, confirmed harmless:** full-page `screenshot` calls on this dark-theme page
intermittently returned solid-black frames in this session (e.g. right after a same-document hash
navigation). Every time this happened it was cross-checked with `getBoundingClientRect`/`innerText`
via `javascript_tool` and, in most cases, a retried screenshot succeeded and showed the expected
content (see the v0.3.0/v0.7.0 mobile screenshots in this pass) — never a real rendering defect.

## 2. Acceptance Criteria Verification

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-1.1 | Loaded index, read `document.body.innerText` order of all rows; cross-checked against `git tag --sort=v:refname` (8 tags) + pseudo-release. | 9 rows, oldest-first, no reorder/filter. | Exactly 9 rows in order `v0.1.0…v0.8.0, Since v0.8.0` — byte-identical order to git's own tag order. | ✅ pass |
| AC-1.2 | Read each row's member/unattributed counts; cross-checked 6 of 9 against live `git log --name-only <prev>..<tag> -- .spark/` (v0.1.0, v0.2.0, v0.3.0, v0.4.0, v0.5.0, v0.7.0). | Counts match `members`/`unattributed` list lengths, never recomputed. | v0.1.0→1/0, v0.2.0→2/0, v0.3.0→3/0, v0.4.0→2/1, v0.5.0→2/0, v0.7.0→1/0 — every one matched independent `git log` counts. | ✅ pass |
| AC-1.3 | Read pseudo-release row + detail; cross-checked against live `git log v0.8.0..HEAD`, `git branch`, and commit dates. | `tag: null` row distinguished, `commits`/`branches`/`days_since_tag`/`work_types` shown as-is (today: 2 commits). | Row reads "Since v0.8.0 OPEN WINDOW · 1 member · 0 unattributed"; detail reads "2 commits since v0.8.0, 1 day ago. 2 local branches. Work types: docs 100%." — matches `git log v0.8.0..HEAD` (2 commits, both `docs:`), `git branch` (2), and tag date (2026-08-19, 1 day before today 2026-08-20) exactly. | ✅ pass |
| AC-1.4 | Checked `read_network_requests` across the whole session (7 full navigations, 4 different ports); inspected the `<img>` element's `src`/`complete`/`naturalWidth`. | Zero external fetches; logo embedded inline. | `img.src` starts `data:image/png;base64,...`, `complete:true`, `naturalWidth:484` (no broken-image icon). Network log across the entire session shows exactly one request per page load — the HTML document itself — never a second request. | ✅ pass |
| AC-2.1 | Clicked v0.3.0's index row; watched `location.hash` and the network log; inspected the resulting `<article>`'s member/table structure. | Same-document navigation (hash change, no reload/request), full member + 5-artifact table with `status`/`date`/`reason`. | `location.hash` → `#rel-2`, network log unchanged (no new request). All 42 `<th>` elements across all 14 `<table>`s carry `scope="col"`. Status/date/reason all render per member. | ✅ pass |
| AC-2.2 | Drilled into v0.3.0; read all member names in that section; cross-checked against `git log --name-only v0.2.0..v0.3.0`. | All 3 real members render, not truncated. | `mcp-server`, `public-repo-polish`, `traceability-metrics` — all 3 present, each with its own full 5-row table, matches `git log` exactly. | ✅ pass |
| AC-2.3 | Drilled into v0.7.0 (`#rel-6`); counted `<h4>` member headings inside that `<article>`. | Exactly 1 member, no phantom second row. | `memberCount: 1`, `memberNames: ["git-native-mid-cycle-board"]` — matches `git log --name-only v0.6.0..v0.7.0` exactly (the corrected AC-2.3 example, C7). | ✅ pass |
| AC-2.4 | Read v0.6.0's unattributed section; cross-checked hash and subject against `git log -1 --format=%s 26e7f95`. | Commit `26e7f95` verbatim, not mis-attributed to `snapshot-report`. | "`26e7f95 — feat: snapshot-report scorecard redesign — cards, confidence mix, full table, v0.6.0`" — byte-identical to `git log`'s own subject, and correctly listed under v0.6.0's *unattributed* section, not folded into a member. | ✅ pass |
| AC-2.5 | Checked every release with an empty `unattributed` list (v0.1.0, v0.2.0, v0.3.0, v0.5.0, v0.7.0, v0.8.0, pseudo-release). | Literal "none" shown, never silently absent. | All 7 show the literal text "none" under "Unattributed commits". | ✅ pass |
| AC-2.6 | Round 1: checked every rendered status string across all 14 tables (70 status cells) for stray backticks; found B1 on `v0.7.0`'s compound `qa` status. Round 2 (this re-test, 2026-08-20): after the fix landed, re-read `v0.7.0`'s `qa` Status cell fresh via `document.body.innerText` (not screenshot, not the diff) and re-checked a plain single-word case (`v0.1.0`'s `spec`/`plan`/`review`/`release`) for regression. | Decorative code-span backticks stripped for legibility; underlying value otherwise verbatim; Date-column backticks (commit hashes) untouched. | Round 1 held for every simple case, with one real exception (B1, now fixed — see §3). Round 2: `v0.7.0`'s `qa` Status cell now reads `"passed — independent re-test (2026-08-19, second pass) reproduced B1–B5 and NFR-7..."` — zero leading backtick. The same row's Date cell still reads `` "...commits `8b4f9ff`/`99e4aae`)" `` — backticks correctly preserved (AC-2.6 only ever applied to Status). `v0.1.0`'s plain statuses (`approved`, `approved`, `passed`, `passed`, `released`) all still render clean, no regression. | ✅ pass (B1 fixed and independently re-verified) |
| AC-3.1 | Built a throwaway zero-tag repo (`/tmp/rbh-zerotags`), rendered it with the real CLI, opened it in the browser. | "repository has no tags" reason shown in words; empty index; no pseudo-release; no traceback/blank page/placeholder row. | `document.body.innerText` = "Release Board\n\nrepository has no tags"; `articleCount: 0`, `rowCount: 0`. Screenshot confirms a clean, styled message box, not a blank page. | ✅ pass |
| AC-3.2 | Built a throwaway one-tag/zero-commits-since repo (`/tmp/rbh-zerosince`), rendered, opened. | True-zero sentence, row still shown, never omitted. | Index row: "Since v1.0.0 OPEN WINDOW · 0 members · 0 unattributed" (row present, not omitted). Detail: "Nothing has landed since v1.0.0." — exact true-zero sentence. | ✅ pass |
| AC-3.3 | Real repo: mcp-server's `qa` artifact (no `qa.md` file exists — confirmed via `ls .spark/mcp-server/`). Synthetic repo: a member with zero `.spark/` artifact files at all. | Reason shown in words next to the badge, never a blank cell, never a guessed status. | Real repo: "file not found" next to the `qa` badge (v0.3.0 and v0.4.0's mcp-server row) — confirmed against the real filesystem, `.spark/mcp-server/` genuinely has no `qa.md`. Synthetic repo: `spec` → "no header table found", `plan`/`review`/`qa`/`release` → "file not found" — all five distinct honest reasons, never blank, never a guess. | ✅ pass |
| NFR-4 | Built a throwaway repo with 60 unattributed commits (`/tmp/rbh-bigdata`), rendered, opened; also re-confirmed AC-1.4's zero-external-request result held across every navigation in this session (7 loads, 4 ports). | Bounded list (≤50) with disclosure; index count itself uncapped; self-contained/offline on any dataset size. | Detail list shows exactly 50 `<li>`-equivalent entries + "Showing the first 50 of 60." disclosure text, rendered in the browser (not just asserted by a unit test). Index row still correctly shows the true, uncapped "60 unattributed". Zero secondary network requests at any dataset size. | ✅ pass |
| NFR-5 | DOM heading traversal (42 headings, all releases); `getComputedStyle`-based WCAG contrast recomputed from scratch on live DOM colors (not trusting review's numbers); 375px viewport `scrollWidth`/`clientWidth` on both index and two detail sections (v0.3.0, v0.7.0 — the longest); badge-color-by-type audit across all 70 badges; interactive-element count. | h1→h2→h3→h4 with no skipped level; AA contrast on shipped text/badge pairs; no page-level horizontal scroll at 375px; color keyed to artifact type only, never status; zero interactive elements beyond plain `<a>`. | Heading sequence: 0 skipped-level transitions across 42 headings, h1 first. Contrast (all computed live, not from source): text-primary ≈15.7–17.4:1, text-secondary ≈7.0–7.8:1, all 5 badge hues 5.28–11.79:1 on `--bg-card` — every text/badge pair clears 4.5:1 comfortably. 375px: `scrollWidth === clientWidth === 375` on index and both detail sections tested (no page-level horizontal scroll; a table's own internal `.table-wrap` scroll container is a separate, non-violating mechanism — see B2). Badge color: exactly one color per artifact type across all 70 badges regardless of status value (`spec` always teal, `plan` always violet, `review` always amber, `qa` always green, `release` always orange — verified via a `Set` of computed colors keyed by badge text, size 1 for every type). Interactive elements: `button:0, input:0, script:0` — only plain `<a>` anchors. | ✅ pass |

## 3. Exploratory Findings

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | Minor | Open `http://localhost:8792/release-board.html#rel-6` (or click v0.7.0's index row). Scroll to the `git-native-mid-cycle-board — artifact status` table, `qa` row, Status column. | Expected: the decorative code-span backticks around the extracted status are stripped for legibility (AC-2.6's stated intent). Observed (round 1): the cell literally renders `` `passed` — independent re-test (2026-08-19, second pass) reproduced B1–B5... `` with an unstripped leading backtick character visible to the user. Root cause (confirmed by reading `releaseboard_report.py:136-143`): `_strip_status_backticks()` only strips when the *entire* value both starts and ends with a backtick (`value.startswith("\`") and value.endswith("\`")`); this real `qa.md`'s Status cell wraps only the first word (`` `passed` ``) and continues with unwrapped free-text narrative, so the whole-value check never matches and the leading backtick survives verbatim. This is the *only* record in the real repo's 9-entry board with a compound (non-simple) status string — every other status observed (`approved`, `passed`, `released`, `preparing`, etc.) is a plain single-word value and strips cleanly. **Fixed, and independently re-verified live in this round-2 `/demo-day` pass (2026-08-20)** — not taken on the developer's annotation: navigated fresh to the regenerated page, read `document.body.innerText` for the whole `v0.7.0` article via `javascript_tool` (not a screenshot, not a re-read of the diff). Observed: the `qa` Status cell now reads `"passed — independent re-test (2026-08-19, second pass) reproduced B1–B5 and NFR-7..."` — zero backtick characters anywhere in the cell. The adjacent Date cell for the same row still reads `` "2026-08-19 (first pass); 2026-08-19 (independent re-test, commits `8b4f9ff`/`99e4aae`)" `` — its backticks are correctly untouched (AC-2.6 never applied the strip to Date, only Status; stripping these would have been a regression, and it didn't happen). Spot-checked the simple case for regression: `v0.1.0`'s `spec`/`plan`/`review`/`release` cells (`approved`, `approved`, `passed`, `released`) all still render clean, zero backticks. Fix holds. | fixed, re-verified |
| B2 | Minor (cosmetic) | Resize to 375px width, navigate to any release detail (e.g. `#rel-2` or `#rel-6`), observe a member's `<table>` caption ("`<name>` — artifact status"). | Expected/observed (round 1): the `<caption>` element lives inside the table's own `.table-wrap` (overflow-x: auto) scroll container alongside the `<table>` itself, so at 375px the caption text clips at the right edge and needs a horizontal scroll gesture inside the table to read in full. No information is actually lost (the `<h4>` member-name heading directly above already states the same name, and the page itself never scrolls horizontally — confirmed `scrollWidth === clientWidth` throughout), so this is polish, not a functional defect. **Fixed, and independently re-verified live in this round-2 `/demo-day` pass (2026-08-20)** — not taken on the developer's annotation: resized the live tab to 375×812, ran a fresh DOM query (`javascript_tool`) across all 14 `<caption>` elements on the regenerated page. Observed: `[...new Set(captions.map(c=>c.textContent.trim()))]` has length 1, value `"Artifact status"` — every caption on the page, including v0.7.0's `git-native-mid-cycle-board` table (the longest real member name in this repo's data, 26 chars), reads the same short fixed string. Measured `scrollWidth === clientWidth === 269` on every one of the 14 captions (no clip at 375px, not eyeballed). Confirmed no information loss: the `<h4>` immediately above that same table still reads the full, unclipped `"git-native-mid-cycle-board"` (`scrollWidth === clientWidth === 269`, `getBoundingClientRect().width > 0`). Also re-confirmed no page-level horizontal scroll regressed in (`document.documentElement.scrollWidth === clientWidth === 375`). Fix holds. | fixed, re-verified |

Both are Minor: neither loses data, crashes, nor blocks a Must flow. Both are now `fixed, re-verified` —
per this project's own house rule ("never take a fix on the fixer's word alone — reproduce it yourself
with fresh inputs"), this round-2 pass reproduced both independently against the regenerated live page
(fresh `javascript_tool` DOM reads, not a re-read of the round-1 screenshots or the developer's diff
annotation) rather than trusting the "**Fixed:** ..." text added in place. Per this project's own
established gate precedent (`review.md`'s REVIEW GATE closed with Minor/Nit findings F6/F8/F12/F13 open,
no formal user waiver required for sub-Major severity), Minor findings are listed but never gating —
here both are additionally closed out as fixed.

**Round-2 regression spot-check (2026-08-20):** did not redo the full exhaustive round-1 sweep (synthetic
zero-tags/zero-since/60-commit repos — untouched by this fix, already passed). Did re-confirm, live, on
the regenerated page: index still shows all 9 rows in order (`v0.1.0`...`v0.8.0`, `Since v0.8.0`, read via
`document.body.innerText`); same-document drill-down still works (clicked `v0.7.0`'s `#rel-6` link via
`javascript_tool` — `location.hash` changed, zero new network request); network log across the whole
round-2 session shows exactly one `GET release-board.html` per page load, no secondary requests; console
log empty at every step (index, detail, post-resize, post-click).

## 4. Console & Network

- **Console:** checked after every navigation, every synthetic-repo load, and after a rapid triple-click
  stress test on an index-row link (`link.click(); link.click(); link.click();`). Zero console messages
  of any kind (no `console.log`, no warnings, no errors) at any point in this session — expected, since
  the page ships zero `<script>` tags (confirmed: `document.querySelectorAll('script').length === 0`).
- **Network:** the entire session (7 full page loads of the app under test across `http://localhost:8792`,
  plus 3 more loads of throwaway synthetic renders on other ports) produced exactly one HTTP request per
  page load — the HTML document itself. Not one secondary request (font, image, script, stylesheet) was
  ever observed, including immediately after resize+reload, hash navigation, and the rapid-click stress
  test. ADR-5's "zero outbound requests" holds under adversarial repetition, not just on first load.

## 5. F6 Ruling — decorative border contrast (routed by review.md)

Independently re-measured via `getComputedStyle` on the live DOM (not read off `review.md`'s numbers,
though they match): `--border-line` (`rgba(255,255,255,.09)`) composites to **≈1.22:1** on `--bg-primary`
and **≈1.28:1** on `--bg-card`; `--border-subtle` (`rgba(58,189,176,.15)`) composites to **≈1.24:1** on
`--bg-primary` and **≈1.29:1** on `--bg-card`. Both are well under the WCAG 1.4.11 3:1 non-text floor.

**Ruling: legitimate exemption, not a failure.** WCAG 1.4.11 applies to UI components and graphical
objects *required to understand the content* — it does not apply to purely decorative ornamentation
when the same structural information is available through other means. Here, both border pairs are
used exclusively as decoration on elements whose actual structure is conveyed by real, verified
semantic markup: `<table>`/`<th scope="col">` for the 5-artifact matrices (42 of 42 `<th>` elements
carry `scope="col"`, confirmed live) and `<article>`/heading-hierarchy for card boundaries (0 skipped
heading levels, confirmed live). A user who could not perceive either border at all would lose no
information — row/column relationships come from the table markup itself, not from a visible gridline,
and card boundaries come from spacing/background-color contrast (`--bg-card` on `--bg-primary`, itself
not a low-contrast pair) plus heading text, not from the border. This is exactly the "decorative
border, structure conveyed by markup" exemption case NFR-5's own binding rule (spec §3 A1) anticipates.
Not gate-blocking; no fix required.

## 6. Verdict

Yes — I would demo this to a stakeholder right now. Every Must-story acceptance criterion (US-1, US-2,
US-3, all three Must) was verified with actual clicks, actual hash navigations, and actual computed
styles pulled from the live DOM — not read off the source or trusted from `review.md`'s numbers. Where
the real repo's 9-entry board couldn't reach a state the spec requires (zero tags, true-zero
pseudo-release, >50-item truncation), I built three throwaway synthetic repos, rendered them with the
real installed CLI, and watched the actual page respond honestly in the browser — all three passed. The
badge-color-by-type rule (A3) is now structurally verified across all 70 badges on the page, not just
reasoned about. F6's decorative-border question is ruled, with a reason, from independently-recomputed
numbers. Zero console errors, zero secondary network requests, held under rapid-click and multi-page
stress.

**Round 2 (2026-08-20 re-test):** both Minor findings from round 1 are now `fixed, re-verified`. B1 —
`v0.7.0`'s real `qa` Status cell, read fresh from the regenerated page's live DOM, shows zero backtick
characters; the adjacent Date cell's own commit-hash backticks are correctly untouched; a plain
single-word status elsewhere still strips clean, no regression. B2 — all 14 table captions on the page
read the literal, fixed-length "Artifact status" (a `Set` of distinct caption texts has size 1),
measured `scrollWidth === clientWidth` at 375px with zero clip on every one, including the longest real
member name (`git-native-mid-cycle-board`, whose full name still renders unclipped in the `<h4>` above).
Neither fix was taken on the developer's word — both were reproduced independently with fresh
`javascript_tool` DOM reads against the regenerated live page. Nothing else regressed: index still shows
all 9 rows in order, same-document drill-down still works with zero new network requests, console stayed
empty throughout, and the single-request-per-load network behavior held. Zero open Blocker, Major, or
Minor findings remain — the gate closes clean.

---

## ✅ QA GATE

*All boxes checked → `/go-live` may start. Any box open → back to `/increment`, then re-run `/demo-day`.*

- [x] Every Must-story acceptance criterion verified in the real browser and passed — AC-1.1 through
  AC-3.3, all 13, each with actual clicks/DOM reads/network checks (AC-2.6 passed with a filed Minor
  exception, B1, not a spec violation of the AC's literal wording)
- [x] Every browser-observable NFR verified and passed — NFR-4 and NFR-5 (the only two routed to
  `/demo-day`), both including a real synthetic-repo click-through for the states the real repo
  can't reach
- [x] No open Blocker or Major bugs (Minor bugs listed and accepted by the user) — 0 Blocker, 0 Major,
  0 open Minor: B1 and B2 (both Minor) are `fixed, re-verified` as of the 2026-08-20 round-2 pass, each
  independently reproduced live against the regenerated page rather than taken on the fixer's word
- [x] Browser console free of errors on the tested flows — zero console messages of any kind, across
  every flow tested including a rapid-click stress test
- [x] Tested on all agreed viewports — desktop (native) and 375px mobile, both index and detail views
- [x] Status set to `passed`
