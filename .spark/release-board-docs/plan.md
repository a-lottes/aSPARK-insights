# Plan: release-board-docs

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/release-board-docs/spec.md` (must be `approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-23 |

**Handoff**
- **Status:** `approved` (2026-08-23, user approval in conversation) — header table authoritative for `Status`.
- **Summary:** A4 resolved to **shape (b): one file, `<details>` collapse-in-place**, with each
  feature's documents embedded **exactly once** (deduplicated across the releases it appears in)
  and a stated, measured weight budget (A5). Two new pure modules — `artifactcontent.py` (bounded
  read, US-2) and `markdownlite.py` (bounded Markdown→HTML, US-3) — behind the existing pure
  renderer; zero new runtime dependencies; zero JavaScript.
- **Open:** `0 tasks not done` — all 11 tasks `done` (2026-08-23). Full suite green (569 tests: T1
  order-flip, T2-T6 `artifactcontent.py`/document-viewing, T7-T10 `markdownlite.py`, T11 close-out).
  Real measured page weight against this repo: 1,314,560 bytes, well under the 5 MB ceiling (§1).
  See §3.
- **Binding ruling:** §3 Task Breakdown for current task status; a plan revision after review/QA
  findings updates §1/§3 in place, never a new section.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as
  a finding at the next `/peer-review` and proceed.

## 1. Architecture Decision

- **Context:** `releaseboard_report.py` (v0.9.0) is a pure `render_release_board_html(data) -> str`
  over `build_release_map()`'s dict, plus a thin writer. It has no I/O in the render path (the
  determinism and unit-test seam), no JS, one output file, and one escape choke-point (`_esc`).
  US-1 is a display-order flip inside that renderer. US-2/US-3 add something the module has never
  done: **read whole files** and **parse Markdown** — this repo has zero Markdown-parsing capability
  today. A4/A5 (file shape, weight ceiling) were parked for this pass.
  **Recounted on disk today (2026-08-23, `rg` line count over `.spark/*/{spec,plan,review,qa,release}.md`),
  not taken from the spec:** **8,663 lines across the 9 shipped features' 44 artifact files** — higher
  than the spec's 7,404 (that count predates `git-native-mid-cycle-board/release.md` and a grown
  `measurement-honesty/spec.md`); largest feature `measurement-honesty` at **1,260** lines, largest
  file `measurement-honesty/spec.md` at **597** lines. Length distribution over the same corpus:
  8,023 non-empty lines, 3,909 ≥90 chars, 643 ≥300, 250 ≥600, 19 ≥1,500 — integrating the buckets
  gives **≈0.95 MB of raw artifact Markdown**, i.e. **≈1.7-2.0 MB of embedded HTML body** once
  escaped and tagged (an estimate from the measured distribution; T11 records the real rendered
  byte count). **T11 measured, real (2026-08-23):** the actual rendered `release-board.html`
  against this repo's own 10 releases is **1,314,560 bytes (≈1.25 MB)** — comfortably under both
  the 2.5 MB per-page document budget and the 5 MB ceiling (≈26% of it), and lower than the
  estimate above because dedup means the ≈0.95 MB of real corpus is embedded once each, not
  inflated by escaping/tagging as much as the worst-case estimate assumed. One further multiplier the spec did not price: a feature is a member of *every*
  release its directory was touched in, so naive embedding would ship the same document 2-3×.
- **Decision:** **Shape (b) — one file, `<details>`/`<summary>` collapse-in-place**, keeping
  `release-board.html` the single artifact both prior specs decided on. Three rules make the weight
  argument hold instead of hand-waving it: (1) **dedup** — each feature's 5 documents are embedded
  exactly once, under its *first* occurrence in the new newest-first display order; every later
  occurrence renders an in-page anchor link to that block, so the embedded corpus equals the real
  corpus (≈0.95 MB), never a multiple of it; (2) **per-document bound** — 1,200 lines or 200 KB,
  whichever trips first (2× today's largest real document), disclosed via the existing
  `.truncation-note`; (3) **page budget (A5)** — 2.5 MB of raw document text consumed in display
  order, after which remaining documents are not embedded and are disclosed by count and on-disk
  path, giving a hard **≤5 MB rendered page ceiling** to verify at `/demo-day`. Because a closed
  `<details>` subtree is never laid out or painted, the practical cost of the bytes is parse +
  DOM-build only, not render. Two new pure modules sit behind the renderer:
  `gitboard/artifactcontent.py` (bounded read → dict, mirroring `artifactstatus.py`'s
  honest-degradation contract, never raising) and `gitboard/markdownlite.py` (pure `str -> str`,
  bounded to A3's constructs). Reading happens in `_cmd_releases`/a collector — **never** inside the
  pure renderer, which gains one additive optional `documents=None` argument. US-2 ships with the
  document body as escaped `<pre>` text; US-3 swaps one call site to `markdownlite`, so the
  Must survives the Should being deferred (C2).
- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | (a) One file, every document expanded inline | Same bytes as (b) with none of the benefits: ≈1.7-2.0 MB of *painted*, laid-out content in one scroll, burying the index the whole page exists for, and making the Designer's findings 3/8 (confusing the board's status with a document's prose, losing your place) worse rather than better. Collapse costs nothing and fixes exactly that. |
  | (c) Genuine multi-file site (`index.html` + per-feature files) | Genuinely lighter per view, but pays for it three times: it reverses `release-board` A2 and `release-board-html`'s Out-of-Scope line; it weakens ADR-5's "one self-contained file you can attach to a mail" to "a directory you must keep together"; and it creates a **new arbitrary-write surface** — output filenames derived from `.spark/` directory names — in a project whose security lens exists because of exactly that class of bug (foundation B5). At ≈0.95 MB of real corpus and ~100 KB growth per cycle, that price buys headroom we do not need yet (YAGNI). |
  | (d) Narrower middle ground: shipped page untouched, only new document content in extra file(s) | Still (c)'s costs (new path surface, multi-file `--output` contract, a navigation event needing finding 8's new affordance) for a smaller share of (c)'s benefit, and it splits one page's wayfinding across two documents. Kept as the documented escape hatch if T11's measured page weight lands materially above the 5 MB ceiling. |
  | A Markdown dependency (`markdown`, `mistune`, `markdown-it-py`) | Breaks the zero-new-runtime-dep precedent held across all three prior HTML surfaces (NFR-3), and every one of them passes raw HTML through by default — which would put a second, un-`_esc`-ed path to the page directly against NFR-2's single-choke-point guarantee, so we would be configuring and re-testing an escaping surface we did not write. A3's bounded construct set is line-oriented and small; we write it (T7-T9) and own its escaping. |
  | Embedding document text into `build_release_map()`'s dict | Would put ~1 MB of file content into `--format json` stdout — a large, unrequested change to a shipped contract, and it would make the JSON path pay for an HTML-only feature. The collector runs only on the `--format html` branch. |
- **Consequences:** *Easier* — the renderer stays pure and dependency-free, so every AC except the
  browser-only ones is unit-testable on fixture strings with no git; finding 8's navigation problem
  mostly evaporates (no page load, no scroll jump, no lost position) and needs only a
  collapse-return anchor; table-caption pressure (finding 7) drops because a closed `<details>` is
  invisible to a screen reader's table list; `--output`/`--help` and ADR-5 need no change at all.
  *Harder* — we own a Markdown renderer, including its own escaping and its own link-scheme
  allowlist (`[x](javascript:…)` is a genuinely new NFR-2 surface); heading depth needs the ARIA
  mapping below; and the page is now weight-bounded by a rule that must actually be measured, not
  asserted.
- **Named sub-decisions (Designer findings 2, 5, 6, 7 — answered here, not left to `/increment`):**
  - **Heading depth (finding 2, AC-3.1):** the page keeps its shipped h1→h4; `<summary>` is a label,
    **not** a heading, so it costs no level. Embedded document headings map `#`→`<h5>`, `##`→`<h6>`,
    `###`→`<div role="heading" aria-level="7">`, `####`→`aria-level="8"`, all styled by one class so
    the visual hierarchy matches the semantic one. Emitted level is **clamped**: the first heading in
    a document is always level 5 and no heading is ever more than one level deeper than the
    preceding one, so a source that skips a level cannot produce a skipped level on the page.
    `#####`/deeper is outside A3 and degrades to bold text (AC-3.4).
  - **Truncation UI (finding 5, AC-2.5):** confirmed as proposed — the existing `.truncation-note`
    idiom, verbatim ("Showing the first 1,200 of 1,940 lines of this document."). No new affordance.
  - **Checklists (finding 6, AC-3.3):** **refined** away from the Designer's primary proposal to the
    named fallback — `☑`/`☐` glyph (`aria-hidden`) plus a visually-hidden "checked"/"unchecked"
    text prefix, on a `list-style:none` item. Reason: a `disabled` native checkbox is not focusable,
    renders through browser-controlled `accent-color`/`color-scheme` that this dark page does not
    own, and its contrast therefore cannot be measured with the `getComputedStyle` technique this
    project requires; a text glyph inherits `--text-primary`, is measurable like every other string,
    and cannot read as editable. Glyph-availability (tofu) is a real offline-font risk — checked at
    `/demo-day`, with `[x]`/`[ ]` in the monospace stack as the recorded fallback.
  - **Table captions (finding 7, AC-3.2):** an embedded table's `<caption>` is its nearest preceding
    document heading text, truncated to 60 chars (B2's clipping lesson); if the table has no
    preceding heading, `<caption>` is omitted rather than filled with a generic label.

## 2. Affected Components

- **NEW `src/aspark_insights/gitboard/artifactcontent.py`** — `read_artifact_document(path, *, max_lines, max_bytes) -> dict`
  (`{"text", "total_lines", "shown_lines", "truncated", "empty", "reason"}`) and
  `collect_release_documents(repo_root, data, *, budget_bytes) -> dict`. Same contract shape as
  `artifactstatus.py`: never raises, degrades to an honest `reason`. Kept separate from
  `artifactstatus.py` deliberately — that module's docstring makes "no other section of the body is
  parsed, at all" a load-bearing promise, and per CLAUDE.md's "don't over-generalize a fix onto
  callers that never asked for it", `build_release_map()`'s JSON path must keep its current
  header-table-only behavior.
- **NEW `src/aspark_insights/gitboard/markdownlite.py`** — `render_markdown(text, *, base_level=5) -> str`,
  pure, bounded to A3's construct set, every leaf text run through `_esc`, link `href` restricted to
  an allowlist (`http`, `https`, `mailto`, `#`, relative). Separate module so US-3 can be deferred
  or reverted at one call site.
- **MODIFIED `src/aspark_insights/gitboard/releaseboard_report.py`** — display-order flip + lead
  sentence (US-1); `render_release_board_html(data, documents=None)` (additive optional kwarg,
  NFR-3); `run_release_board_report(data, output, documents=None)`; new `.doc-*` CSS.
- **MODIFIED `src/aspark_insights/cli.py`** — `_cmd_releases` html branch calls the collector with
  `args.repo` and passes it through; `--output`/`--format` help text updated (still exactly one
  file, NFR-1).
- **MODIFIED `README.md`**, **`src/aspark_insights/__init__.py` + `pyproject.toml`** — release-board
  section; version `0.9.0` → `0.10.0` (real behavior change).
- **REUSED unchanged** — `render.py:_esc`; `releasemap.build_release_map` and its
  `_is_valid_feature_name`; `store.STORE_DIRNAME`; `errors.ReleaseMapUnreadableError` /
  `ReportUnwritableError`. **No new error class:** a document that cannot be read is not a CLI
  failure, it is a per-document `reason` string (AC-2.2), exactly like `artifactstatus.py`'s
  existing `"file not found"` — checked before adding, per the brief.
- **Dependencies:** zero new runtime dependencies (see §1's rejected alternative).
- **Scoping note:** no tool file was passed to this `/sprint-plan`, so no blast-radius query was
  run; *Affected Components* was scoped by hand from a full read of `releaseboard_report.py`,
  `artifactstatus.py`, `releasemap.py`, `cli.py`'s `releases` parser and `errors.py`.

## 3. Task Breakdown

US-1 = T1. US-2 (Must) = T2-T6. US-3 (Should) = T7-T10, deferrable as a block without touching
T1-T6 (C2). T11 closes whichever set shipped.

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Newest-first display order: partition `releases[]` by the `tag is null` discriminator (never by position), emit pseudo-release(s) first then real tags reversed, for **both** the index and the detail cards; anchors keep their original `releases[]` index so `rel-N` still identifies the same entry; fix the `oldest first.` lead sentence (finding 1) | US-1 | AC-1.1, AC-1.2, AC-1.3, AC-1.4 | – | `done` | A 10-entry fixture renders index rows and detail cards in identical newest-first order (pseudo first, `v0.1.0` last); every index row's `href` resolves to its own card's `id`; the lead sentence reads "newest first"; `--format json` stdout is byte-identical to before; member order and each member's 5-artifact row order are unchanged; tests prove each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_render.py, tests/test_releaseboard_cli.py |
| T2 | Walking skeleton for content: `read_artifact_document()` + `collect_release_documents()` (built from repo root + already-validated feature names) wired through `_cmd_releases` → `run_release_board_report` → `render_release_board_html(data, documents=...)`; each member artifact renders a closed `<details>` whose `<summary>` names the artifact and whose body is the raw document text inside `<pre>`, escaped via `_esc`; **dedup**: a feature's documents are embedded only under its first occurrence in display order, later occurrences render an anchor link to it; ids are position-derived (`doc-f<k>-<artifact>`), never the feature text | US-2 | AC-2.1, NFR-1, NFR-3 | T1 | `done` | `insights releases --format html` against this repo writes one file in which `release-board-html`'s own `review.md` prose ("Overall impression" text and its 5 findings) is present and reachable by opening a `<details>`; each feature's document set appears exactly once in the file (no duplicate ids) with every other occurrence linking to it; `render_release_board_html(data)` with no `documents` argument produces byte-identical output to T1's; tests prove all three — files: src/aspark_insights/gitboard/artifactcontent.py, src/aspark_insights/gitboard/releaseboard_report.py, src/aspark_insights/cli.py, tests/test_artifactcontent.py, tests/test_releaseboard_docs.py |
| T3 | Honest per-document states: missing file, unreadable file (permission/`UnicodeDecodeError`), and empty (0-byte) file each produce a distinct, named, visible outcome — never a raw traceback, never an indistinguishable blank block, never a stale value | US-2 | AC-2.2, AC-2.3 | T2 | `done` | Fixtures for a missing path, a chmod-000/undecodable file and a 0-byte file each render a distinct stated message (the specific reason for the failures, "this document is empty" for the empty case) visually distinct from each other and from a truncated document; `read_artifact_document` returns rather than raises in all three; tests cover each — files: src/aspark_insights/gitboard/artifactcontent.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_artifactcontent.py |
| T4 | Bounds and disclosure (A5): per-document cap of 1,200 lines or 200 KB (whichever first) with a `.truncation-note` stating shown-of-total lines; page budget of 2,500,000 bytes of raw document text consumed in display order, after which documents are not embedded and a page-level `.truncation-note` states how many and where they live on disk | US-2 | AC-2.5, NFR-4 | T3 | `done` | A 3,000-line fixture embeds 1,200 lines and states "Showing the first 1,200 of 3,000 lines of this document."; a single-line 1 MB fixture trips the byte cap and discloses it; a fixture corpus exceeding the page budget embeds each feature whose own size still fits the *remaining* budget at its turn in display order — best-fit, not a hard stop once one feature is skipped, since a later smaller feature can still fit (review F7: recorded here deliberately, deterministic and still <= budget either way) — and a page-level `.truncation-note` discloses the count of features left out plus each one's `.spark/<feature>/` path; no read is unbounded; tests cover all four — files: src/aspark_insights/gitboard/artifactcontent.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_artifactcontent.py, tests/test_releaseboard_docs.py |
| T5 | Document-content visual frame and wayfinding (findings 3, 4, 8): a `.doc-content` block visually unlike `.release-card`/`.badge` (flat `--bg-secondary`, left accent rule, no large radius) carrying a persistent `.doc-provenance` label "Document content — read-only, as extracted from `<repo-relative path>`"; prose/list `max-width: 74ch` while tables and `<pre>` stay full width; every document block ends with a `.back-link`-styled "↑ Back to `<member>`" anchor to its member block's id | US-2 | AC-2.1, NFR-5 | T2 | `done` | Every embedded document block renders the provenance label with its real repo-relative path and is styled by `.doc-content`, not `.release-card`; a paragraph inside it computes to ≤74ch while an embedded table is unconstrained; each block's closing anchor resolves to an existing member id; a relative-luminance unit test proves every new text/background pair clears its WCAG floor; tests cover each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_docs.py |
| T6 | US-2 hardening: hand-crafted hostile artifact fixture (`<script>`, `onerror=`, `<img src=x onerror>`, a `</pre>`-breakout attempt and a status-shaped `Status: failed` line) inside a document **body**; re-validate every feature name and artifact filename before it becomes a path in the collector (empty, `../`, absolute, symlink-escape) even though `releasemap` already validated it; determinism | US-2 | NFR-2, NFR-6 | T4, T5 | `done` | Every hostile string renders as inert visible text with no executable attribute or tag surviving, including no `<pre>` breakout; a `../`/absolute/empty feature name never produces a read outside `<repo>/.spark/`; a malformed `documents` mapping raises `ReleaseMapUnreadableError` with exit 1, never a traceback; two renders over one fixture corpus are byte-identical; tests cover each — files: src/aspark_insights/gitboard/artifactcontent.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_docs.py, tests/test_releaseboard_determinism.py |
| T7 | `markdownlite` core (pure `str -> str`): ATX headings with §1's clamped `h5`/`h6`/`aria-level` mapping, paragraphs, bold/italic, inline code, fenced code, horizontal rules, links with a scheme allowlist, `<!-- -->` comments stripped, and any unrecognized construct emitted as plain visible text | US-3 | AC-3.1, AC-3.4, NFR-2 | T2 | `done` | A fixture exercising each named construct produces the expected element for it; the first heading is `h5` and a source that skips `#`→`###` still emits no skipped level; `[x](javascript:alert(1))` renders as plain text, not an anchor; a blockquote/reference link/raw HTML table renders as readable escaped text with the rest of the document intact; every leaf text run passes through `_esc`; tests cover each — files: src/aspark_insights/gitboard/markdownlite.py, tests/test_markdownlite.py |
| T8 | Pipe tables → real `<table>`/`<thead>`/`<th scope="col">`, with `<caption>` sourced from the nearest preceding heading (60-char truncation) and omitted when there is none; ragged rows tolerated without dropping cells | US-3 | AC-3.2, NFR-5 | T7 | `done` | This repo's own `spec.md` AC table and a `review.md` findings table render as real `<table>` markup with `<th scope="col">` header cells and no raw `|` text; a table under "## Acceptance criteria" gets that caption, a table with no preceding heading gets none; a row with too few/many cells renders every cell it has without crashing; tests cover each — files: src/aspark_insights/gitboard/markdownlite.py, tests/test_markdownlite.py |
| T9 | Lists: bullet, numbered, and checklists — `- [x]`/`- [ ]` render as `☑`/`☐` (`aria-hidden`) plus a visually-hidden "checked"/"unchecked" prefix on a `list-style:none` item, distinguishable from each other and from a plain bullet without color | US-3 | AC-3.3, NFR-5 | T7 | `done` | Checked, unchecked and plain bullet items are distinguishable by text/glyph content alone with color removed; the accessible name of a checked item begins with "checked"; no CSS rule gives checklist state a distinct hue; nested lists render nested, not flattened; tests cover each — files: src/aspark_insights/gitboard/markdownlite.py, src/aspark_insights/gitboard/releaseboard_report.py, tests/test_markdownlite.py |
| T10 | Switch the document body call site from escaped `<pre>` to `render_markdown(...)`; re-run the hostile fixture through the structured path; assert full-page heading order | US-3 | AC-3.1, AC-3.2, NFR-2, NFR-5 | T6, T8, T9 | `done` | The rendered page contains exactly one `<h1>`, no skipped heading level anywhere in document order, and no embedded document introduces a second `<h1>`/`<h2>`; T6's hostile fixture is inert through the structured renderer too (re-run, not assumed); reverting this one call site restores T6's `<pre>` behavior with the suite still green; tests cover each — files: src/aspark_insights/gitboard/releaseboard_report.py, tests/test_releaseboard_docs.py |
| T11 | Close-out: `--help` for `releases --output`/`--format html` states exactly what is written (one file, its name, that it embeds document content) and README's release-board section matches; version `0.10.0`; **measure and record** the real rendered page size against this repo and confirm it against the 5 MB ceiling | US-1, US-2, US-3 | NFR-1, NFR-3, NFR-4 | T6 | `done` | `insights releases --help` names the single output file and the embedded-content behavior; README's example block matches actual behavior; `__version__` and `pyproject.toml` read `0.10.0`; a test asserts the rendered page for the real repo is ≤5,000,000 bytes and the measured figure is written into this plan's §1 in place; no existing export's signature changed — files: src/aspark_insights/cli.py, README.md, src/aspark_insights/__init__.py, pyproject.toml, tests/test_releaseboard_docs.py, .spark/release-board-docs/plan.md |

## 4. Test Strategy

- **Unit — pure renderer on fixture dicts (no git), `tests/test_releaseboard_render.py` /
  `tests/test_releaseboard_docs.py`:** US-1's ordering, anchor pairing and lead sentence (T1);
  document block markup, dedup, honest states, truncation, provenance label and back-anchor
  (T2-T5); contrast of every new pair via the repo's existing relative-luminance helper.
- **Unit — pure functions on fixture strings, `tests/test_artifactcontent.py` /
  `tests/test_markdownlite.py`:** the bounded read (missing/unreadable/empty/oversize) and every
  A3 construct plus the unrecognized-construct degradation. No git, no HTML page needed — this is
  where US-3 gets most of its coverage.
- **Security / adversarial (NFR-2, both Must stories):** a hand-crafted hostile artifact **body**
  fixture — not a copy of the existing status-cell test — covering `<script>`, event-handler
  attributes, a `</pre>` breakout attempt, `javascript:` link targets and a status-shaped prose
  line; run once against the `<pre>` path (T6) and **again** against the structured path (T10),
  per this project's adversarial-reproduction bar. Plus the §4 hostile-input checklist re-applied
  to every feature name and filename that becomes a path in the collector.
- **Determinism (NFR-6):** byte-identical render across two calls over a fixed fixture corpus,
  including truncation and page-budget behavior (budget consumption must be order-deterministic).
- **Integration (real git, never mocked — house rule):** one end-to-end
  `insights releases --format html` against a real temp git repo with real `.spark/` files, and one
  against this repo itself for the T11 weight measurement. No new git surface is added, so this
  stays a smoke test, not a second git suite.
- **CLI:** `--format json` stdout byte-unchanged (AC-1.3); `--output` still writes exactly one
  file; `--help` text assertions (T11).
- **Deliberately left to `/demo-day`** (only observable in a real browser, per NFR-5's own method —
  measured, never eyeballed): heading order including the `aria-level="7"/"8"` blocks read through
  the accessibility tree; `getComputedStyle` contrast on `.doc-content`, `.doc-provenance` and the
  checklist glyphs; the `☑`/`☐` glyph rendering without tofu offline; keyboard operability of
  `<details>`/`<summary>` and the back-anchors; 375px no-horizontal-scroll for embedded tables and
  long unwrapped table cells; real page-load feel at the measured weight; a genuinely
  network-disabled load (ADR-5).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Measured page weight lands materially above the ≈2 MB estimate (long unwrapped table rows expand worse than modeled) | The 5 MB ceiling (A5) is breached and the single-file decision is wrong | T11 measures the real render before ship, not after; the page budget (T4) caps it by construction; if the measurement embarrasses the decision, §1's alternative (d) is the recorded, pre-argued escape hatch — a smaller reversal than a full multi-page site |
| Hand-written Markdown renderer is the largest genuinely new code in this plan and its escaping is now our problem, not a library's | An escaping hole in a page that renders untrusted-ish file content (NFR-2, the project's strongest bar) | Every leaf text run through the existing `_esc` choke-point with no second path to output; link scheme allowlist; hostile fixture run twice (T6 and again at T10); the US-3 block is deferrable in full without touching the Must path |
| `<details>` content is skipped by find-in-page in some browsers | The maintainer Ctrl+Fs the board, finds nothing, and concludes the content is missing | Disclosed at `/demo-day` as a known trait of the chosen shape; the summary line always carries the artifact name and path so the block is findable; full-text search is explicitly out of scope this cycle |
| Dedup makes a feature's documents appear under only one release card | A reader drills into `v0.5.0`, sees a link rather than the content, and thinks the content is missing | Every non-first occurrence renders an explicit labelled anchor ("Documents shown under `<release>`"), not a silent omission; asserted in T2 |
| `aria-level="7"/"8"` is correct but unusual; a reviewer may read it as a workaround rather than a decision | Churn at `/peer-review` over a settled call | Recorded here as the named answer to finding 2, with the clamping rule that makes "no skipped level" structurally true; verified through the accessibility tree at `/demo-day`, not by reading the source |
| Reading ~44 files on every html render slows the command | A previously fast command becomes noticeably slower | Reads are bounded per document and by page budget (T4) and happen only on the `--format html` branch; `--format json` reads nothing new |

**Inherited spec assumptions:** A1 (newest-first definition — implemented exactly, discriminator-driven);
A2 (scope is the same 5 artifacts — the collector reads no other filename); A3 (construct set is
bounded, not a Markdown-correctness claim — stated in `markdownlite.py`'s docstring, mirroring
`artifactstatus.py`'s own "deliberately not tolerant" framing); A6 (visual language not reopened —
new `.doc-*` styles reuse the shipped `:root` tokens only). A4/A5 are resolved above, not inherited.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints — `_esc` choke-point, named-error
  taxonomy reused with no new class, no `datetime.now()`, `--output` contract unchanged and documented
  in `--help`, reproducibility, real-git integration, zero new runtime dependency, ADR-0 (nothing
  re-derived) and ADR-5 (one self-contained offline file) both intact. No conflict recorded.
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task (AC-1.1-1.4 → T1;
  AC-2.1 → T2/T5; AC-2.2/2.3 → T3; AC-2.4 → T6; AC-2.5 → T4; AC-3.1-3.4 → T7-T10; NFR-1 → T2/T11;
  NFR-2 → T6/T7/T10; NFR-3 → T2/T11; NFR-4 → T4/T11; NFR-5 → T5/T8/T9/T10; NFR-6 → T6)
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies (walking skeletons at T1 and T2)
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
