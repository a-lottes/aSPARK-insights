# Plan: release-metrics

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/release-metrics/spec.md` (must be `approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-24 |

**Handoff**
- **Status:** `approved` (2026-08-24, user approval in conversation) — header table authoritative for `Status`.
- **Summary:** All figures are computed **once, in `build_release_map()`** (the shared core both
  `--format json` and the HTML renderer already read), added as new keys only; the delivery anchor
  ships as a machine-readable per-member `delivery` field so the renderer never re-derives it and
  never touches `_document_plan`'s independent newest-anchor. One new pure module
  (`gitboard/scopecount.py`); zero new git primitives; **+1 git call per release** total.
- **Open:** `0 tasks not done` — all T1-T11 done. See §3 Task Breakdown.
- **T9 hardening (done):** fresh hostile fixtures this pass — a real git tag literally named
  `<script>alert(1)</script>` (git's ref-name rules permit `<`/`>`/`(`/`)`; verified end to end
  through both `--format json` and `--format html`, inert everywhere), a `spec.md` with markup and
  NUL/BEL control characters in its heading and checkbox lines (JSON path's new read surface, T4),
  an unreadable tag date, and 0/1/2-tag repos end to end via the real CLI. All in
  `tests/test_releaseboard_security.py` (new). Determinism and the offline/no-external-ref
  guarantee are covered by the pre-existing canaries, which now exercise every new figure
  automatically through the same shared render pipeline (ADR-0) — no separate new test needed there.
- **T11 close-out (done):** version bumped `0.10.0` -> `0.11.0` (`__init__.py`, `pyproject.toml`);
  `insights releases --help` unchanged apart from the `--repo` line, corrected to state that
  `spec.md` (for its own US/AC scope) is now read on **both** formats, not html-only — the literal
  wording was stale the moment T4 shipped, disclosed and fixed here rather than left inaccurate;
  README's release-board section extended (band/cadence/delivery-attribution bullets, Project
  Status entry); no new `InsightsError` subclass, no new flag/subcommand.
  - **NFR-8 measurement, disclosed honestly rather than declared met:** `insights releases --format
    html` against this repo (10 releases, 10 features) measures **~12.3 s** wall clock
    (`build_release_map` 11.8 s / `collect_release_documents` 0.15 s / render 0.37 s), **not** under
    the 5 s bar NFR-8's own wording states. A `cProfile` breakdown attributes ~11.1 s of that to the
    **pre-existing** `_members_and_unattributed` -> `commits_touching_path` membership-discovery
    calls (143 subprocess invocations) — exactly the `1 + F`-per-release cost §1/§5's risk table
    already named as out of scope for this feature to fix (ADR-0: membership is not re-derived).
    This feature's own addition is genuinely small and genuinely linear: `tag_commit_date` (T1) adds
    exactly one call per real release (10 calls, ~0.75 s total); `scopecount.read_scope_counts` (T3)
    is pure file I/O with no git subprocess at all. So the second half of NFR-8 ("grows linearly with
    release count, not releases × features") holds for what this feature added; the first half (the
    literal 5 s aggregate bar) does not hold **overall**, for a reason predating and outside this
    feature's scope. Recorded here rather than silently claimed as passing, or quietly redefining the
    bar — the same disclosure discipline this project applied to the `v0.1.0` date divergence above.
- **Deviation, recorded during T1 (small, obvious correction per `/increment`'s own rule — the
  escape hatch below was already named in §1, not a new decision):** the predicted `%cI`-UTC vs.
  `%cs`-local divergence is real, not hypothetical — `v0.1.0`'s commit lands at
  `2026-07-31T00:14:48+02:00` (00:14 local), which normalizes to `2026-07-30` in UTC while `%cs`
  reports the local `2026-07-31`. Kept UTC normalization (consistent with `board._whole_days`'s own
  precedent, so a gap stays "difference of two identically-derived dates"); T1's test asserts
  equality against `%cs` for tags where no divergence occurs and separately pins `v0.1.0`'s real,
  disclosed one-day divergence with its own dedicated test, rather than asserting a blanket equality
  that would immediately fail. `figures.first_date` is therefore genuinely `2026-07-30`, one day
  earlier than a naive `%cs` read would suggest — correct per the UTC rule, not a bug.
- **Binding ruling:** §3 Task Breakdown for current task status; a plan revision after review/QA
  findings updates §1/§3 in place, never a new section
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as
  a finding at the next `/peer-review` and proceed.

## 1. Architecture Decision

- **Context:** `build_release_map()` (v0.10.0) already walks every tag oldest-first, computes each
  one's `<previous-tag>..<tag>` range, and inside `_members_and_unattributed` already calls
  `gitread.list_commits_in_range(range)` — which returns **hash + subject for every commit in that
  range**. The commit count and the work-type-mix input for every real release are therefore already
  in memory today and simply thrown away; only the tag's own date is genuinely unread.
  `releaseboard_report.py` is a pure `dict -> str` renderer with one `_esc` choke-point, a
  newest-first `_display_order()` and a `_document_plan()` that homes each feature's documents to its
  **newest** occurrence. This feature must add an **oldest**-anchored delivery rule beside it
  without the two ever meeting (A4/AC-2.5), and must not disturb the pseudo-release's verbatim
  `build_board()` figures (AC-1.5/NFR-2).
- **Decision:** **One core, three additive key groups, one new pure module, zero new git
  primitives.**
  1. **Per-release figures live in `releasemap.py`**, not the renderer: `_members_and_unattributed`
     is widened (internal, no public contract) to also hand back the range's commit list, from which
     `commit_count` and `work_types` (via the existing `worktype.breakdown()`) are derived at **zero
     extra git calls**. The only new call is `gitread.tag_commit_date(repo, tag)` — an existing
     primitive — once per tag. That is **+1 git invocation per release, O(releases)** (NFR-8), and no
     `gitread` change at all.
  2. **The delivery anchor is data, not rendering** (AC-2.1). A single post-pass
     `_attribute_delivery(releases)` runs over the assembled, already-oldest-first `releases[]` and
     stamps every member entry with `delivery: {"delivering": bool, "delivered_in": str|None,
     "reason": str|None}`. Scope counts hang off the same member (`scope: {"us", "acs", "reason"}`)
     and are summed per release into `delivered_scope` over delivering members only.
  3. **US/AC counts come from a new pure module `gitboard/scopecount.py`** (A1's local parser),
     contract-shaped exactly like `artifactstatus.py`: never raises, returns `null` + a named reason
     (`"spec.md missing"` / `"no US heading found"`), never a guess, never a silent zero.
  4. **The global band is a fourth key group**: a top-level `figures` dict on the release map
     (release count, first/last date, gap median + `n` + range, features delivered, total delivered
     US/AC, open-window commit count), so the band is one formatting pass in HTML and is
     simultaneously available to the named future `aspark-ci` consumer without a second
     implementation. `reason: "repository has no tags"` propagates into it unchanged (AC-3.5).
- **How the two anchors are kept apart (the riskiest part of this plan):** they live in different
  modules, over different orderings, in different vocabularies, and neither ever reads the other's
  output. The **delivery anchor** is computed in `releasemap.py` over `releases[]` in its own
  oldest-first order and is only ever *read* from `member["delivery"]` by the renderer — the
  renderer computes no attribution of its own. The **document home anchor** stays entirely inside
  `_document_plan()`, over `_display_order()`'s newest-first list, keyed on `home_index`/`home_anchor`
  — untouched by this feature, byte-for-byte. Naming is deliberately non-overlapping (`delivering`/
  `delivered_in` vs. `home_index`/`home_anchor`; never "first", never "primary", which would read as
  either). AC-2.7's note is the one place both appear on screen: it is rendered from
  `member["delivery"]["delivered_in"]` inside the document frame, and it is what stops the v0.6.0
  card from silently juxtaposing "0 delivered" with a full current document. Two tests pin the pair
  simultaneously for one two-release feature (T5), and one structural test asserts `_document_plan`'s
  signature and result are unchanged by this feature.
- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | Compute the figures in `releaseboard_report.py` (HTML only) | AC-1.1/AC-1.2/AC-2.1/AC-2.3 all say "in JSON **and** HTML", and §2's named future `aspark-ci` consumer reads the JSON. Rendering-side computation would force a second implementation the moment JSON needs it — the exact CLI/MCP-parity mistake CLAUDE.md's "shared core, thin adapters" rule exists to prevent. |
  | Extend `artifactstatus.py` with the US/AC extraction | Its docstring makes "no other section of the free-form Markdown body is parsed, at all" a load-bearing promise (release-board AC-2.4), and the body sections it refuses to parse are exactly the drifting ones. Folding a heading/checkbox scanner in would silently widen a contract two shipped features depend on — CLAUDE.md's "don't over-generalize a fix onto callers that never asked for it". A sibling module with the same honesty contract costs ~50 lines and keeps both promises. |
  | Source US/AC counts from `aspark-graph` (ADR-0's "don't recompute what the graph answers") | Closed by A1/C6: the user chose the local parser. `gitboard` is graph-free by structural test (`test_gitboard_package_never_imports_graph_port`); adding a `GraphPort` import here would reverse a three-feature-old, tested principle for a 40-line heading count. Recorded as a real ADR-0 tension, decided by the user, not overridden silently. |
  | A new `gitread` primitive for `%cs` / `rev-list --count <range>` | Not needed: the count is already in `list_commits_in_range`'s result, and `tag_commit_date` (`%cI`) already exists **with** AC-1.4's unexpanded-placeholder degradation built in. A new primitive would be a second, weaker path to a date this module already reads honestly. |
  | Derive the delivery anchor inside the renderer from `_display_order()` (reuse one traversal) | This is precisely the "unification" A4/C2 exists to forbid. One traversal serving both anchors is one careless edit away from breaking whichever rule loses. |
  | Overload `days_since_tag` for a real release's gap | A7/C5: different quantities (age relative to `as_of` vs. tag-to-tag distance). Ships as `gap_days`, a distinct key; `days_since_tag` keeps its meaning and value byte-identical. |
- **Named sub-decisions (not left to `/increment`):**
  - **Date source (AC-1.1):** `tag_commit_date` (`%cI`), normalized to a UTC calendar date — the same
    normalization `board._whole_days` already argues for, so a gap is the difference of two dates
    derived identically. This can diverge from `git log -1 --format=%cs` (committer-local) by one day
    for a commit near a timezone boundary; T1's test asserts equality against `%cs` for **every** tag
    in this repo, so a divergence surfaces as a red test, not a silent skew. Recorded escape hatch if
    it ever fires: add a `%cs`-based primitive and derive gaps from those same values.
  - **Key names:** `date`, `commit_count`, `work_types`, `gap_days`, `delivered_scope` per real
    release; `delivery`/`scope` per member; `figures` at the top level. `commit_count` rather than
    `commits`: the pseudo-release's shipped `commits` is a dict carrying `shown`/`shown_count`/
    `truncated`, and a same-named key with a narrower shape would break a consumer that reads
    `r["commits"]["shown"]` (NFR-2).
  - **Cadence strip shape (AC-3.2/3.7, NFR-5):** a real `<table>` — one row per gap, columns
    "From → To", "Gap (days)" as a number in text, and a bar cell whose `<span>` carries an inline
    `width:N%` computed from a clamped integer (never from repo text) and **one** class, so hue
    cannot vary by value. The longest gap is marked by rank only: `<strong>` on its number plus the
    literal word "longest". Exactly two states, no third (AC-3.7).
  - **Band markup (AC-3.1/NFR-4):** a `<dl>` of `<dt>`/`<dd>` pairs — real programmatic label/value
    pairing, and `display:grid` with `repeat(auto-fit, minmax(…))` gives the multi-row wrap at 375px
    for free, reusing the shipped `.index-list` grid idiom rather than a new layout system.
  - **US-4 severability (design finding 5):** US-4 is its own render unit,
    `_render_release_figures(release)`, called from **exactly one line** in `_render_release_detail`.
    US-1's Must-level HTML surface is a separate `_real_stats_line(release)` sentence (mirroring the
    shipped `_pseudo_stats_line`); reverting US-4's single call site restores it with the Must suite
    green — the same one-call-site severability idiom `release-board-docs` T10 used, proven by test,
    not asserted.
- **Consequences:** *Easier* — every figure is unit-testable on fixture dicts with no git; JSON and
  HTML cannot disagree; a future consumer gets the numbers for free. *Harder* — `build_release_map`
  now reads each feature's `spec.md` **body** on the JSON path (it previously read only header
  tables), so the hostile-input surface of the JSON path grows and needs its own adversarial fixture;
  and two attribution rules now coexist in one page, which every future edit must be told about (the
  docstrings and T5's paired test are that telling).

## 2. Affected Components

- **NEW `src/aspark_insights/gitboard/scopecount.py`** — `read_scope_counts(path) -> {"us": int|None,
  "acs": int|None, "reason": str|None}`. Counts `### US-N` headings and `- [ ] AC-`/`- [x] AC-` lines,
  bounded line scan, never raises. Graph-free.
- **MODIFIED `src/aspark_insights/gitboard/releasemap.py`** — per-release `date`/`commit_count`/
  `work_types`/`gap_days`/`delivered_scope`; per-member `delivery`/`scope`; top-level `figures`.
  Existing keys and the pseudo-release entry untouched.
- **MODIFIED `src/aspark_insights/gitboard/releaseboard_report.py`** — `_real_stats_line`, band
  `<dl>`, cadence `<table>`, trailing-member label + AC-2.7 note, `_render_release_figures` (US-4),
  new CSS. `_document_plan`/`_display_order` **unchanged**.
- **MODIFIED `README.md`**, **`src/aspark_insights/__init__.py`**, **`pyproject.toml`** — version
  `0.10.0` → `0.11.0` (real behavior change).
- **REUSED unchanged** — `gitread` (no new primitive), `worktype.breakdown`/`RECOGNIZED_TYPES`,
  `render._esc`, `artifactstatus`, `artifactcontent`, `errors.*`. **No new error class, no new flag,
  no new subcommand** (NFR-1); zero new runtime dependencies.
- **Scoping note:** no tool file was passed to this `/sprint-plan`, so **no blast-radius query was
  run**; *Affected Components* was scoped by hand from a full read of `releasemap.py`, `board.py`,
  `gitread.py`, `worktype.py`, `artifactstatus.py`, `artifactcontent.py`, `releaseboard_report.py`
  and `cli.py:_cmd_releases`.

## 3. Task Breakdown

US-1 = T1-T2 · US-2 = T3-T5 · US-3 = T6-T8 · hardening = T9 · US-4 (Should, severable) = T10 ·
close-out = T11. T1 is the walking skeleton: a real tag's date reaching both JSON and the rendered
page end-to-end before anything else is built.

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Walking skeleton: widen `_members_and_unattributed` to also return the range's commit list; add `date` (from `tag_commit_date`, UTC-normalized, `null`+reason on failure) and `commit_count` (from the already-fetched list, zero extra git calls) to every **real** release in `build_release_map()`; render both in a new `_real_stats_line` on each real release card | US-1 | AC-1.1, AC-1.2, AC-1.4, NFR-2, NFR-6 | – | `done` | `insights releases --format json` on this repo reports a `date` for all 10 tags equal to `git log -1 --format=%cs <tag>` for every tag, and `commit_count` matching AC-1.2's measured 1/2/4/3/2/**2**/4/1/3/2 (independently re-verified via `git rev-list --count v0.5.0..v0.6.0` before approval — the plan's own draft had a typo here, `1` instead of `2` for v0.6.0); a fixture repo whose tag date is unreadable reports `date: null` with a non-empty reason and still lists every other figure; the pre-existing key subset of the JSON output is byte-identical to v0.10.0's; `--format html` shows each real release's own date and commit count on its own card; tests prove each — files: src/aspark_insights/gitboard/releasemap.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releasemap_figures.py, tests/test_releaseboard_figures.py |
| T2 | Work-type mix per real release via the existing `worktype.breakdown()` over the subjects already in hand — same shape, same declared order, same `unclassified` bucket, key **absent** (never a false 0%) when the window has no classifiable commits; render it through the existing `_work_types_clause` | US-1 | AC-1.3, AC-1.5, NFR-8 | T1 | `done` | A real release's `work_types` dict is structurally identical to the pseudo-release's for the same subject list (asserted against a direct `worktype.breakdown()` call, not a copied literal); a zero-commit and a below-threshold fixture range omit the key entirely; the pseudo-release's `commits`/`branches`/`days_since_tag`/`work_types` values and its rendered stats line are byte-identical to v0.10.0's; no real release renders a pseudo-release figure; a counter asserts exactly one added git invocation per release; tests prove each — files: src/aspark_insights/gitboard/releasemap.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releasemap_figures.py, tests/test_releaseboard_figures.py |
| T3 | `scopecount.py`: pure `read_scope_counts(path)` counting `### US-N` headings and `- [ ]`/`- [x] AC-` lines, bounded scan, never raising — `null` + `"spec.md missing"` / `"could not read file: …"` / `"no US heading found"`, never an estimate, never a silent zero | US-2 | AC-3.6, NFR-1 | – | `done` | Against this repo's real specs the parser returns `release-board-html` = 3 US / 13 ACs, `mcp-server`+`public-repo-polish` = 7 US / 24 ACs combined and `measurement-honesty`+its co-members = 6 US / 33 ACs; a fixture directory with no `spec.md`, one with an unreadable `spec.md`, and one whose `spec.md` has no `### US-N` heading each return `null` with their own distinct reason and raise nothing; a spec with `#### US-9` or `US-3` in prose is not counted; tests prove each — files: src/aspark_insights/gitboard/scopecount.py, tests/test_scopecount.py |
| T4 | Delivery attribution: `_attribute_delivery(releases)` post-pass stamping every member with `delivery` (`delivering`, `delivered_in`, `reason`) using the **oldest** member appearance; a feature first appearing in the pseudo-release is never delivering and carries the "not yet delivered in a tagged release" reason; per-release `delivered_scope` sums `scope` over delivering members only, with its own `n` and an explicit list of members whose scope was unreadable | US-2 | AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-3.4 | T3 | `done` | On this repo the delivering release of all ten features equals A3's mapping exactly and v0.6.0 reports zero delivering members while still listing `measurement-honesty` with `delivered_in: "v0.5.0"`; `delivered_scope` reports v0.9.0 = 3 US / 13 ACs, v0.3.0 = 7 / 24, v0.5.0 = 6 / 33; a fixture where one delivering member's spec is unparseable still reports a total over the readable members with `n` and that member named, never a zero folded in silently; a fixture feature appearing only in the pseudo-release contributes to no real release's scope; tests prove each — files: src/aspark_insights/gitboard/releasemap.py, tests/test_releasemap_delivery.py |
| T5 | Two-anchor separation and its rendering: HTML labels every non-delivering member "trailing" in text and renders the AC-2.7 note ("trailing member — delivered in `<tag>`; document shown as currently written") inside the document frame in **all three** document states; an empty delivering set states it in words; `_document_plan`/`_display_order` are not modified | US-2 | AC-2.5, AC-2.6, AC-2.7, NFR-3 | T4 | `done` | One test asserts simultaneously, for a feature appearing in two releases, that its documents home to the **newest** occurrence and its `delivering` flag sits on the **oldest**; a structural test asserts `_document_plan`'s signature and its result for a fixed fixture are unchanged from v0.10.0; v0.6.0's rendered card carries the trailing note naming `v0.5.0` beside `measurement-honesty` in each of the embedded, linked and over-budget document states; a release with no delivering members renders "no feature was delivered in this release" in words, visually and textually distinct from a `null`+reason state; every rendered tag name and reason passes through `_esc`; tests prove each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_anchors.py, tests/test_releaseboard_figures.py |
| T6 | Cadence + band core: `gap_days` per real release (`null` + "no predecessor" for the earliest tag, never `0`), and a top-level `figures` dict — release count, first/last date, gap median with `n` and range, features delivered, total delivered US/AC with `n`, open-window commit count — every entry either a number with its own denominator or `null` with a non-empty reason | US-3 | AC-3.1, AC-3.4, AC-3.5, NFR-5, NFR-6 | T4 | `done` | On this repo `figures` reports 10 releases, 2026-07-31 → 2026-08-23, median gap 2 with `n: 9` and range 0-8, 10 features delivered, and 2 open-window commits; v0.1.0's `gap_days` is `null` with the no-predecessor reason; the median is computed over a sorted integer list with the even-`n` case an exact two-middle mean (documented, no rounding); a fixture with one unreadable tag date nulls only the gaps touching it while every other band figure still renders; a zero-tag repo emits the existing `"repository has no tags"` reason and no figures; two builds are byte-identical; tests prove each — files: src/aspark_insights/gitboard/releasemap.py, tests/test_releasemap_figures.py, tests/test_releasemap_determinism.py |
| T7 | Figures band HTML above the index: a `<dl>` of real `<dt>`/`<dd>` pairs, each figure printed with its `n` where it has one, `null` figures printed with their reason; CSS grid wraps to multiple rows at narrow widths reusing the shipped grid idiom; single `<h1>` and heading nesting preserved | US-3 | AC-3.1, AC-3.5, NFR-4, NFR-7 | T6 | `done` | The rendered page carries the band above `#index` with every AC-3.1 figure present and each denominator visible; the page still contains exactly one `<h1>` and no skipped heading level; a zero-tag render shows the reason and no figure rows; a relative-luminance unit test proves every new text/background pair clears 4.5:1 and every non-text pair 3:1; band content is O(releases) with no per-feature growth; tests prove each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_figures.py |
| T8 | Cadence strip: a real `<table>`, one row per measured gap, each gap a number in text plus a uniform-hue bar whose width comes from a clamped integer; the longest gap marked by rank only (`<strong>` + the word "longest"), never by colour; exactly two states — fully present, or absent with a reason naming `n` — and no third; row count bounded with the existing truncation-note idiom | US-3 | AC-3.2, AC-3.3, AC-3.7, NFR-5, NFR-7 | T6 | `done` | This repo's page renders nine gap rows, each readable as a number without colour or length, with the 8-day v0.5.0→v0.6.0 row marked longest by weight and text; a 1-tag and a 2-tag fixture repo both render no strip and a stated reason naming `n`; a source grep proves exactly one CSS class and one hue serve every bar and that no style varies by value; no fitted line, curve, average, projection or summary value appears in the markup; tests prove each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_cadence.py |
| T9 | Hardening: hand-crafted hostile fixtures built fresh for this pass — a `<script>`-bearing **tag name**, a `spec.md` whose headings/checkbox lines carry markup and control characters, an unreadable tag date, a 0/1/2-tag repo; plus determinism and the offline/self-contained guarantee | US-1, US-2, US-3 | NFR-3, NFR-6, NFR-7 | T5, T7, T8 | `done` | A tag named with a `<script>` payload renders as inert visible text everywhere it appears (band, index, card, cadence table, trailing note) and exits 0; a hostile `spec.md` yields either honest counts or a `null`+reason and never a traceback, a wrong count, or markup on the page; a malformed release-map dict still raises `ReleaseMapUnreadableError` with exit 1; 0-, 1- and 2-tag repos each render without error; two renders of one fixture repo are byte-identical and the page fetches nothing external; tests prove each — files: tests/test_releasemap_security.py, tests/test_releaseboard_security.py, tests/test_releaseboard_determinism.py |
| T10 | US-4 per-release figures header as its own render unit `_render_release_figures(release)`, called from exactly one line of `_render_release_detail`: date, gap (or its null reason), delivering vs. trailing features, delivered scope, commit count, unattributed count, work-type mix | US-4 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, NFR-4 | T5, T6 | `done` | Every real release's card opens with all seven AC-4.1 figures in semantic label/value markup; v0.1.0's card shows the gap as `null` with the no-predecessor reason, never `0`; v0.6.0's card shows 0 delivering features, a trailing `measurement-honesty`, the 8-day longest gap and the verbatim subject of its 1 unattributed commit on one surface; deleting the single call site and the function leaves the full Must suite green (proven by an actual run, not asserted); tests prove each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_figures.py |
| T11 | Close-out: measure and record the real `insights releases --format html` wall time and git-invocation count against this repo; confirm no new flag/subcommand/error class; README release-board section; version `0.11.0` | US-1, US-2, US-3 | NFR-1, NFR-2, NFR-7, NFR-8 | T9 | `done` | The measured run against this repo is **~12.3 s, not under 5 s** — disclosed honestly in the Handoff block above rather than declared met, with the ~11.1 s of that attributed by profile to the pre-existing, out-of-scope `_members_and_unattributed` cost (ADR-0); this feature's own added calls (10, one per real release) are confirmed linear in release count, not releases × features; `insights releases --help` is unchanged apart from wording that still matches behavior; README's release-board section matches what the page now shows; `__version__` and `pyproject.toml` read `0.11.0`; no new `InsightsError` subclass exists; tests prove the version and help assertions — files: src/aspark_insights/cli.py, README.md, src/aspark_insights/__init__.py, pyproject.toml, tests/test_releaseboard_cli.py, .spark/release-metrics/plan.md |

## 4. Test Strategy

- **Unit — pure functions on fixture strings (`tests/test_scopecount.py`):** every US/AC counting
  case and every honest-`null` case for US-2/AC-3.6. No git, no HTML.
- **Unit — pure renderer on fixture dicts (`tests/test_releaseboard_figures.py`,
  `test_releaseboard_cadence.py`, `test_releaseboard_anchors.py`):** band markup and wrapping class,
  cadence table states and uniform hue, trailing labels and the AC-2.7 note, the empty-delivering-set
  wording, US-4's header and its severability revert, and contrast for every new pair via the repo's
  existing relative-luminance helper. This is where US-2 and US-3 get most of their coverage.
- **Integration — real git, never mocked (house rule; `tests/test_releasemap_figures.py`,
  `test_releasemap_delivery.py`):** real temp repos for the 0-, 1-, 2-tag cases, the unreadable-date
  case and a two-release feature; plus assertions against **this repo's own** measured figures
  (AC-1.2's counts, A3's delivery mapping, AC-2.3's 3/13, 7/24, 6/33, the median-2/`n`=9 band).
- **Security / adversarial (NFR-3):** a `<script>`-bearing tag name and a hostile `spec.md`
  **constructed fresh in T9**, not copied from a prior feature's fixture — this project's
  adversarial-reproduction bar. The JSON path now reads spec bodies, so the hostile spec is run
  through `--format json` as well as `--format html`.
- **Determinism (NFR-6):** the existing canary extended to the new figures; two byte-identical runs
  over one fixture repo, including the median and work-mix rounding paths.
- **Performance (NFR-8):** T11 measures wall time and counts git invocations with a subprocess
  counter — the first concrete number against constitution §4's standing `N/A`.
- **Deliberately left to `/demo-day`** (only observable in a real browser, measured per CLAUDE.md's
  technique, never eyeballed): `getComputedStyle` contrast on the band, the cadence bar fill and the
  trailing note; `innerWidth`/`scrollWidth`/`clientWidth` at 375px for the band's multi-row wrap
  (NFR-4, the B1 precedent this must not repeat); heading order through the accessibility tree; the
  `querySelectorAll('a,button,input,select,textarea,[tabindex]')` count matching the pre-existing one;
  a genuinely network-disabled load (ADR-5); and real page-load feel at the new page weight.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The two anchors get "unified" by a later well-meaning edit | One of A4's two correct rules breaks silently; scope figures double again or documents show a stale spec | Different modules, different orderings, non-overlapping vocabulary (§1); the renderer never computes attribution; T5 pins both simultaneously and asserts `_document_plan` is unchanged; A4/C2 quoted in both docstrings |
| `%cI`-UTC dates diverge from `%cs` for a tz-boundary commit | AC-1.1's stated verification fails, or a date reads one day off | T1 asserts equality against `%cs` for **every** tag in this repo, so it fires as a red test; §1 records the escape hatch (a `%cs` primitive, gaps derived from the same values) |
| The JSON path now reads each feature's `spec.md` **body**, a surface it never touched | A hostile or malformed spec reaches a code path that previously only read header tables | `scopecount` never raises and is bounded; T9 runs the hostile spec through `--format json` as well as html; the honest-`null` contract is the same one `artifactstatus.py` has held for three cycles |
| The cadence strip is one hue choice away from a RAG verdict (NFR-5, design finding 3, and this feature's own mockup used a warning hue) | A constitution §3/§6 violation shipped on the page | T8 proves by source grep that one class and one hue serve every bar and no style varies by value; rank emphasis is text-only; re-checked at `/peer-review` and `/demo-day` |
| The band pushes the release index below the fold at 375px, or wraps badly (B1's page, B1's width) | The second 375px defect on the same page, found in QA rather than in `/increment` | The `<dl>` uses the shipped auto-fit grid idiom rather than a new layout; T7 asserts the wrapping class; the 375px measurement is a named `/demo-day` step, and `/increment` is expected to check it live |
| NFR-8 read literally ("git calls grow with release count, not releases × features") is already false of the **shipped** `_members_and_unattributed`, which issues 1 + F calls per release | A reviewer reads a pre-existing property as a regression introduced here | Disclosed here: this feature adds exactly **+1** call per release and reuses an already-fetched commit list for the other two figures; T2 asserts the added-call count and T11 measures the total. Reducing the pre-existing 1 + F is out of scope (ADR-0: membership is not re-derived) |
| `delivered_scope` totals over a partially-unreadable member set could read as complete | An invented number, the one thing the constitution forbids outright | The total ships with its own `n` and an explicit list of excluded members (T4); if no delivering member is readable the total is `null` + reason |

**Inherited spec assumptions:** A3 (delivery = oldest member appearance — implemented over member
sets only; a `spec.md` merely existing on disk never confers delivery, and `_all_feature_names`'
disk∪history union from release-board B1 is what makes a renamed or deleted directory still score);
A5 (cadence over `n = tags − 1`, earliest tag `null`+reason, span as two endpoint dates); A6 (the
open window is not a delivery); A7 (`gap_days` distinct from `days_since_tag`); A8 (visual language
not reopened — new styles use the shipped `:root` tokens only). A1/A2 are resolved in the spec.

**Inherited spec-gate note (stale, corrected — review F13):** this note previously claimed the
spec's SPEC GATE still showed one unchecked box (the clarify-pass line). That was fixed directly in
`spec.md` before `/increment` started (the checkbox itself was corrected to match its own already-
resolved C1-C11 text), but this note was never updated to match — re-verified now: all ten SPEC
GATE boxes in `spec.md` are checked. Left here, corrected in place, as the record of what happened
rather than deleted — a stale note is itself a small defect (CLAUDE.md's own "a stale block is a
defect, not a cosmetic issue"), so it gets fixed, not silently removed.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (six, including the ADR-0 tension A1
  resolved and the "one traversal for both anchors" trap)
- [x] Architecture respects the constitution's technical constraints — `_esc` choke-point, named-error
  taxonomy with **no** new class, no `datetime.now()`, no new flag/subcommand, `gitboard` stays
  graph-free, zero new runtime dependencies, ADR-0 (nothing re-derived; membership, ranges and status
  untouched), ADR-4 (determinism), ADR-5 (one offline self-contained file), MTA-001 (`n` beside every
  figure; the strip refuses itself rather than inventing a threshold), §3/§6 (no verdict, no
  value-dependent colour, no person-level figure). No conflict recorded.
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task (AC-1.1/1.2/1.4 → T1;
  AC-1.3/1.5 → T2; AC-2.1-2.4 → T4; AC-2.5-2.7 → T5; AC-3.1 → T6/T7; AC-3.2/3.3/3.7 → T8;
  AC-3.4 → T4/T6; AC-3.5 → T6/T7; AC-3.6 → T3; AC-4.1-4.4 → T10; NFR-1 → T3/T11; NFR-2 → T1/T11;
  NFR-3 → T5/T9; NFR-4 → T7/T10; NFR-5 → T6/T8; NFR-6 → T1/T6/T9; NFR-7 → T7/T8/T9/T11;
  NFR-8 → T2/T11)
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies (walking skeleton at T1; T3 is independent and can run in
  parallel with T1/T2)
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
