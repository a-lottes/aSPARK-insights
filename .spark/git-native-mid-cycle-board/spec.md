# Spec: git-native-mid-cycle-board

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-10 |
| **Ticket** | none |

<!-- APPROVED 2026-08-11. Route to this state, for a reader who wasn't here:
     A1/A2/C2/C3/C4/C5 ruled by the user 2026-08-10; /look-and-feel pass 1 the same day
     (Blocker + 4 Major → C6–C10); three derivations + a layout reorganization approved from a
     visual preview (C11–C16); /look-and-feel pass 2 on 2026-08-11 re-derived pass 1's verdicts
     adversarially and added its own Blocker + 7 Major + 3 Minor; the user then cut the per-day
     activity strip to a §6 follow-up (C17), and the remaining findings landed as C18–C24.
     A verification pass confirmed each amendment at the strength its finding required and
     found six Minor residuals — two corrected here, four carried to /sprint-plan, /increment
     and /demo-day via §8's routing block. A8 ruled "accept the divergence as specified".
     §8 was condensed to findings/verdicts/routing + the four independently re-verified
     figures; both passes' full derivations were removed once ruled on. -->

## 1. Problem & Goal

- **Problem:** Insights answers exactly one question — "how complete is our traceability,
  point-in-time, from `aspark-graph`." It has *no* notion of "what shipped since when" or
  "what is in flight right now," and it structurally cannot run at all against a repo with no
  graph built (`build` raises `GraphNotBuiltError`). So the maintainer mid-cycle, and *any*
  git repo without the aSPARK toolchain, gets nothing from this product.
- **Goal:** (1) Prove Insights can produce a deterministic, provenance-sealed, honest-null
  answer against a repository with **zero graph and zero `.spark/`** — the strategic wedge
  toward "standalone, any repo." (2) Give that answer for the one question the graph does not
  answer at all: what has landed since the most recent release marker, *and over what elapsed
  time* — a count without a time span is not an answer (C11).
- **Success signal:** Running the new command on this repo returns a commit count since the
  latest tag that matches `git rev-list --count <tag>..HEAD` exactly, alongside the elapsed
  days since that tag; on a tagless repo it returns `value: null` with a reason; it emits
  **no** author name/email in any output; it succeeds on a directory containing neither
  `.aspark-graph/` nor `.spark/` without ever invoking `GraphPort`; and every output's
  provenance carries a `source: git-interim` marker naming it as the ADR-2 fallback, not
  graph-sourced.
- **Why now:** If we never build it, the family loses nothing — graph's G1/G2 (Release/Commit
  nodes) will eventually give a richer, authoritative timeline. What is lost is only the
  **standalone proof** — US-2, ruled Must, and confirmed by the user (A2, 2026-08-10) as **the
  actual justification for building this feature**, over the smaller "prettier git log"
  framing. The git-derived commit/branch data by itself is two `git` commands away
  (`git rev-list --count`, `git branch -v`) and would not alone clear this project's own
  forcing-question bar ("what happens if we never build this?") — it is the demonstrated
  ability to run Insights against *any* git repo, with no graph and no `.spark/`, that does.

## 2. Target Users

- **The maintainer mid-cycle (primary, concrete: Andreas, sole dev today).** Wants "what
  landed since v0.x, deterministically and consistently with the rest of Insights" without
  standing up a graph.
- **A developer/maintainer of an arbitrary git repo (hypothesised, not yet observed).** The
  generic-repo audience is the *bet* this feature places, not a user we can point to today —
  named honestly as a hypothesis, not a validated persona.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | **Constitutional grounding — RESOLVED 2026-08-10, ruled "yes, as a time-boxed fallback."** This is not a rules violation needing a carved-out exception: BACKLOG.md §4's "Eigener Git-Parser" row already reads *"Nur der dokumentierte Fallback, falls `touches` abgelehnt wird"* (only the documented fallback, if `touches` is rejected), and the I3 `flow-metrics` backlog entry (§3) already reads *"sonst dokumentierter Interim-Git-Adapter als Fallback, ADR-2"* (otherwise the documented interim git adapter as fallback, ADR-2). This feature **activates the pre-anticipated ADR-2 fallback path for real**, rather than opening a new exception. Made enforceable, not just promised: every output's provenance self-discloses `source: git-interim` (AC-1.9), distinct from graph-sourced facts — this is what lets the graph's G1/G2 timeline supersede it later without ambiguity about which source is authoritative, rather than "yields to the graph" being an unchecked aspiration. |
| A2 | **RESOLVED 2026-08-10, ruled "the standalone proof, not the git data itself."** Confirmed as originally framed by the PO. US-2 (Must) is the load-bearing story; US-1's data is necessary evidence for US-2, not the point on its own. |
| A3 | "Most recent tag" = the nearest tag reachable from `HEAD` by commit topology (`git describe --tags --abbrev=0` semantics), **not** newest-by-creation-date; any tag string counts (no semver parsing). **RESOLVED 2026-08-10** — matches AC-1.1 as originally drafted; no wording change needed. |
| A4 | "Age" and any elapsed-time figure — including days-since-tag (AC-1.10) — is computed relative to the caller-supplied `as_of`, never `datetime.now()` (ADR-4). | Accepted — binding NFR-5. |
| A5 | Architecture lean: a **separate, standalone read-only command** with its own `as_of`, that does **not** call `GraphPort` and does **not** feed the graph-coupled `Snapshot`. Rationale in §7/C1. Finer seam naming (a `GitPort` mirroring `PolicyPort`'s null-adapter, exact subcommand name, whether it reuses `render.py`) is a `/sprint-plan` call — unchanged by the design review or the layout reorganization: AC-4.7/C15 govern only the *rendered result*, not whether the code imports `render.py`. | Product boundary accepted; implementation deferred to plan. |
| A6 | The deferred larger ideas (a pluggable `TrackerPort` for GitHub/Jira/Linear; DORA/flow via graph G1/G2, backlog I3) are **not** in this feature. The deferred strategic fork "family-scoped vs standalone" (backlog I9, open question 1) is *implicitly pre-empted* by shipping a standalone surface — named as a risk, not decided here. | Named risk, not gate-blocking — unchanged. |
| A7 | The two derivations that survive the 2026-08-11 scope ruling (days-since-tag, work-type mix) invent **no new data source**: each is a grouping or subtraction over the commits AC-1.1 already returns, plus `as_of`. None reads a second source, none contacts the graph, none introduces a metric requiring the registry's versioning machinery (this feature does not feed the metric registry — C1/A5). | Accepted; bounded by AC-1.10/1.12 and NFR-3's amended parsing rule. |
| A8 | **Constitution §4 tension — RESOLVED 2026-08-11: the user ruled "accept the divergence as specified."** The commit listing keeps the scannable-list shape with explicit per-field labels (AC-4.12(b)); the branch listing — the genuinely tabular comparison data — stays a real `<table>`. Grounding accepted: §4's bar binds *tabular metric data*, and the shipped report already renders `.metric-grid`/`.metric-card` as `<div>`s under this same constitution without objection, so the mechanism has always been understood to bind tabular data rather than every block; the provenance `<dl>` is arguably better semantics than the shipped `<th scope="col">Field</th><th>Value</th>` it replaces. Original wording of the tension follows for the record. **Constitution §4 tension — recorded.** §4's accessibility bar is worded as a *mechanism* ("real `<table>`/`<th>`… not `<div>` grids"), but the approved layout (C14) replaces the commit list with a scannable list and the provenance table with a two-column grid. AC-4.6/AC-4.12 preserve the *guarantee* (programmatic field/value pairing; per-item structure with a named mechanism) while changing the mechanism for two of four surfaces — the branch listing stays a real `<table>`. This is a genuine, deliberate divergence from a mechanism-worded bar, not an oversight, and is recorded here rather than silently absorbed so the SPEC GATE's "conflicts recorded" box is honestly ticked. Ruled 2026-08-11: accepted as specified. | **RESOLVED.** |

## 4. User Stories

### US-1 (Must): Commits since the latest release marker, as scriptable JSON

> As a repo maintainer, I want the count, elapsed time and work-type mix of the commits since
> the most recent tag, so that I can see what has landed but not yet been released — without a
> graph.

**Acceptance criteria:**

- [ ] AC-1.1: Given a repo whose `HEAD` has a most-recent reachable tag `T` (nearest by commit topology, `git describe --tags --abbrev=0` semantics — A3), when I run the command, then the output's commit count equals `git rev-list --count T..HEAD` and lists each commit's short hash, subject (first line only) and date.
- [ ] AC-1.2: Given a repo with **no tags**, when I run the command, then the "commits since last release" value is `null` with a non-empty reason (e.g. "repository has no tags; commits-since-release is undefined without a release marker") and exit code is `0` — this is an honest null, not a failure.
- [ ] AC-1.3: Given any repo, when I run the command, then the output contains **no** author name, author email, or committer identity, and no field grouped/sorted/aggregated by person (constitution §6, NFR-3).
- [ ] AC-1.4: Given `--repo` set to an empty string, a `../` traversal, an absolute path, a non-git directory, or a directory with a corrupt `.git`, when I run the command, then it exits `1` with a named error on stderr and **never** prints a raw traceback (constitution §6; §4 hostile-input checklist).
- [ ] AC-1.5: Given `git` is not on `PATH`, when I run the command, then it exits `1` with a named error explaining git is required — distinct from the AC-1.2 "no tag" null.
- [ ] AC-1.6: Given a fixed repo `HEAD` and a fixed `as_of`, when I run the command twice, then stdout is byte-identical both times (JSON `sort_keys=True`).
- [ ] AC-1.7: Given a commit subject containing HTML/special characters, when that subject appears in any rendered (non-JSON) surface, then it is escaped through the existing render escape choke-point; in JSON it is carried verbatim as an opaque string, parsed only for the type token NFR-3 permits.
- [ ] AC-1.8: Given a shallow clone (`git rev-parse --is-shallow-repository` is true), when I run the command, then the output discloses `shallow: true` so the counts are not silently mistrusted.
- [ ] AC-1.9: Given any output this feature produces (JSON or HTML), when its provenance/metadata is inspected, then it carries a `source: git-interim` marker (or equivalent explicit field) distinct from graph-sourced facts, naming this as the ADR-2 documented interim fallback (A1) — so a value produced by this feature is never mistaken for a graph-sourced (G1/G2) figure, today or after graph ships release nodes.
- [ ] AC-1.10 (new per C11): Given a resolved tag `T`, when I run the command, then the output carries **days since `T`** — whole days from `T`'s commit date to `as_of`, never `now()` (A4). Two degradation cases: (a) given **no tag**, this figure is **absent entirely**, not a second null — AC-1.2's single null already explains the whole since-release frame (one null, one reason, per `measurement-honesty`'s AC-1.4 precedence precedent); (b) given a tag whose commit date cannot be read, the figure is `null` with a reason naming that specific cause, never a guessed or zero span.
- [ ] ~~AC-1.11~~ — **withdrawn 2026-08-11 (C17).** The per-day activity strip is cut from this feature and moved to §6 as a named follow-up. The ID is retired rather than reused or renumbered, so a later reader of `/sprint-plan` or the follow-up spec finds the decision instead of a gap.
- [ ] AC-1.12 (new per C13): Given commits since `T`, when I run the command, then the output carries a **work-type breakdown** derived only from each subject's leading Conventional-Commit type token, matched case-insensitively and normalized to lowercase, against exactly this recognized set: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style` (an optional `(scope)` and/or `!` before the `:` is tolerated). Honest degradation, in precedence order: (a) given **fewer than 20%** of the commits carry a recognized token, the breakdown as a whole is `value: null` with a reason naming the counts (e.g. "3 of 47 commits carry a recognized Conventional Commit type; too few to characterize the work mix") and **no distribution is emitted or rendered**; (b) given at or above 20%, the breakdown is emitted with the unrecognized remainder always present as an explicit `unclassified` share — never hidden, never redistributed across the recognized types, never inferred from any other signal. A commit is never assigned a type by guesswork. **Frame preconditions (per C18/§8 finding 9):** (c) given **no tag**, the breakdown is **absent entirely** — never computed over all commits in the repo, because "commits since `T`" has no referent without `T`; emitting a real distribution beside AC-1.2's null would make every number true while the frame itself is invented (constitution §6); (d) given a resolved tag with **zero commits since it**, the classifiable ratio is 0/0 and therefore undefined — the breakdown is likewise **absent**, not `null` and not `0%`, since AC-4.13's true-zero state already answers the page's question.

### US-2 (Must): Runs against a repo with zero graph and zero `.spark/`

> As the maintainer, I want this command to work on any git repo with no aSPARK toolchain, so
> that Insights is proven to serve a standalone repo — the whole point of this feature (A2).

**Acceptance criteria:**

- [ ] AC-2.1: Given a git repo containing neither `.aspark-graph/` nor `.spark/`, when I run the command, then it returns the US-1 result and exits `0`.
- [ ] AC-2.2: When the command runs, then it never calls `GraphPort` / `LibraryInterimGraphPort` / `CLIGraphPort` and never requires `aspark-graph` to be installed or version-matched (verifiable by a test that runs it with the graph dependency absent/unpinned).
- [ ] AC-2.3: Given a directory that is not a git repository, when I run the command, then it reports the git-unavailable condition as an honest named result (mirroring `NullPolicyPort`'s "no source configured → honest unavailable"), never a fabricated zero.

### US-3 (Should): Local branch inventory with age relative to `as_of`

> As the maintainer, I want a list of local branches and how long since each last moved, so
> that I can see what is in flight — bounded honestly to what this checkout contains.

**Acceptance criteria:**

- [ ] AC-3.1: Given a repo with several local branches, when I run the command, then each `refs/heads/*` branch is listed with its tip short-hash, tip date, and an age in whole days computed as `as_of − tip-date` (never `now()`); the list carries **no** author identity.
- [ ] AC-3.2: Given a single-branch or CI checkout (only `main` present locally), when I run the command, then it reports exactly the branches present as a true statement about this checkout — not an error and not a claim about branches it cannot see.
- [ ] AC-3.3: Given a branch whose tip date cannot be read, when I run the command, then that branch's age is `null` with a reason, never a guessed number.

### US-4 (Must — re-prioritized from Should per C2, ruled 2026-08-10): Self-contained HTML view, consistent with the existing report

> As the maintainer, I want an offline HTML view of this data that answers "where do I stand"
> in one glance, in the same visual language as the snapshot report, so it reads as one
> product, not a competing surface.

The user chose JSON + HTML in one cycle over the PO's smaller JSON-only slice (C2), making
NFR-7's accessibility bars live now. `/look-and-feel` ran twice (§8): the first pass's Blocker
and four Major findings are folded into AC-4.2/4.5/4.6/4.7 and NFR-4/NFR-7 (C6–C10); a visual
preview added two surviving derivations (AC-1.10/1.12) and a layout reorganization
(AC-4.8–AC-4.13, C11–C15); the second pass's Blocker and Majors are folded in as C17–C22.
The per-day activity strip was **cut** on 2026-08-11 (C17) and is a named follow-up in §6.
Four §8 findings rated safe to apply inside existing AC/NFR wording at `/increment` time
(the "showing 50 of N" note, the absent badge on an unclassified row, `lang`/viewport/`<title>`,
and the programmatic name for the breakdown) are intentionally **not** amended here.

**Acceptance criteria:**

- [ ] AC-4.1: Given a produced view, when I open the HTML file with no network, then it renders fully (ADR-5: no external font/CDN/script fetch) and contains no executable JS.
- [ ] AC-4.2 (amended per C6): Given an honest-null value (no tag, an unreadable tag date per AC-1.10(b), a null branch age, or a nulled work-type breakdown per AC-1.12(a)), when rendered, then it uses the shipped report's dashed-border "not measured" card treatment — `render.py`'s `.metric-card--null` shape plus its `.null-value`/`.metric-value--null` italic treatment — rather than a new, unrelated null shape, together with its reason; visually distinguishable from a real value by more than color alone (constitution §4).
- [ ] AC-4.3: Given the view, when inspected, then it applies **no** red/green pass-fail coloring that implies a judgment — Insights measures, `aspark-ci` enforces (§3 off-limits); status is conveyed as text, not a verdict hue. This binds the work-type breakdown (AC-4.11) and the per-branch age bar too: neither may color a work type, a branch's age, or a busy/quiet period as good or bad.
- [ ] AC-4.4: Given the HTML surface writes a file, when run, then it honors a `--output` flag that redirects the write location, documented in `--help` (constitution "--output from day one"). The JSON-only command (US-1) writes nothing and needs no `--output`.
- [ ] AC-4.5 (rewritten per C7): Given the view, when inspected, then (a) the page renders its own provenance section (AC-4.6) and the `source: git-interim` marker (AC-1.9) lives inside it; (b) the marker is also legible near the top of the page without scrolling, as a labelled line (e.g. `INTERIM (git-native) — …`), so a reader skimming the page meets it immediately; (c) its visual treatment is neutral provenance — visually distinct from `.stale-cue`'s warning/alarm shape, since this is a status fact, not a warning — distinguished by a constant label token, never by hue alone.
- [ ] AC-4.6 (new per C8, Blocker; markup reconciled per C15): Given any report this feature produces, when rendered, then it includes a provenance section listing `as_of`, `insights_version`, the resolved tag (or its null value and reason), the `shallow` flag (AC-1.8), git-availability, the `source: git-interim` marker (AC-1.9), and any active bound disclosure (AC-1.12's classifiable share, NFR-4's 50-commit cap) — so no trust-bearing field, in particular the shallow-clone disclosure, is ever available in JSON only and silently absent from a page built to be skimmed and believed. The approved layout renders this as a compact two-column field/value grid rather than the existing report's full-width table (C15); whatever markup is used, **each field is programmatically associated with its value** (e.g. a `<dl>` of `<dt>`/`<dd>` pairs, or a table with row headers) — the pairing must survive as semantics, not as visual adjacency alone.
- [ ] AC-4.7 (new per C6; markup reconciled per C15): Given the HTML view, when compared against `render.py`'s shipped scorecard, then it reuses that report's visual vocabulary as the checked reference for US-4's "reads as one product" goal: `.metric-card`/`.metric-card--null` card shapes for the headline figures (AC-4.9), the `<h1>` + per-section `<h2>` heading structure, and the no-judgment-color rule (AC-4.3). Where the approved layout replaces a table with a list or grid (AC-4.6, AC-4.10), the reused vocabulary is the report's card/typographic scale and palette, not its `<table>` markup specifically — the accessibility bar moves with the shape (AC-4.12), it is not waived by it. **Which reference shapes exist, stated so this AC is enforceable rather than vacuous (per C19/§8):** `render.py` *does* ship a magnitude bar (`.metric-bar`/`.metric-bar-fill`) — the reference for the per-branch age bar — and a labelled stacked-proportion bar with an adjacent text legend (`.confidence-mix`/`.confidence-bar`/`.confidence-seg`/`.confidence-legend`) — the reference for AC-4.11's work-type breakdown. It ships **no** badge precedent, so the commit-row type badge is the one genuinely new primitive and must justify itself against AC-4.3 and NFR-7 on its own rather than claiming inherited approval. Whether the implementation literally imports `render.py` remains a `/sprint-plan` decision (A5); this AC governs only the rendered result.
- [ ] AC-4.8 (new per C14; degenerate states and the shallow qualifier added per C20/C21): Given a report with a resolved tag, when rendered, then a single plain-language answer sentence appears immediately after the interim marker (AC-4.13's fixed order), before any card or list, stating the count, the tag, the elapsed days, the branch count and the oldest branch age (e.g. "8 commits landed since `v0.4.0`, 6 days ago; 3 local branches, oldest moved 21 days ago"). Three degenerate states are stated **in words**, never as a silently-omitted clause or a `null`/`—` placeholder, and never as a second explanation for a cause AC-1.2 already explains once: (a) **no tag** — the sentence names that as the single reason the since-release frame is unavailable and states only what *is* known (e.g. "This repository has no tags, so there is no release marker to measure against. 3 local branches, oldest moved 21 days ago."), consistent with AC-1.10(a)'s "absent, not a second null"; (b) **zero commits since the tag** — a true zero, stated as such (e.g. "Nothing has landed since `v0.4.0`, tagged 6 days ago."), never as a null and never as an empty list; (c) **zero local branches** — stated plainly rather than omitted. **Shallow qualifier (C21):** given `shallow: true` (AC-1.8), the sentence's own count carries the qualifier inline (e.g. "at least 8 commits landed since…"), because the provenance grid that holds the `shallow` flag sits several blocks below an otherwise-unqualified exactness claim.
- [ ] AC-4.9 (new per C14; degenerate states per C20): Given the report, when rendered, then the headline figures (commits since tag, days since tag, branch count, oldest branch age) appear as a stat-card row **before** any list or table on the page, in `.metric-card` shape (AC-4.7), each card carrying its label and, for a null, AC-4.2's treatment. A figure that is **absent** rather than null (AC-1.10(a): days-since-tag on a tagless repo) renders **no card at all** — an absent figure must not be given a null card, which would assert "we tried and could not measure" where the truth is "this figure has no referent here". A **true zero** (zero commits since tag, zero branches) renders as a real value card showing `0`, never AC-4.2's dashed null treatment.
- [ ] AC-4.10 (new per C14; strip clauses withdrawn per C17): Given commits since `T`, when rendered, then the commit list renders as a scannable list — type badge, subject dominant, hash and date secondary — rather than four equally-weighted columns, subject to AC-4.12. *(The former clauses (a)–(c) governed the per-day activity strip and are withdrawn with it; see §6's follow-up entry.)*
- [ ] AC-4.11 (new per C13/C14; rewritten per C19/§8 finding 14 and C22/finding 17): Given a work-type breakdown at or above AC-1.12's 20% threshold, when rendered, then it follows `render.py`'s shipped `.confidence-mix` pattern rather than per-segment inline labels — which are unrenderable, since a 1-of-50 segment is ~6px while the label `refactor` needs ~55px: a single-fill proportional bar with hairline separators between segments, plus an **adjacent text legend** carrying every type name and its count/share. The `unclassified` share appears in bar and legend with the same weight as any recognized type (never hidden, never rounded away, never redistributed). **Segment and legend order is fixed and declared** (C22): the recognized-set order of AC-1.12 — `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style` — with `unclassified` last; types with a zero count are omitted from both bar and legend. Fixed order is what makes two runs of one repo visually comparable, which byte-stable output alone does not guarantee. Given the breakdown is null (AC-1.12(a)), then no distribution, empty bar, or placeholder chart renders — only AC-4.2's null card carrying the reason. Given it is **absent** (AC-1.12(c)/(d): no tag, or 0/0), then neither a bar nor a null card renders.
- [ ] AC-4.12 (new per C15; strengthened per C23/§8 finding 16): Given the layout replaces tables with lists/grids (AC-4.6, AC-4.10), when the rendered HTML is inspected, then the accessibility bar holds in the new shape **by a named mechanism, not an outcome claim**: (a) the **branch listing stays a real `<table>`** with `<th scope="col">` and a `<caption>` — the approved layout replaced the age *cell* with a bar, never the table itself, so nothing the user approved is reverted; (b) the **commit listing** may keep the approved scannable-list shape, but each item must carry **explicit per-field labels** — a `<dl>` of `<dt>`/`<dd>` pairs, or visually-hidden `<span>` labels — so **type, subject, hash and date** are distinguishable without relying on visual order (the type badge included: an unlabelled glyph announces "feat" with no indication of its role); (c) the listing as a whole carries a **programmatic name** (an `<h2>`, `aria-labelledby`, or `<caption>`); (d) the per-branch age bar carries its numeric age as text, not bar length alone. This supersedes C15's claim that "no accessibility guarantee from the previous table-based wording is dropped" — that claim did not survive re-derivation, since NFR-7 no longer carried any `table`/`th`/`scope`/`caption` token and "per-item structure" named no mechanism. The residual divergence from constitution §4's mechanism-worded bar is recorded as **A8**, open for the user.
- [ ] AC-4.13 (new per C24/§8 finding 15): Given the rendered page, when its block order is checked by byte offset in `outerHTML`, then it is exactly: `<h1>` → interim marker (AC-4.5b) → answer sentence (AC-4.8) → stat-card row (AC-4.9) → `<h2>` Work types (AC-4.11) → `<h2>` Commits (AC-4.10) → `<h2>` Branches (AC-3.1) → `<h2>` Provenance (AC-4.6). Every block after the stat-card row carries an `<h2>`, so the page has a navigable hierarchy rather than unlabelled content blocks; no two blocks separately claim to be "first" (AC-4.5b and AC-4.8 previously both did). A block whose content is absent — the work-type breakdown on a tagless repo (AC-1.12(c)) — omits its `<h2>` with the block, rather than leaving an empty labelled section.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | Results to stdout as `sort_keys=True` JSON; errors/diagnostics to stderr; exit `0` on success (incl. honest nulls), `1` with a named error on failure; distinct reasons for "no tag" (null, exit 0) vs "git absent" / bad `--repo` (exit 1). `--help` documents flags and any write location. | /peer-review |
| NFR-2 | Security (lens) | `--repo` validated against the §4 hostile-input checklist before use; `git` invoked with a fixed argument vector (`-C <path>` / `cwd`), never a shell string built from repo content; no raw traceback on any input; output bounded (NFR-4). Commit subjects are attacker-influenceable content: the AC-1.12 type match is a bounded pattern check against a fixed 10-token set, never a dynamic regex built from repo content, and every subject still flows through the render escape choke-point (AC-1.7). | /peer-review |
| NFR-3 (amended per C16) | Privacy / §6 | **Permitted subject parsing, exhaustively:** the leading Conventional-Commit type token from AC-1.12's fixed recognized set, plus the first line as an opaque display string. **Permanently forbidden:** any parsing, extraction, grouping, aggregation, counting or display touching author or committer identity — the author/committer name and email fields, handles, and **message trailers including `Co-Authored-By` and `Signed-off-by`** (this repo's own commits carry such trailers, so this is a live constraint, not a hypothetical one). No output field is keyed, sorted, grouped or filtered by a person, and no person-derived value is logged. Derivation 3 parses subjects for *work type*, never for *who* (constitution §6). | /peer-review + a test asserting no author/trailer field reaches any output |
| NFR-4 (amended per C9) | Performance / reliability | On a repo with 10k commits since the last tag, the command returns within 2s on a mid-range laptop; the rendered/JSON subject list is bounded to the most-recent **50 commits (N=50, fixed)**, with an explicit visible disclosure when the bound is active, while the **total count is always exact**. Handles an empty repo (no commits), a tagless repo, and a tag with zero commits since it without error. | /demo-day |
| NFR-5 | Reproducibility (§1 P3) | For a fixed repo `HEAD` and fixed `as_of`, output is byte-identical across runs; no wall-clock or ambient read anywhere in the derivation path — days-since-tag and branch ages are `as_of`-relative (A4); the work-type breakdown's order is fixed and declared (AC-4.11), so two runs are visually comparable, not merely byte-stable. | /peer-review + increment test |
| NFR-6 | Library (lens) | Zero new runtime pip dependencies (git is a subprocess, not a package dep); any new public export is minimal and additive — no breaking change to existing `build/query/render/diff/verify/serve` exports; error behavior documented. | /peer-review |
| NFR-7 (amended per C6/C10/C15, strengthened per C23) | UX / Accessibility (lens) | **Live this cycle (C2).** Single `<h1>` with an `<h2>` per section (AC-4.13); WCAG 2.1 AA contrast (4.5:1 text, 3:1 graphics — including every work-type segment, its hairline separators and the per-branch age bar against their backgrounds); any interactive element keyboard-operable; honest-null distinct by non-color cue; no information carried by color or bar length alone (AC-4.11, AC-4.12). **Named markup mechanisms, not outcome claims (C23):** the branch listing is a real `<table>` with `<th scope="col">` and a `<caption>`; the commit listing carries explicit per-field labels (`<dl>` pairs or visually-hidden `<span>`s); the provenance grid keeps programmatic field/value pairing (AC-4.6). Reuses `render.py`'s shipped CSS vocabulary — `.metric-card`/`.metric-card--null`, `.null-value`, `.metric-bar`, `.confidence-*`, the heading/typographic scale and palette — as the checked reference for "one product" (AC-4.7). At **375px viewport width**: no horizontal page scroll; the commit and branch listings wrap or scroll within their own `.table-wrap`-style container rather than overflowing the page — verified via `innerWidth`/`scrollWidth`/`clientWidth` at `/demo-day`, per this project's "measure, don't eyeball" technique. | /look-and-feel + /demo-day |
| NFR-8 | Observability | The output carries a lightweight provenance block: `as_of`, `insights_version`, the resolved tag (or null+reason), `shallow` flag, git-availability, the `source: git-interim` marker (AC-1.9/A1), and every active bound disclosure — so a reader can tell *why* a value is what it is and *which source* produced it. This block must render on the HTML surface, not only exist in JSON — see AC-4.6. | /peer-review |

## 6. Out of Scope

- **DORA / flow / lead-time / MTTR metrics** — deferred (backlog I3); require graph G1/G2 or a `TrackerPort`, which this feature must not depend on. Naive git-derived DORA would be exactly the "second derivation of the same truth" ADR-0/ADR-2 forbid.
- **The per-day commit-activity strip — cut 2026-08-11 (C17), named follow-up feature.** Not dropped for lack of time: it is the only element with its own bounding rule, its own §6 fence and its own NFR-7 conflict, it appears in neither §1's Goal nor its success signal, and it accounted for six of eleven second-pass design findings including all three hardest. Cutting it costs US-2's standalone proof — A2's stated justification — nothing. **Four costs it must pay when picked up, recorded here so the follow-up inherits the analysis instead of re-deriving it:** (1) its window must be anchored `max(T, as_of − Nd) … as_of`, not to `as_of` alone, or a week-old tag yields a strip that is structurally empty by construction; (2) 90 daily bars do not fit — 375px minus `body{margin:2rem}` leaves 311px of content, i.e. **3.46px per bar**, while a legible 4px bar with a 1px gap needs ≈513px; **60 days is the largest daily window that fits (299px ≤ 311px)** and is a *smaller window in the same unit*, not the second time unit rejected below; (3) it needs a non-tooltip text alternative — a `<title>` per bar is 90 hover-only targets, failing keyboard and touch; (4) its "empty bin" needs a token passing NFR-7's 3:1, since the obvious `#e2e2e2` on `#fff` measures **1.30:1**. All four figures independently re-verified 2026-08-11.
- **Weekly/monthly bucketing of the activity strip above a span threshold** — considered and rejected (C12) before the strip itself was cut: a second time unit means two shapes, two disclosures and two tests for one figure. Recorded for the follow-up, which should prefer a smaller daily window over a second unit.
- **Inferring a work type from anything other than the leading Conventional-Commit token** — no keyword heuristics on subject text, no file-path-based classification, no LLM. A commit without a recognized token is `unclassified` or the whole breakdown nulls (AC-1.12); guessing is the exact dishonesty this project forbids.
- **A configurable recognized-type set, a configurable threshold, or a flag to force the breakdown to render below 20%** — built-in and documented; configurability has no requester, and an escape hatch to show a misleading distribution is the bug re-exposed as a feature.
- **A pluggable `TrackerPort` (GitHub Issues / Jira / Linear, null-adapter default)** — the larger three-board concept; separate, larger follow-up.
- **Remote-tracking branches (`refs/remotes/*`)** — this cycle reads local refs only; remotes change the promise (what the origin has vs. this clone) and need their own definition.
- **"Unmerged" branch classification** — "unmerged relative to what base?" is undefined for a generic repo with no guaranteed `main`; deferred until a base-branch rule is decided. (C4: PO-proposed default, accepted on the user's behalf rather than put to them directly — flagged in the report-back.)
- **Person / developer metrics, and any per-committer view of the new derivations** — never (constitution §6, NFR-3); permanently out, not deferred. The work-type mix answers "what kind of work landed", never "who did it".
- **Threshold / pass-fail judgment on any of these numbers** — Insights measures; `aspark-ci` enforces (§3 off-limits). No "you haven't released in N days" warning.
- **Resolving the strategic fork "family-scoped vs standalone"** (backlog I9, open question 1) — not decided here; this feature merely *leans* standalone and names that as risk A6.
- **Snapshot-history / time-series trending of these git figures** — this is a single point-in-time view; trending is a separate feature.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-10 | New `Fact` feeding the graph-coupled `Snapshot`, or a separate standalone surface? | **Separate standalone surface.** `build_snapshot` requires `port.read_graph` (raises `GraphNotBuiltError` with no graph), so folding git-facts into the Snapshot makes them unreachable in exactly the no-graph case this feature exists for (US-2). A separate command also keeps the ADR-0/ADR-2 boundary structurally visible. Recorded as A5; seam naming left to `/sprint-plan`. |
| C2 | 2026-08-10 | Does the feature emit only JSON, or also HTML? | **RESOLVED — ruled "JSON + HTML in one cycle,"** overriding the PO's recommended smaller JSON-only slice. US-4 re-prioritized Must. NFR-7 live this cycle. |
| C3 | 2026-08-10 | "Most recent tag" — topology-nearest vs newest-by-date? | **RESOLVED — "topology-nearest"** (`git describe` semantics), matching the PO's default (A3). Any tag string counts; no-tag → honest null (AC-1.2). |
| C4 | 2026-08-10 | Branches: local-only vs include remotes; is "unmerged" classification in scope? | **RESOLVED by default-accept, not a direct user ruling.** Local-only, no "unmerged" classification (§6), on the PO's reasoning (no guaranteed base branch). Lower-stakes Should-story detail — flagged for the user rather than silently proceeded past. |
| C5 | 2026-08-10 | Is the git-native read authorized under the constitution, and does it yield to the graph once G1/G2 ship? | **RESOLVED — "yes, as a time-boxed fallback."** Grounded in BACKLOG.md §4's "Eigener Git-Parser" row and the I3 `flow-metrics` entry — this activates the pre-anticipated ADR-2 fallback, not a new exception. Made enforceable via AC-1.9/NFR-8's `source: git-interim` marker. See A1. |
| C6 | 2026-08-10 | **§8 finding 1 (Major)** — "reads as one product" was unenforceable prose; no AC named the shipped report's actual visual vocabulary. | Folded into **AC-4.2** (null shape is `.metric-card--null` + `.null-value`), new **AC-4.7**, and an NFR-7 clause. Later reconciled by C15 where the layout replaces tables. |
| C7 | 2026-08-10 | **§8 finding 2 (Major)** — AC-4.5 pointed at "the existing report's Provenance section," a broken cross-reference on a standalone page; marker prominence and neutral-vs-alarm treatment undefined. | **AC-4.5 rewritten**: own provenance section holds the marker; also legible near the top unscrolled as a labelled line; neutral provenance treatment distinct from `.stale-cue`, by label token never hue alone. |
| C8 | 2026-08-10 | **§8 finding 3 (Blocker)** — the shallow-clone disclosure and provenance block were required in JSON but never required to render on the HTML. | New **AC-4.6**: every report renders its own provenance section with all trust-bearing fields, including every active bound disclosure. NFR-8 cross-references it. |
| C9 | 2026-08-10 | **§8 finding 4a (Major)** — NFR-4 permitted truncating the commit list without stating N. | **NFR-4 amended**: N fixed at **50**, with a visible truncation disclosure when exceeded; total count stays exact. |
| C10 | 2026-08-10 | **§8 finding 8 (Major)** — NFR-7 had no responsive/viewport bar despite wide tabular surfaces. | **NFR-7 amended**: at 375px, no horizontal page scroll; listings/strip wrap or scroll in their own container; measured via `innerWidth`/`scrollWidth`/`clientWidth` at `/demo-day`. |
| C11 | 2026-08-10 | **New derivation 1** — days since the resolved tag. Is the no-tag state a second null, or simply absent? | **New AC-1.10.** `as_of` − tag commit date, whole days, never `now()`. No tag → the figure is **absent entirely**, not a second null: AC-1.2 already explains the whole since-release frame, and two nulls for one cause is the "two competing explanations" failure `measurement-honesty` AC-1.4 settled. An unreadable tag date is its own null+reason. §1's Goal/success signal updated: a count without an elapsed span is not an answer. |
| C12 | 2026-08-10 | **New derivation 2** — per-day commit bins. What bounds the strip when the tag is two years old (700+ bars)? | **New AC-1.11**, bound resolved rather than deferred: a fixed **90-day** window ending at `as_of`, one bin per UTC calendar day, zero-commit days present as explicit zero bins (never omitted). Above 90 days, an explicit disclosure states the window covers 90 of D days and M of N commits; the AC-1.1 total stays exact. Weekly/monthly bucketing was considered and **rejected** (§6) — a second time unit doubles the shapes, disclosures and tests for one figure. |
| C13 | 2026-08-10 | **New derivation 3** — Conventional-Commit work-type mix. What is the recognized set, and what happens in a repo that doesn't use the convention? | **New AC-1.12.** Recognized set stated explicitly (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style`; optional `(scope)`/`!`; case-insensitive, normalized). Honest degradation is an AC, not a footnote: **below 20% classifiable the whole breakdown is `null` + reason with no distribution rendered** (AC-4.11); at or above it, the `unclassified` remainder is always shown at equal visual weight, never redistributed. No inference from any other signal (§6) — the same class of guarantee as `measurement-honesty`'s null-on-absent-evidence rule. |
| C14 | 2026-08-10 | **Layout reorganization** — approved preview: answer sentence, stat-card row before tables, scannable commit list, per-branch age bar, compact provenance grid. | **New AC-4.8** (one-line plain-language answer sentence under the `<h1>`, stating null/absent figures in words rather than placeholders), **AC-4.9** (stat-card row before any list/table), **AC-4.10** (activity strip + scannable commit list), **AC-4.11** (work-type breakdown rendering incl. its null case). No new data — presentation only, over AC-1.1/1.10/1.11/1.12 and US-3. **Partially superseded by C17:** the activity strip and AC-1.11 were cut on 2026-08-11; AC-4.10 retains only its scannable-commit-list clause. This row is left as the historical record of what was approved that day, not as a live requirement. |
| C15 | 2026-08-10 | The layout replaces two tables (commit list → list; provenance → grid), but AC-4.6/AC-4.7 were written against the existing report's `<table>`/`<th scope="col">` shapes. Does the accessibility bar survive? | **Reconciled, not weakened.** AC-4.6 now requires the provenance grid to keep **programmatic field/value pairing** (`<dl>`/`<dt>`/`<dd>` or row headers) rather than visual adjacency; AC-4.7 clarifies the reused vocabulary is the card/typographic scale and palette, not `<table>` markup specifically; new **AC-4.12** restates the listing guarantees for the new shape — semantic list/table with a programmatic name, per-item field structure, and the branch age bar carrying its numeric value as text. NFR-7 updated to cover bar-length and color as non-exclusive channels. |
| C16 | 2026-08-10 | **Contradiction** — NFR-3 said subjects are "never parsed," but derivation 3 parses them. | **NFR-3 amended** to state permitted parsing exhaustively (the leading type token from AC-1.12's fixed set, plus the first line as an opaque display string) and to forbid permanently any parsing/extraction/grouping/aggregation touching identity — author/committer name and email, handles, **and message trailers including `Co-Authored-By`/`Signed-off-by`**, which this repo's own commits carry. Parses for *work type*, never for *who*. |
| C17 | 2026-08-11 | The second `/look-and-feel` pass returned 1 Blocker + 7 Major + 3 Minor, six of them against the activity strip, and both the Designer and the PO independently recommended a scope cut. Cut the strip, cut more, or amend everything? | **Ruled: cut the activity strip only.** AC-1.11 withdrawn (ID retired, not renumbered); AC-4.10's strip clauses (a)–(c) withdrawn; strip moved to §6 as a named follow-up carrying its four re-derivation costs. The work-type breakdown is **kept**, with C19's legend restatement. The PO's further recommendation to cut the breakdown as well rested partly on a size argument that did not survive checking: the spec proper (§1–§7 + gate) measured **203 lines**, inside the template's ~250 budget — §8's two-pass review record was 690 of the file's 892 lines. §8 condensed to its findings, verdicts and routing on the same ruling. |
| C18 | 2026-08-11 | **§8 finding 9 (Blocker)** — on a tagless repo, the feature's own headline scenario, the breakdown opens "given commits since `T`" while its ratio needs no `T`, so the page could render a real distribution beside AC-1.2's null saying that frame cannot be established. | **AC-1.12(c)/(d) added.** No tag → the breakdown is **absent entirely**, never computed over all commits in the repo. Zero commits since the tag → the classifiable ratio is 0/0, undefined → likewise absent, neither `null` nor `0%`. Every number true while the frame is invented is a §6 violation, not an ambiguity. |
| C19 | 2026-08-11 | **§8 finding 14 (Major)** — AC-4.11's per-segment inline labels are unrenderable: a 1-of-50 segment is ~6px, the label `refactor` needs ~55px. | **AC-4.11 rewritten onto the shipped precedent.** `render.py`'s `.confidence-mix` already solves this the opposite way: single-fill bar, hairline separators, adjacent text legend. AC-4.7 additionally now names *which* reference shapes exist (`.metric-bar` for the age bar, `.confidence-*` for the breakdown) and which do **not** (no badge precedent) — answering the Designer's own question about whether "reuse the vocabulary" means anything for shapes the reference lacks. |
| C20 | 2026-08-11 | **§8 finding 10 (Major)** — AC-4.8's sentence and AC-4.9's card row are undefined in three degenerate states, and AC-4.8 gave a second explanation for the no-tag cause AC-1.10(a) already settled. | **AC-4.8 and AC-4.9 amended.** Three states stated in words: no tag (single reason, consistent with AC-1.10(a)); zero commits since tag (a **true zero**, stated as such, never a null card); zero branches (stated, not omitted). AC-4.9 distinguishes **absent** (no card at all) from **null** (AC-4.2 dashed card) from **true zero** (real value card showing `0`) — asserting "we tried and could not measure" where the truth is "this figure has no referent here" is the null-card misuse first-pass finding 5 warned against. |
| C21 | 2026-08-11 | **§8 finding 11 (Major)** — the shallow-clone caveat is reachable (AC-4.6) but sits blocks below AC-4.8's unqualified exactness claim, so a shallow-clone reader can still form the wrong belief. | **AC-4.8 amended:** given `shallow: true`, the answer sentence carries the qualifier inline ("at least 8 commits landed since…"). Reachability was never the gap after the first pass; adjacency was. |
| C22 | 2026-08-11 | **§8 finding 17 (Minor)** — nothing specifies the breakdown's segment order, so two runs of one repo differ visually despite byte-stable output. | **AC-4.11:** fixed declared order — AC-1.12's recognized-set order with `unclassified` last, zero-count types omitted from bar and legend. NFR-5 extended: byte-stability alone does not make two runs *visually* comparable. |
| C23 | 2026-08-11 | **§8 finding 16 (Major)** — C15's claim that "no accessibility guarantee from the previous table-based wording is dropped" does not survive re-derivation: NFR-7 carried no `table`/`th`/`scope`/`caption` token, and AC-4.12 replaced the mechanism with an outcome sentence that is not falsifiable at review. | **Conceded — the amendment was genuinely weaker than the finding asked.** AC-4.12 rewritten with named mechanisms: the **branch listing stays a real `<table>`** with `<th scope="col">` + `<caption>` (the approved layout changed the age *cell* to a bar, never the table to a list, so nothing the user approved is reverted); the commit listing keeps the scannable shape but must carry explicit per-field labels (`<dl>` pairs or visually-hidden `<span>`s); plus a programmatic name and the age bar's numeric text. NFR-7 restated to name the same mechanisms. The residual divergence from constitution §4's *mechanism*-worded bar is recorded as **A8, open** — so the gate's "conflicts recorded" box is honestly ticked rather than ticked past an unnamed tension. |
| C24 | 2026-08-11 | **§8 finding 15 (Major)** — the page had eight blocks with no defined section set and no defined order, and three separately claimed to be "first". | **New AC-4.13:** the block order is enumerated and checkable by byte offset in `outerHTML` (`<h1>` → interim marker → answer sentence → stat-card row → Work types → Commits → Branches → Provenance), every block after the card row carries an `<h2>`, and a block whose content is absent omits its `<h2>` with it rather than leaving an empty labelled section. Seven blocks after the strip cut, not eight. |

## 8. Design Review

<!-- Filled by /look-and-feel (two passes: 2026-08-10, 2026-08-11).
     CONDENSED 2026-08-11 on the user's instruction: the findings, their verdicts and their
     routing are preserved in full; the long per-finding derivations were removed once each
     finding had been ruled on. The quantitative claims that carried the second pass were
     independently re-verified before condensing (see "Verified numbers" below), so nothing
     load-bearing rests on a derivation that is no longer in the file. -->

### Scope ruling that supersedes part of this review

The user ruled on 2026-08-11, after the second pass: **the activity strip is cut** from this
feature and becomes a named follow-up (§6). It carried its own bounding rule, its own §6 fence
and its own NFR-7 conflict, appeared in neither §1's Goal nor its success signal, and accounted
for six of the eleven second-pass findings including all three hardest. Cutting it costs US-2's
standalone proof — A2's stated justification — nothing. The **work-type breakdown is kept**, with
finding 14's legend restatement. Findings that died with the strip are marked *moot* below rather
than deleted, so the follow-up feature inherits the analysis instead of re-deriving it.

### Verified numbers (re-checked independently, not taken on the review's word)

| Claim | Verified |
|---|---|
| Empty-bar token `#e2e2e2` on `#fff` | **1.30:1** — below NFR-7's own 3:1 bar |
| 90 bars in 311px content (375px − `body{margin:2rem}`) | **3.46px** per bar incl. gap |
| 60 bars at 4px + 1px gap | **299px** — fits 311px |

These are why the strip was cut rather than patched: it was unbuildable against the spec's own
375px and contrast bars, not merely awkward.

### First-pass findings (2026-08-10) with second-pass verdicts

| # | Severity | Subject | Verdict |
|---|---|---|---|
| 1 | Major | "Reads as one product" unenforceable prose | **Resolved** — 4 of 5 named elements appear literally in AC-4.2/4.7/NFR-7; the 5th (`.table-wrap`/`<th scope="col">`) was withdrawn by C15 and is re-raised on its own merits as finding 16 |
| 2 | Major | AC-4.5's broken "existing report's Provenance section" anchor | **Resolved** — all three fix parts near-verbatim |
| 3 | **Blocker** | Shallow disclosure + provenance required in JSON only | **Resolved as written; adjacency re-opened** by AC-4.8 (→ finding 11). Reachability fixed, so the Blocker is closed |
| 4a | Major | Commit-list bound N undefined | **Resolved** — N=50 fixed in NFR-4 |
| 4b | Major | Truncation note shapeless | Unchanged — **safe for `/increment`** |
| 5 | Major | Zero-commits-since-tag "clean" state undesigned | **Re-opened, re-routed out of `/increment`** — entangled with AC-1.12's 0/0 and AC-4.11's null card (→ findings 9/10) |
| 6 | Major | No `<h2>` per section | **Resolved as text, superseded** — written for 3 blocks, page grew to 8 (→ finding 15) |
| 7 | Major | Table header semantics unspecified | **Partially resolved, weaker than asked; routing void** (→ finding 16) |
| 8 | Major | No responsive/375px bar | **Resolved** as a page-level bar |

### Second-pass findings (2026-08-11)

| # | Severity | Subject | Status after the scope ruling |
|---|---|---|---|
| 9 | **Blocker** | On a tagless repo — the feature's own headline scenario — the strip and breakdown open "given commits since `T`" but their window/ratio is defined without `T`, so the page renders a real distribution beside AC-1.2's null saying that frame cannot be established | **Partially survives.** The strip half is moot; the breakdown must be **absent** on a tagless repo, never computed over all commits → **spec amendment** |
| 10 | Major | AC-4.8's sentence and AC-4.9's card row undefined in the degenerate states (no tag, zero commits, zero branches); AC-4.8 contradicts AC-1.10(a) by giving a second explanation for one cause | **Survives** → spec amendment |
| 11 | Major | Shallow caveat reachable but no longer adjacent to the exactness claim it qualifies | **Survives** — qualifier moves into AC-4.8's sentence → spec amendment |
| 12 | Major | AC-4.10(b)'s text alternative permits a hover-only mechanism (no keyboard, no touch) | **Moot** — strip cut; recorded for the follow-up |
| 13 | Major | Strip's window anchored to `as_of` not `T`; 90 bars do not fit 375px; empty-bar token fails contrast | **Moot** — strip cut; the three costs are recorded in §6 so the follow-up inherits them |
| 14 | Major | AC-4.11's per-segment inline labels unrenderable at any width (a 1-of-50 segment is ~6px; `refactor` needs ~55px) | **Survives** — restate on `render.py`'s shipped `.confidence-bar` pattern: one fill, hairline separators, adjacent legend in fixed order → spec amendment |
| 15 | Major | Eight blocks with no defined section set and no defined order; three separately claim to be "first" (**AC-4.5b, AC-4.8, AC-4.9**) | **Survives, reduced to 7 blocks** → spec amendment (order) + `/increment` (programmatic name). All three claimants reconciled: AC-4.5b "near the top", AC-4.8 "after the interim marker", AC-4.9 "before any list or table"; AC-4.13 is the byte-offset-checkable rule that governs |
| 16 | Major | AC-4.12 states an outcome with no named mechanism; C15's "no guarantee dropped" does not survive re-derivation — NFR-7 carries no `table`/`th`/`scope`/`caption` token | **Survives** → spec amendment, incl. recording the constitution §4 tension |
| 17 | Minor | Breakdown segment order unspecified — two runs of one repo differ visually despite byte-stable output | **Survives** → spec amendment |
| 18 | Minor | Commit-row badge undefined for an unclassified commit | **Survives** — **safe for `/increment`** |
| 19 | Minor | `<html lang>`, viewport meta and descriptive `<title>` unnamed (a real shipped `snapshot-report` bug) | **Survives** — **safe for `/increment`** |

### Accessibility notes

- **Contrast, recomputed from `render.py` source** (Mode A — no `getComputedStyle` available):
  `.stale-cue` `#7a4a00` on `#fff6e5` ≈ **6.97:1**, its border on `#fff` ≈ **7.48:1**;
  `.null-value`/`.metric-value--null` `#444` on `#fff` ≈ **9.74:1**. Reusing the shipped palette
  ships the primary text pairs contrast-safe with margin.
- **Any new color** this feature introduces beyond that palette — the neutral `git-interim`
  marker, the breakdown's segment fill and separators, the per-branch age bar — is **unverified**
  and becomes a `/demo-day` `getComputedStyle` measurement under NFR-7.
- **AC-4.7's open question, answered:** `render.py` *does* contain a magnitude bar
  (`.metric-bar`/`.metric-bar-fill`) and a labelled stacked-proportion bar
  (`.confidence-mix`/`.confidence-bar`/`.confidence-seg`/`.confidence-legend`) — the latter is a
  near-exact precedent for the work-type breakdown and solves AC-4.11's labelling problem the
  opposite way to how AC-4.11 specified it. It contains **no** badge precedent. Naming both the
  shapes that exist and the one that doesn't is what makes AC-4.7 enforceable rather than vacuous.
- **Keyboard / focus / motion — N/A and correctly so**, re-checked against the new ACs: AC-4.1
  forbids executable JS and no AC smuggles in interactivity (no sortable table, no filter, no
  expand/collapse). Matches the shipped report's measured zero-interactive-element state.
- **Touch targets — N/A**: the ~44px bar applies to controls; this page has none.

### Design risks & required changes (routing)

- **Route to `/story-time` before the gate closes — spec amendments:** finding 9 (breakdown's
  tagless behavior), finding 16 (named accessibility mechanism + record the constitution §4
  tension), finding 14 (restate AC-4.11 on the shipped legend pattern; name the reference shapes
  in AC-4.7), finding 10 (the three degenerate states), finding 11 (shallow qualifier in the
  sentence), finding 15 (block order and section list), finding 17 (segment order).
- **Safe for `/increment` inside existing AC/NFR wording:** finding 4b (the "showing 50 of N"
  note), finding 18 (badge absent rather than `unclassified` on every row), finding 19 (`lang`,
  viewport meta, descriptive `<title>`), and the programmatic-name half of finding 15.
- **Deferred to `/demo-day` measurement:** every new color pair under NFR-7 via
  `getComputedStyle`; the 375px behavior of the commit list, branch list and provenance grid via
  `innerWidth`/`scrollWidth`/`clientWidth`; the presence of the viewport meta; and the rendered
  block order by byte offset in `outerHTML`.
- **Moot after the scope ruling:** findings 12 and 13, and the strip half of findings 9 and 15 —
  preserved above so the follow-up feature inherits the analysis.
- **No finding reopens a settled scope cut.** Nothing above asks for remotes, "unmerged"
  classification, DORA/flow metrics, personas, a `TrackerPort`, interactivity, JS, a configurable
  threshold, or keyword-based type inference (§6, A6, AC-4.1 intact).

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C1–C24 all resolved
- [x] Open questions are resolved or explicitly accepted as risk — A1–A5, A7 resolved/accepted; A6 and A8 named risks (A8 is open for the user's ruling at approval, but does not block: the divergence is specified, not undefined)
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution respected, or conflicts recorded as open questions — A1/C5 resolved (ADR-2 fallback, enforced via AC-1.9); C16 reconciles NFR-3 against derivation 3's subject parsing; **A8/C23 records the one live divergence** — constitution §4's accessibility bar is worded as a *mechanism* (`<table>`/`<th>`, not `<div>` grids) and the approved layout changes that mechanism for two of four surfaces while preserving the guarantee. Recorded, not absorbed silently
- [x] Design review done for UI-facing features (or marked N/A with reason) — **two passes run** (§8, 2026-08-10 and 2026-08-11). Pass 1's Blocker + four Majors folded in as C6–C10; pass 2 re-derived each of those verdicts adversarially rather than accepting them, and its own Blocker + Majors are folded in as C17–C24. Six findings died with the activity strip (cut per C17, preserved in §6 with its four re-derivation costs); the rest are amended into AC-1.12, AC-4.7–AC-4.13 and NFR-4/5/7. Four findings remain routed to `/increment` and four measurements to `/demo-day`, both listed in §8's routing block.
- [x] Status set to `approved` by the user (2026-08-11), with A8 ruled "accept the divergence as specified"
