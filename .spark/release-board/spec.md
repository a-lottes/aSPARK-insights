# Spec: release-board

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-19 |
| **Ticket** | none |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `approved` (2026-08-19) — A1/A2/A4 ruled by the user (§7 C4-C6); A3 stays open but is explicitly non-blocking (no story in this spec depends on it). Gate re-verified this pass, not just re-checked; see the SPEC GATE below. Approved by the user in this conversation; hands off to `/sprint-plan`.
- **Summary:** A scriptable, honesty-bounded map from every actually-tagged git release **and the open window since the latest tag (a distinguishable pseudo-release, per the user's explicit reversal of the PO's own recommendation — A4/C6)** to the `.spark/<feature>/` directories (and unattributed commits) in range, plus each artifact's own header-table `Status`/`Date`. Still deliberately not the full "why" (Clarifications/ADR prose, A3) and still deliberately JSON-only (A2 resolved informationally, no HTML story this cycle).
- **Open:** `1 deferred, non-blocking` — A3 (how far "why" extraction goes) stays open in §3 but gates nothing in this spec (§6 already excludes any "why" story).
- **Binding ruling:** §4 User Stories for what's committed this cycle; §3 for what isn't yet; §7 for what changed and why.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at the next `/peer-review` and proceed.

## 1. Problem & Goal

- **Problem:** Reconstructing "what shipped in which release, and what was decided along the way"
  today means opening 5-6 files per feature directory across N directories, plus cross-referencing
  raw `git log`/`git tag` by hand. This is not hypothetical: **producing this very spec required
  it** — reading the constitution, `BACKLOG.md`, six features' `spec.md`/`release.md`/`review.md`/
  `qa.md`, `.git/refs/tags`, `.git/packed-refs`, `.git/logs/HEAD`, and `src/aspark_insights/
  gitboard/gitread.py`, across dozens of tool calls, to answer "what actually shipped, in what
  order, and why." That cost lands on the sole maintainer today, every time a future `/story-time`
  or `/go-live` needs project history, and would land harder on any future second contributor with
  none of this context in their head. The workaround (reading files directly) works, but scales
  linearly with feature count and has already produced its own `CLAUDE.md` process notes to
  compensate.
- **Goal:** A small, honest slice of that answer: for every release — each actually-tagged one,
  **and, per the user's explicit ruling (A4/C6, reversing the PO's own recommendation), the open
  window of commits since the latest tag as a distinguishable pseudo-release** — which
  `.spark/<feature>/` directories (and which unattributed commits) landed in it, and each of those
  features' own artifact status, extracted only where it can be extracted with confidence,
  `null`-with-reason everywhere else. The pseudo-release's own git-derived figures are never
  recomputed independently: they are `gitboard.board.build_board()`'s own result, reused verbatim
  (AC-1.8) — the same "shared core, two thin adapters" discipline already used for CLI↔MCP parity
  and `render.py`'s style reuse, extended here rather than re-invented. Explicitly **not** the full
  "why" (Clarifications, Architecture Decisions) or any rendered page this cycle (§6) — the latter
  is now a resolved *shape* (A2: an index page with drill-down) pending only *timing*, not an open
  design question.
- **Success signal:** Run against *this* repo and get, byte-verifiably: `v0.3.0` listing **three**
  members — `traceability-metrics`, `public-repo-polish`, and `mcp-server` — hand-traced against
  this repo's own `.git/logs/HEAD` reflog (corrected from this spec's original draft, which
  undercounted at two; see C7). `v0.5.0` lists exactly `measurement-honesty`. A commit touching no
  `.spark/<feature>/` directory at all — this repo's own `26e7f95` and `3382942d` are both real,
  confirmed examples — appears in an explicit `unattributed` bucket, never dropped and never
  attributed by matching a commit's message text against a directory name (`26e7f95`'s subject
  reads "snapshot-report scorecard redesign" while touching zero files under
  `.spark/snapshot-report/` — a deliberately adversarial real example). A trailing pseudo-release
  entry (`tag: null`) for the window since `v0.5.0` reports a commit count and elapsed days that
  match `insights board`'s own live answer exactly, because AC-1.8 requires it to be
  `build_board()`'s literal output — concretely, **6 commits since `v0.5.0`**
  (`7cd03af`, `26e7f95`, `2b4c105`, `8b4f9ff`, `99e4aae`, `4743b41`), independently re-counted from
  `.git/logs/HEAD` for this pass rather than taken on the coordinator's word alone.
- **Why now — argued honestly, not assumed:** If this is never built, nothing breaks; the
  information already exists in git and Markdown, and the workaround above is merely slow, not
  wrong. The case *for* building it rests entirely on the reconstruction cost demonstrated above,
  which is real but currently tolerable at 7 feature directories. Two things weighed against
  building it *now* remain on the record even though the user chose to proceed: (1) this idea had
  **no precedent anywhere in `BACKLOG.md`**'s I1-I9 roadmap before this ruling — unlike
  `git-native-mid-cycle-board`, which activated an already-anticipated ADR-2 fallback, this was a
  genuine scope excursion the PO flagged rather than confirmed, now authorized by the user (A1/C4);
  (2) the most recent cycle, `git-native-mid-cycle-board`, still has a **fully gated but unpublished
  release sitting in `.spark/git-native-mid-cycle-board/release.md`** (`v0.6.0`/`v0.7.0` prepared,
  not pushed) — the team has unfinished release-*management* work in flight before it has
  release-*visualization* work. The user was presented this sequencing tension and chose to
  continue this spec now rather than pause for the pending publish — recorded here, not treated as
  scope, and not affecting anything below.

## 2. Target Users

- **The maintainer, reconstructing past decisions (concrete: Andreas)** — the same audience every
  prior Insights surface names, in the same honest, non-"everyone" framing. Concretely: the person
  who, next cycle, needs "what shipped between `v0.4.0` and `v0.5.0`, and why" without repeating
  this spec's own multi-file reconstruction.
- **A future second maintainer onboarding (hypothesized, not yet observed)** — named as a
  hypothesis, exactly as `git-native-mid-cycle-board`'s A2 named its own generic-repo audience,
  not inflated into a validated persona.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | **Structural boundary — does this belong in `aspark-insights` at all?** No `BACKLOG.md` entry (I1-I9) anticipates this feature, unlike every prior Insights feature. | **RESOLVED 2026-08-19** — the user ruled "yes, in `aspark-insights`," matching the PO's working-draft assumption; no story content changed as a result. See C4. |
| A2 | **Output surface shape.** One HTML page per release with prev/next links, vs. one index page listing all releases with drill-down. | **RESOLVED 2026-08-19, informationally** — "an index page with drill-down." No HTML story ships this cycle (§6 unchanged on that point); this only shapes a *future* `/story-time` pass that proposes one. See C5. |
| A3 | **How far does "why" extraction go?** Real, observed heading/section drift within this project's own 7 cycles (e.g. `git-native-mid-cycle-board/release.md` nests "Version"/"Rollback Path" as `###` subsections where every earlier `release.md` gives them top-level `##` headings; `foundation/qa.md`'s verdict heading carries a different number and extra trailing text than every other `qa.md`) makes a full section-extract fragile and a stable file pointer far less useful. | **Still OPEN — deliberately not resolved this pass, and not blocking.** No story in this spec depends on it: §6 already excludes any "why"-extraction story regardless of how A3 resolves. Revisit only when a future spec proposes one. |
| A4 | **Overlap with `insights board`'s mandate.** `insights board` already answers "what's landed since the last tagged release" for the current, untagged window. The PO's own recommendation was to leave that window entirely to `insights board`, to avoid a second derivation of the same truth (ADR-0's spirit). | **RESOLVED 2026-08-19 — the user ruled the OPPOSITE of the PO's recommendation: "NO, the untagged window must also be included."** Re-scoped: US-1 gains AC-1.8 (mandatory reuse of `gitboard.board.build_board()`, never a second implementation), AC-1.9 (true-zero-vs-absent rule for the pseudo-release), AC-1.10 (the `tag: null` discriminator); US-3's AC-3.1 gains the pseudo-release's `previous_tag`/`next_tag` rule. §6's corresponding Out-of-Scope line is corrected, not silently dropped. See C6. |
| A5 | *(Accepted, not open.)* "Release" = an actual git tag object (`git tag --list`), not a version string in a commit message. `v0.6.0`/`v0.7.0` are therefore **not** real releases for this feature — they are absorbed into the pseudo-release entry instead (A4/C6), which is exactly why A4's reversal matters: without it, this repo's own six most recent commits would have been entirely invisible to release-board. |
| A6 | *(Accepted.)* A real release's commit range is `<previous-tag>..<this-tag>` in tag-topology order; the earliest tag's range is `<root-commit>..<earliest-tag>`; the pseudo-release's range is `<latest-tag>..HEAD` — the identical range `gitboard.board.build_board()` already uses internally for `commits`/`days_since_tag`/`work_types` (AC-1.8 requires reusing its result rather than recomputing this range's figures a second time). New enumeration code is still needed only for the *ordered list of all tags* — today's `gitread.py` resolves just the single nearest-to-`HEAD` tag — but the same subprocess discipline (fixed argument vector, no shell string, no identity fields) carries over directly; no second git parser is invented (ADR-2). |
| A7 | *(Accepted.)* A `.spark/<feature-name>/` directory is "in" a release (real or pseudo) if `git log <range> -- .spark/<feature-name>/` returns at least one commit — a bounded, per-directory `git log` call, not a second implementation of `git diff`/`blame`. Commits touching no `.spark/<feature>/` path land in that release's `unattributed` list. Attribution is decided **only** by changed paths, never by matching a commit's subject text against a directory name (AC-1.3's `26e7f95` counter-example is exactly why this must be stated explicitly, not left implicit). |
| A8 | *(Named risk, not blocking.)* One release **spanning multiple feature directories is this repo's real history, not padding**: `v0.3.0` spans **three** (A9/C7 below), not the two originally assumed. Any implementation that assumes "one release, one feature" will be wrong on this repo's very first release it's tested against. |
| A9 | *(New, accepted — found during this pass's re-verification, C7.)* A feature's own trailing "docs: record `<feature>`'s release report" commit routinely lands **inside the next release's (or the pseudo-release's) range**, not the range its own feature shipped under — confirmed at nearly every boundary in this repo's real history (`foundation`→`v0.2.0`, `traceability-metrics`→`v0.3.0`, `mcp-server`→`v0.4.0`, `snapshot-report`→`v0.5.0`, `measurement-honesty`→the pseudo-release, all hand-traced via `.git/logs/HEAD`). Membership is decided purely by "did any commit in this range touch this path" (A7); it never distinguishes a feature's "main" shipping commit from an incidental later touch, because that distinction would require guessing intent from a commit's content — exactly what this feature must never do. The user-visible consequence (a feature reappearing as a minor member of the release after its own) is a real, honest, if initially surprising, fact, not a bug to filter out. |

## 4. User Stories

### US-1 (Must): Release-to-feature-directory membership, honest for unattributed commits, including the open window since the latest tag

> As the maintainer, I want every release — tagged or still open — to list which `.spark/<feature>/`
> directories (and which orphaned commits) had changes in its range, so I can see what shipped
> together, and what's landed but not yet tagged, without reconstructing either from `git log` by
> hand.

**Acceptance criteria:**

- [ ] AC-1.1 (amended per A4/C6): Given this repo's real tags, when I run the command, then the release list contains exactly one entry per tag returned by `git tag --list` (ordered by tag topology, oldest first), plus exactly one trailing pseudo-release entry for the window since the latest tag whenever at least one tag exists (AC-1.9 governs its zero-commit and no-tag-at-all cases). No real tag is ever silently omitted, and there is never more than one pseudo-release entry.
- [ ] AC-1.2 (corrected 2026-08-19, C7): Given release `v0.3.0` (range `v0.2.0..v0.3.0`), when I run the command, then its member list is exactly **three** directories: `traceability-metrics` (one trailing docs-bookkeeping commit, `6f987a15`, that lands just inside this range even though the feature itself shipped under `v0.2.0` — see A9), `public-repo-polish` (its whole no-version-bump cycle, `a3c03094`/`0e60deb9`), and `mcp-server` (the tagged commit, `378095e7`) — hand-verified against this repo's own `.git/logs/HEAD` reflog, not merely against each feature's own `release.md`.
- [ ] AC-1.3: Given a commit inside any release's range — including the pseudo-release's open range — that touches no `.spark/<feature>/` path, when I run the command, then it appears in that release's `unattributed` list (short hash, subject; this repo's own `3382942d`, "docs: fold mcp-server's shared-core-two-adapters pattern into CLAUDE.md", which touches only `CLAUDE.md`, is a real example), never dropped and never attached to a feature it didn't touch, and never attributed by matching the commit subject's text against a feature-directory name — this repo's own `26e7f95` ("snapshot-report scorecard redesign") touches zero files under `.spark/snapshot-report/` despite naming it in prose, which is exactly the trap this AC forbids (A7).
- [ ] AC-1.4: Given a repo with zero tags, when I run the command, then the release list is empty with an explicit reason ("repository has no tags") and exit code `0` — an honest empty state, not a failure. No pseudo-release entry appears either (AC-1.9).
- [ ] AC-1.5: Given `--repo` set to an empty string, a `../` traversal, an absolute path, a non-git directory, or a directory with a corrupt `.git`, when I run the command, then it exits `1` with a named error and never a raw traceback (constitution §6, hostile-input checklist).
- [ ] AC-1.6: Given any output this feature produces, when inspected, then it contains no author name, author email, or committer identity, and no field grouped by person (constitution §6).
- [ ] AC-1.7: Given a fixed `HEAD`/tag set and a fixed `as_of`, when I run the command twice, then stdout is byte-identical both times (`sort_keys=True` JSON, ADR-4 — no wall-clock read; NFR-7 states the pseudo-release's own "fixed" scope precisely).
- [ ] AC-1.8 (new per A4/C6): Given the pseudo-release entry, when its commit count, elapsed days, work-type breakdown and branch inventory are computed, then they are produced by calling `gitboard.board.build_board()` directly and carrying its result through unchanged — never a second, independent implementation of "commits since the latest tag" (ADR-0's spirit, mirroring how the real releases' ranges already reuse `gitboard.gitread`'s primitives per A6). Only the feature-directory membership and `unattributed` breakdown — logic `build_board()` itself never computes; its own docstring states it "never touches `.spark/`" — is computed by this feature, applied to the same `<latest-tag>..HEAD` range `build_board()` used internally to produce its `commits` figure.
- [ ] AC-1.9 (new per A4/C6): Given at least one tag exists and there are zero commits since the latest tag, when I run the command, then the pseudo-release entry is still present, with empty `members` and `unattributed` lists — a true, honest zero, mirroring `build_board()`'s own `commits: {"value": 0, "reason": null}` shape for the identical case — never omitted. Given the repository has no tags at all, when I run the command, then no pseudo-release entry appears either: the "since the latest tag" frame has no referent without a latest tag (AC-1.4 already covers the whole-empty-release-list case; this avoids a second, competing explanation for the same absence, matching the precedent `git-native-mid-cycle-board`'s own spec set for `days_since_tag` on a tagless repo).
- [ ] AC-1.10 (new per A4/C6): Given the release list, when inspected, then every entry carries a `tag` field: a real release's `tag` is its tag string; the pseudo-release's `tag` is `null`. This is the sole, unambiguous discriminator between a real and an in-progress release — nothing about list position or field presence is required to tell them apart.

### US-2 (Must): Per-artifact status disclosed only when confidently parseable

> As the maintainer, I want each feature's spec/plan/review/qa/release status pulled from that
> artifact's own header table, so I get an accurate at-a-glance status without re-reading five
> files per feature — and never a guessed one where the file can't be read confidently.

**Acceptance criteria:**

- [ ] AC-2.1: Given an artifact file (`spec.md`/`plan.md`/`review.md`/`qa.md`/`release.md`) whose header table contains a `| **Status** |` row — confirmed present in all 7 observed cycles' artifacts, including the oldest (`foundation`, 2026-07-29) — when I run the command, then that artifact's status is the value cell, extracted verbatim.
- [ ] AC-2.2: Given a feature directory missing one of the five artifact files (e.g. a feature not yet reviewed, no `review.md`), when I run the command, then that artifact's entry is `status: null` with reason `"file not found"` — never omitted from the output entirely, never inferred from a sibling artifact's status.
- [ ] AC-2.3: Given an artifact file that exists but whose header table can't be matched by the documented extraction rule (malformed table, missing `Status` row, unreadable encoding), when I run the command, then that artifact's status is `null` with a reason naming the specific parse failure — never a stale, cached, or guessed default.
- [ ] AC-2.4: Given any artifact file, when parsed, then only its header table (the first pipe-table block at the top of the file) is read for `Status`/`Date` — no other section of the free-form Markdown body is parsed this cycle, keeping the parsing surface exactly as bounded as A3 requires to ship now.

### US-3 (Should): Ordered release list with prev/next tag pointers, JSON only

> As the maintainer, I want the release list ordered with each entry's previous/next tag named, so
> that a future navigation UI (now informed by A2's index-with-drill-down resolution) has a stable
> contract to build on rather than re-deriving order itself.

**Acceptance criteria:**

- [ ] AC-3.1 (amended per A4/C6): Given two or more tags, when I run the command, then every **real** release entry carries `previous_tag`/`next_tag` naming only real tags (`null` at either end of the real-tag sequence). Given a pseudo-release entry is present (AC-1.9), when inspected, then its `previous_tag` is the latest real tag and its `next_tag` is always `null` (it is never superseded, since it isn't tagged yet); `next_tag` never names the pseudo-release itself — its existence is discoverable only via AC-1.10's `tag: null` marker on the list's own trailing entry, never by chaining through a real release's `next_tag`.
- [ ] AC-3.2: This story makes no claim about any rendered page. A2 is now resolved, informationally, toward an index-page-with-drill-down shape for a *future* HTML story, but no HTML is produced by this story or this spec (§6).

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | Results to stdout as `sort_keys=True` JSON; diagnostics/errors to stderr; exit `0` on success (incl. honest empty/null), `1` with a named error on failure. `--help` documents flags and any write location. Reuses `insights board`'s existing flag names (`--repo`, `--as-of`, `--format`, `--output`) rather than inventing new ones for the same concepts. | /peer-review |
| NFR-2 | Security (lens) | `--repo` validated against the hostile-input checklist before use (constitution §4). `.spark/<feature-name>/` entries read via directory listing are treated as untrusted path components — validated against traversal before being joined into any filesystem path (a maliciously-named or symlinked entry under `.spark/` must not escape the repo root). `git log <range> -- <path>` invoked with a fixed argument vector (`git -C <repo> ...`), never a shell string built from a feature-directory name (mirrors `gitread.py`'s existing discipline). No raw traceback on any input. | /peer-review |
| NFR-3 | Library (lens) | Zero new runtime pip dependencies (git remains a subprocess). The pseudo-release entry's git-derived figures come from calling the existing `gitboard.board.build_board()` function **in-process** (AC-1.8) — not a new dependency, not a new subprocess boundary, not a second git-parsing implementation. Any new public export is minimal and additive — no breaking change to any existing `build/query/render/diff/verify/serve/board` export. | /peer-review |
| NFR-4 | Privacy / §6 (Non-Negotiable) | No author/committer identity, no per-person breakdown or grouping, ever — mirrors `git-native-mid-cycle-board` NFR-3's verbatim guarantee. Structurally reinforced, not just promised: AC-2.4 bounds artifact parsing to the header table's `Status`/`Date` cells only, and the pseudo-release's figures reuse `build_board()`'s own already-identity-free output (its own NFR-3) rather than needing this feature to re-prove that guarantee independently. | /peer-review + a test asserting no author/trailer field reaches any output |
| NFR-5 | Reliability | Any artifact file read is bounded (only the bytes needed to locate and read the header table, not the whole file) so one pathologically large file under `.spark/` cannot cause an unbounded read. A repo with zero tags, zero `.spark/` directories, or a feature directory with zero commits in any release's (or the pseudo-release's) range is handled without error (mirrors AC-1.4/AC-1.9/AC-2.2's honest-null/honest-zero pattern). | /demo-day (CLI invocation) |
| NFR-6 | Accessibility / UX (lens) | **N/A this cycle, by design — not a silent gap.** No HTML/rendered surface is committed (§6); A2's resolution (index-with-drill-down) only informs a *future* story, and the constitution's live accessibility bar (§4) becomes binding the moment that story is proposed, exactly as it did for `git-native-mid-cycle-board`'s own US-4 (C2 there). | Re-evaluated at the `/story-time` pass that proposes the HTML story |
| NFR-7 | Reproducibility (§1) | Byte-identical stdout for a fixed tag set, `HEAD`, and `as_of` (ADR-4); no `datetime.now()` or other ambient read anywhere in the derivation path; real-release order is git's own tag topology, never wall-clock/creation-date. The pseudo-release entry is explicitly a point-in-time answer relative to the run's `HEAD` — like `insights board` itself, it is expected, not a determinism violation, for it to differ across two runs whose `HEAD` has moved between them; determinism is scoped to "same `HEAD`, same `as_of`," matching `insights board`'s own precedent exactly. | /peer-review + increment test |

## 6. Out of Scope

- **Any HTML/rendered view** — no default silently chosen. A2 resolved the eventual *shape*
  (index page with drill-down), but no HTML story ships this cycle. US-3 prepares the JSON contract
  only.
- **Extraction or summarization of Clarifications, Architecture Decisions, or any other free-form
  prose ("why") beyond the bounded header `Status`/`Date` fields** — blocked on A3, still open. A
  future cycle may add a stable file-level pointer once A3 resolves; not built here.
- **~~The "unreleased since last tag" window, left entirely to `insights board`~~ — REVERSED
  2026-08-19 (C6), at the user's explicit ruling, overriding the PO's own recommendation above.**
  This window is now in scope (US-1 AC-1.8/1.9/1.10; US-3 AC-3.1). What stays genuinely out of
  scope, preserving ADR-0's spirit: **a second, independent implementation of "commits since the
  latest tag."** AC-1.8 requires this feature to call `gitboard.board.build_board()` directly and
  reuse its result verbatim — recomputing that figure a second way is what remains forbidden, not
  the window itself.
- **Any release whose only evidence is a commit-message version string with no actual git tag
  object** (today, concretely: `v0.6.0`, `v0.7.0`) — these are not invisible any more (A4/C6
  absorbed them into the pseudo-release entry), but they are still never treated as a *real, named*
  release; no synthetic tag is ever invented from parsed commit-message text (A5).
- **Cross-repo / fleet aggregation** (backlog I9) — out, same boundary every prior board has
  respected.
- **Any pass/fail, staleness, or health judgment on a release or feature** ("this release is
  overdue", "this feature is stale") — Insights measures, `aspark-ci` enforces (constitution §3,
  off-limits).
- **Writing to, editing, or annotating any `.spark/` artifact** — this feature only ever reads.
- **MCP exposure of this feature** — no story asks for it; a future cycle's call once real usage
  exists, mirroring how `mcp-server` (I7) followed `traceability-metrics` rather than shipping day
  one.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-19 | What does "release" mean for this feature — any version string, or an actual git object? | **Resolved (A5):** an actual git tag (`git tag --list`). A commit-message version string with no tag (`v0.6.0`/`v0.7.0`) is not a *real* release; both are now covered indirectly via the pseudo-release entry (C6). |
| C2 | 2026-08-19 | Does mapping commits to feature directories require a new git-parsing implementation, conflicting with ADR-2? | **Resolved (A6/A7):** no — it generalizes `gitboard/gitread.py`'s existing single-nearest-tag primitive to enumerate all tags and runs one bounded `git log <range> -- <path>` per feature directory, the same subprocess discipline already established, not a second parser. |
| C3 | 2026-08-19 | Is "one release, one feature" a safe assumption to build against? | **Resolved, no — A8/A9:** this repo's own `v0.3.0` spans three feature directories, not the two the PO's original draft assumed (see C7). |
| C4 | 2026-08-19 | (A1) Does release-board belong in `aspark-insights` at all, given no `BACKLOG.md` precedent? | **RESOLVED — the user ruled "yes, in `aspark-insights`."** Matches the PO's working-draft assumption; no story content changed. |
| C5 | 2026-08-19 | (A2) What HTML page shape should a future release-board view use — per-release pages with prev/next, or an index with drill-down? | **RESOLVED, informationally — "an index page with drill-down."** No HTML story ships this cycle (§6 unchanged on that point); this only shapes the *future* `/story-time` pass that proposes one. |
| C6 | 2026-08-19 | (A4) Should release-board also cover the untagged window since the latest tag, or leave it entirely to `insights board` (the PO's own recommendation)? | **RESOLVED — the user ruled the opposite of the PO's recommendation: "yes, include it."** Re-scoped US-1 (new AC-1.8 mandating reuse of `gitboard.board.build_board()` rather than a second implementation, AC-1.9's true-zero-vs-absent rule, AC-1.10's `tag: null` discriminator) and US-3 (AC-3.1's `previous_tag`/`next_tag` rule for the pseudo-release). §6's corresponding Out-of-Scope line corrected in place, not silently dropped. |
| C7 | 2026-08-19 | Re-verifying AC-1.1 for A4's reversal surfaced a second issue: is AC-1.2's original `v0.3.0` example (`public-repo-polish` + `mcp-server`, two members) actually correct? | **No — corrected.** Hand-tracing this repo's own `.git/logs/HEAD` reflog shows `v0.2.0..v0.3.0` contains a third member, `traceability-metrics`, via one trailing "docs: record …release report" bookkeeping commit (`6f987a15`) that lands just inside the next range rather than the one its feature shipped under. This is a systematic pattern at nearly every release boundary in this repo (also true for `mcp-server`→`v0.4.0`, `snapshot-report`→`v0.5.0`, `measurement-honesty`→the pseudo-release) — named as **A9** and folded into AC-1.2's corrected wording. Caught during this gate re-verification pass, not by the original draft; disclosed here rather than silently fixed. |

## 8. Design Review

**N/A this cycle.** No UI-facing story is committed (NFR-6) — this cycle ships JSON only. A2
resolved the *shape* a future HTML story will take (index page with drill-down), but building
that story is deferred to a future `/story-time` pass, which is where a genuine `/look-and-feel`
review belongs — reviewing a page that doesn't exist yet would be a design review of a shape
decision already made in prose, not of a real mockup or running page.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone") — updated for A4's reversal; the success signal now cites independently re-verified real figures (the corrected 3-member `v0.3.0` example, the 6-commits-since-`v0.5.0` pseudo-release example), not just restated claims
- [x] Every story has testable Given/When/Then acceptance criteria — US-1 gains AC-1.8/1.9/1.10 (all falsifiable: a specific function call, a specific presence/absence rule, a specific field); AC-1.2 corrected to a hand-verified real example; US-3's AC-3.1 rewritten with an explicit, checkable `previous_tag`/`next_tag` rule for the pseudo-release
- [x] Stories are prioritized (MoSCoW) and at least one is a Must — unchanged (US-1/US-2 Must, US-3 Should)
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason) — NFR-3 now names the exact reuse mechanism (`build_board()` in-process call); NFR-4 traces the pseudo-release's privacy guarantee to `build_board()`'s own; NFR-7 states precisely why pseudo-release non-determinism across moving `HEAD`s is expected, not a violation
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C4-C7 added; C7 in particular is a self-caught correction, not a rubber-stamped re-check
- [x] Open questions are resolved or explicitly accepted as risk — **A1, A2, A4 resolved this pass (C4-C6); A5-A9 resolved/accepted. A3 remains open but is explicitly accepted as a non-blocking, deferred risk** — no story in this spec's committed scope depends on it, and §6 already excludes the only story type it would affect
- [x] Out-of-scope section is filled (something was consciously cut) — the "unreleased window" line corrected in place (struck through, not silently deleted) to show exactly what reversed and what still holds (no second git-parsing implementation)
- [x] Constitution respected, or conflicts recorded as open questions — no conflict; A4's reversal is explicitly re-grounded in ADR-0 via AC-1.8's mandatory `build_board()` reuse, so the scope expansion doesn't create the "second derivation of the same truth" ADR-0 forbids
- [x] Design review done for UI-facing features (or marked N/A with reason) — **N/A this cycle**: no UI-facing story is committed (NFR-6); a genuine `/look-and-feel` pass is required the moment a future spec revision adds the HTML story A2 already shaped
- [x] Status set to `approved` by the user — approved 2026-08-19, in this conversation ("ja, approved").
