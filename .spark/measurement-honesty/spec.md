# Spec: measurement-honesty

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-04 |

<!-- Closes the disclosure half of I2's accepted risk A3. Not a new metric, not an upstream fix. -->

## 1. Problem & Goal

- **Problem:** This product's central promise is "never invent a number" (constitution §6). It is
  currently breaking that promise on its own repo. The pinned `aspark-graph` v0.7.0 artifact parser
  reads `review-report.md`/`qa-report.md` (`artifacts.py:78-80`), while this repo — and the current
  aSPARK template convention — writes `review.md`/`qa.md`. Result, verified in this repo's own
  `.aspark-graph/graph.json`: 41 `AcceptanceCriterion` nodes, **zero** `QACheck` nodes, **zero**
  `verifies` edges. `traceability.py:41` divides anyway, so `TRC-002` reports a confident **0.0 with
  n=41** and `TRC-004-unverified-acs` reports **41 of 41 unverified** — numbers that look like a
  damning QA finding but are an extraction artifact. I2 accepted this as risk A3 and "disclosed it
  via existing provenance", but no reader can reach that disclosure. Since `snapshot-report` (v0.4.0)
  shipped, the fabricated zero is rendered on an HTML page built to be skimmed and believed.
- **Goal:** A metric whose evidence layer is entirely missing from the graph reports `value: null`
  with a reason naming what was and wasn't observed — never a computed zero — and a reader of the
  HTML report sees that caveat without hunting for it. Where artifact files exist on disk but
  produced no graph nodes, the reason says so, turning "we can't measure this" into "here is your
  actual bug".
- **Success signal:** `insights build` on this repo (unchanged tree) produces `TRC-002` and
  `TRC-004-unverified-acs` as `null` with a reason naming both counts (0 QA-evidence nodes in the
  graph, 4 `qa.md` files on disk), while `TRC-001`/`TRC-003`/`TRC-004-orphan-tasks` keep their real
  values (their `maps_to`/`implements` evidence does exist). `insights render` shows a caveat notice
  in the report's top band stating how many metrics of the total could not be computed, which ones,
  and where the detail lives. No metric anywhere reports a computed value derived from an evidence
  kind with a repo-wide count of zero.
- **Why now:** The dishonest number is now on a rendered page, and I6's finding-density metrics
  (BACKLOG §3) read the same unparsed `Finding` nodes — they would inherit the same lie. Fixing the
  rule before those metrics exist makes the guarantee structural instead of retrofitted twice.

## 2. Target Users

- **Whoever runs `insights build`/`render`/`query` today** — the Insights maintainer dogfooding
  against this repo and `aSPARK-graph`. They currently cannot tell a real 0% from an extraction gap.
- **Any consumer of a snapshot's JSON** (the MCP `query` tool, a future `aspark-ci`): reads the same
  sealed `value`/`reason`, so it inherits the fix with no surface-specific logic.
- **Not a target:** `aspark-graph`'s maintainer (the upstream filename fix is out of scope, §6); any
  external package importer (none exists).

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | The graph's artifact extraction yields zero `QACheck`/`Finding` nodes for every current-convention repo. | **Verified twice**: `aSPARK-graph/src/aspark_graph/artifacts.py:78-80` names the legacy filenames; this repo's built `graph.json` contains no `QACheck` node and no `verifies` edge alongside 41 `AcceptanceCriterion` nodes. Not re-derived at build time — Insights states what it observes, not what upstream does. |
| A2 | Insights gains a second source of truth about the repo: an assumption about the `.spark/` layout it currently knows nothing about. | Accepted by the user (2026-08-04) with the cost named. Bounded by NFR-2/NFR-3 (presence only, no contents, one level deep, fixed filename set). Failure mode is deliberately conservative: if the convention changes filenames again, the probe under-reports ("no artifact files found"), never over-claims — see AC-2.5. |
| A3 | `aspark-policy` is unusable as a dogfood target (its own `TemplateDriftError` means it has no built graph). | Dogfood targets are **this repo** and `aSPARK-graph` only. No AC depends on `aspark-policy`. |
| A4 | Snapshots built before this release keep their old, misleading numbers; `insights verify` against one now fails `verify_mismatch`. | Accepted and documented (AC-5.4). No backfill or migration of stored snapshots (§6) — rewriting sealed history would be a worse dishonesty than the one being fixed. |
| A5 | Does a changed null-condition on a shipped metric need a `metric_version` bump, and which? | **Yes — confirmed by the user 2026-08-04** (major bump, superseded entry removed; both alternatives — keeping both versions registered, and no bump at all — were put to the user and rejected). A consumer that could previously assume a number can now get `null`: a breaking change to the value contract, so a **major** bump (`1.0.0` → `2.0.0`) for exactly the metrics whose behavior changes, with the superseded registration removed so one `metric_id` never computes twice per snapshot (US-5). Without it, `insights diff` shows `0.0 → null` under an unchanged version string — the same definition apparently producing two answers, which is precisely the lie this feature exists to kill. |
| A6 | Does the rule apply registry-wide, or only to the QA-evidence metrics? | **Registry-wide**, per the user's settled scope decision (2026-08-04). On this repo that changes only the two QA-evidence metrics, because `maps_to`/`implements` evidence genuinely exists — which is exactly the discrimination the rule is supposed to have (see the success signal). |
| A7 | Any open question left blocking the gate? | No. `/look-and-feel` ran on 2026-08-04 (§8); its one Blocker and five Major spec-amendment findings are folded into AC-2.1, AC-4.1, AC-4.2, AC-4.3, the new AC-4.6 and NFR-4, and logged as C9–C16. The two `/increment`-safe findings (D6, D7) are logged too, D7 as a testable clause inside AC-2.1. Only the user's approval remains. |

## 4. User Stories

### US-1 (Must): An absent evidence layer reports `null` + reason, never a computed zero

> As a reader of any metric, I want a metric whose evidence is entirely missing from the graph to
> say so instead of returning a number, so I never mistake an extraction gap for a measurement.

**Acceptance criteria:**

- [ ] AC-1.1: **Definition (testable).** Every registered metric declares the **evidence kind(s)** its
      numerator counts — the graph node/edge kind that has to exist for the numerator to be able to
      be non-zero (e.g. `TRC-002`/`TRC-004-unverified-acs`: a `verifies` edge from a passing
      `QACheck`; `TRC-001`/`TRC-004-orphan-tasks`: a `maps_to` edge; `TRC-003`: an `implements`
      edge). The evidence layer is **absent** exactly when the count of that kind across the whole
      scope-filtered graph is zero.
- [ ] AC-1.2: Given a graph where a metric's declared evidence kind has a repo-wide count of zero,
      when `insights build` runs, then that metric's entry has `value: null` and a non-empty `reason`
      — never `0`, `0.0`, `null` without a reason, or a count equal to its own `n`.
- [ ] AC-1.3: Given a graph where the declared evidence kind occurs at least once, when
      `insights build` runs, then the metric's `value` and `n` are **byte-identical to today's
      output** for the same input — this rule adds a null condition, it never changes a computed
      number.
- [ ] AC-1.4: Given a metric whose denominator is also empty (`n == 0`), the existing
      denominator-absent reason wins (e.g. `"no AcceptanceCriterion nodes found in graph"`) — one
      null, one reason, deterministic precedence, never two competing explanations. This precedence
      is what AC-4.1's caveat trigger keys off, so it holds end to end: one null, one reason, one cue.
- [ ] AC-1.5: Given this repo's own tree, when `insights build` runs, then `TRC-002` and
      `TRC-004-unverified-acs` are `null` with a reason, and `TRC-001`, `TRC-003`,
      `TRC-004-orphan-tasks` and `TRC-005-*` still carry computed values.
- [ ] AC-1.6: Given the rule lives in the registry's shared path, when a new metric is registered
      that declares an evidence kind, then it inherits the null-on-absent-evidence behavior without
      restating it — provable by registering a throwaway test metric and asserting it nulls on a
      graph lacking its evidence kind.

### US-2 (Must): The reason names what was actually observed, on disk and in the graph

> As whoever reads the null, I want the reason to distinguish "QA never ran here" from "your QA
> artifacts were never parsed", so the null is a diagnosis rather than a shrug.

**Acceptance criteria:**

- [ ] AC-2.1: Given the evidence layer is absent **and** ≥1 file matching the built-in artifact
      filename set exists under `<repo>/.spark/<feature>/`, when `insights build` runs, then the
      reason states both observations with counts — the evidence-kind count in the graph (zero) and
      the number of matching files found — and names the artifact filename(s) matched. **No reason
      this feature produces (AC-2.1/2.2/2.3) begins with a digit**: it renders into the report's
      Value column, where a leading `0` reads as the metric's own value — the exact confusion this
      feature exists to remove (check: `reason[0].isdigit() is False`). Illustrative phrasing, not
      prescriptive: `"no QA-evidence nodes found in the graph (0 of 41 ACs); 4 matching artifact
      files found under .spark/"`.
- [ ] AC-2.2: Given the evidence layer is absent **and** no matching file exists, the reason says so
      explicitly ("no matching artifact files found under `.spark/`") — a materially different string
      from AC-2.1's, so the two cases are distinguishable by a reader and by a test.
- [ ] AC-2.3: Given the presence check could not complete (see US-3), the reason states the evidence
      layer is absent **and** that the on-disk check was inconclusive, naming why — never silently
      falling back to AC-2.2's wording.
- [ ] AC-2.4: The reason asserts only what Insights itself observed (counts in the graph, counts on
      disk). It never states a specific `aspark-graph` version's parser behavior as fact — Insights
      does not verify that claim, and it would become false the moment the sibling is upgraded.
      (Falsifiable: no reason string contains a hardcoded sibling version number or a filename the
      probe did not itself look for.)
- [ ] AC-2.5: The probe's outcome is recorded in the snapshot's provenance on **every** build,
      including builds where no metric is affected — otherwise "no caveat shown" is
      indistinguishable from "the check never ran", the same invisible-disclosure failure A3 already
      produced once. The recorded value is counts/flags only (AC-3.6). This record must also *render*
      on every report, not only exist in the JSON — see AC-4.6.
- [ ] AC-2.6: The probe runs at `build` time only. `query`, `render`, `diff`, `verify` and the MCP
      `query` tool read the sealed snapshot and touch no other file — provable by rendering a
      snapshot from a directory that contains no `.spark/` at all and still seeing the caveat.

### US-3 (Must): The new filesystem read path is safe, bounded and deterministic

> As whoever points `--repo` at an arbitrary tree, I want the artifact-presence check to be
> incapable of crashing the build, escaping the repo, or making a snapshot non-reproducible.

**Acceptance criteria:**

- [ ] AC-3.1: Given `<repo>/.spark/` does not exist, when `insights build` runs, then it exits 0 and
      the probe reports "no matching artifact files found" (AC-2.2) — an absent `.spark/` is a valid
      answer, not an error.
- [ ] AC-3.2: Given `<repo>/.spark` exists but is a regular file, a broken symlink, or a symlink of
      any kind, when `insights build` runs, then it exits 0 with an inconclusive probe result
      (AC-2.3), never a traceback. Symlinks are never followed, at any level of the probe.
- [ ] AC-3.3: Given `<repo>/.spark/` (or a feature directory inside it) cannot be listed — e.g.
      permissions removed — when `insights build` runs, then it exits 0 with an inconclusive probe
      result naming the OS-level cause, never a raw traceback (constitution §6).
- [ ] AC-3.4: The probe reads **zero bytes of file content**: a matching file that is empty, huge, or
      invalid UTF-8 changes nothing about the build's behavior or output beyond being counted, and
      the build exits 0.
- [ ] AC-3.5: The probe descends exactly one level (`<repo>/.spark/<feature>/<known-filename>`). A
      file at `<repo>/.spark/a/b/c/qa.md` is not counted, and a `.spark/` containing 1,000 feature
      directories completes within NFR-1's budget.
- [ ] AC-3.6: Nothing the probe records in the snapshot contains an absolute path, a home directory,
      a username, or any filename outside the built-in set — snapshots stay machine-independent and
      person-free (constitution §6).
- [ ] AC-3.7: Every path the probe touches is composed of `--repo` plus the built-in filename set
      only — never a value from graph content, snapshot content, or another flag. The existing
      hostile-input checklist for `--repo` (empty string, `../` traversal, absolute path, a
      nonexistent path) is exercised against the probe and each case either exits 0 or exits 1 with
      an existing named error.
- [ ] AC-3.8: Building twice against the same unchanged tree (with `.spark/` present) produces
      byte-identical snapshots — the probe sorts its traversal, reads no clock and no mtime, and does
      not depend on directory iteration order. The existing determinism canary is extended to cover a
      repo with a populated `.spark/`.

### US-4 (Must): The caveat reaches a reader of the HTML report

> As someone skimming `report.html`, I want to see that a metric was not measurable — and why —
> without scrolling into a table cell, because a caveat nobody sees is not a disclosure.

**Acceptance criteria:**

- [ ] AC-4.1: **Trigger, content, stacking, check.**
      *(i) Trigger* — the notice appears exactly when ≥1 metric is null **and the reason that
      actually shipped on that metric is an evidence-absent reason** (AC-2.1/2.2/2.3). A metric whose
      null carries the denominator-absent reason (AC-1.4) never raises it: binding the trigger to the
      shipped reason rather than to the underlying condition keeps AC-1.4's principle intact end to
      end — one null, one reason, **one cue** — and leaves the fresh-repo first screen identical to
      the empty state `/demo-day` already accepted as reading correctly.
      *(ii) Placement* — in the top band `snapshot-report` AC-1.6 reserves: after the `<h1>` and
      summary, before the provenance section.
      *(iii) Content, in this order* — (a) the count of affected metrics against the total ("2 of 8
      metrics could not be computed — the evidence they count is absent from the graph"), count first
      so the notice degrades gracefully as the list grows; (b) the affected `metric_id`s; (c) a
      pointer to where the full reason lives ("see the Metrics table below"), mirroring the stale
      cue's existing "see Provenance for details". The full `reason` strings never appear in the top
      band — AC-2.1's reasons carry two counts plus filenames, and AC-4.2 owns the detail. Example
      strings are illustrative content, not prescriptive markup.
      *(iv) Stacking* — `graph_staleness.stale` is `true` on this repo today, so both cues render
      together on the very first real run. Order is fixed: **stale cue first, evidence caveat
      second**, because staleness qualifies everything below it *including* the caveat's own
      observation counts. The caveat opens with a constant label token distinct from `STALE` (e.g.
      `NOT COMPUTED —`) so the two blocks are told apart by their first word rather than by body text
      or hue, and it reuses `.stale-cue`'s box geometry (border width, padding, margin, weight)
      rather than introducing a third block shape. If `/increment` introduces a new hue anyway,
      NFR-4's contrast measurement covers that new pair too.
      *(v) Check* — byte offsets in the rendered HTML, anchors named explicitly: top
      `<p class="stale-cue">` < caveat `<p>` < `<section id="provenance">`.
- [ ] AC-4.2: The affected metric's own row still shows its full `reason` in the existing
      `Not computed: …` shape (`snapshot-report` AC-3.2) — the notice is *in addition to*, never
      *instead of*, the row-level explanation. This is an **accessibility requirement, not
      redundancy**: a screen-reader user navigating by heading jumps `h1 → Provenance` and skips band
      (1) entirely, so the row-level reason inside `<h2>Metrics</h2>` is the guaranteed path to the
      detail (§8, Accessibility notes). It must not be weakened or traded against the top-band notice.
- [ ] AC-4.3: Given no metric carries an evidence-absent reason, **no evidence-caveat notice,
      placeholder or empty container** is rendered anywhere in the output. Explicitly unaffected by
      this rule: `snapshot-report` AC-3.3's shipped `.empty-notice` empty-facts block
      (`render.py:93-99`) and AC-4.6's provenance row — neither is an evidence-caveat artefact.
      Testable in the direction that matters: rendering a snapshot in which every metric is null
      **with a denominator-absent reason** (the fresh-repo first screen) produces no caveat notice
      and still renders the empty-facts notice.
- [ ] AC-4.4: The notice carries a textual label, never color alone (constitution §4), and every
      string it renders passes through the existing escaping choke-point — a `reason` containing
      `<script>` appears escaped, and the page still renders end-to-end (exit 0).
- [ ] AC-4.5: The page remains fully static and self-contained: no JavaScript, no external fetch, and
      the existing fixed section order (AC-1.6) is unchanged.
- [ ] AC-4.6: The probe's provenance record (AC-2.5) renders in the report's **Provenance** section on
      **every** report — affected or not — in the same field/value row shape as the existing entries.
      Without it, AC-2.5's guarantee and C7's resolution hold in JSON only, and the failure case is
      live, not theoretical: an inconclusive probe (AC-2.3 — `.spark` a symlink or unreadable) against
      a graph that *does* carry evidence affects no metric, renders no caveat, and leaves a reader
      concluding "measured fine" with nothing on the page to correct it. The provenance rows are
      generated from the record's own keys rather than a hardcoded literal list (`render.py:166`
      enumerates rows literally today and silently drops any new top-level field), so a future
      provenance field cannot vanish the same way. Not new scope: this is what `snapshot-report`
      AC-1.3 already promises ("verbatim … never summarized away") and the current renderer cannot
      deliver for a new field.

### US-5 (Must): A changed metric definition is visible as a changed version

> As a consumer diffing two snapshots, I want a metric whose definition changed to carry a new
> version, so I never see the same definition apparently produce two different answers.

**Acceptance criteria:**

- [ ] AC-5.1: Every metric whose null-conditions changed ships under a new `metric_version`
      (`1.0.0` → `2.0.0`, per A5); `TRC-005-*`, whose behavior is unchanged, stays `1.0.0` — the bump
      tracks behavior, not the release.
- [ ] AC-5.2: `registry.list()` contains exactly one entry per `metric_id` — a superseded definition
      is removed, never left registered alongside its successor, so one snapshot never carries both
      the honest null and the old fabricated zero.
- [ ] AC-5.3: `insights diff <old> <new>` on two snapshots spanning this change shows the
      `metric_version` change together with the value change.
- [ ] AC-5.4: `insights verify` against a snapshot built before this release fails with the existing
      `verify_mismatch` named error (exit 1, no traceback) — expected behavior for changed
      definitions, documented in the README (US-6), not a bug to suppress.

### US-6 (Should): The README stops making claims that are two releases stale

> As anyone landing on the repo, I want the README's status claims to be true, so the project's own
> front page isn't the least honest artifact it ships.

**Acceptance criteria:**

- [ ] AC-6.1: The README no longer states `v0.2.0` as the current status (status banner and family
      table); the version it claims equals `aspark_insights.__version__` at release time.
- [ ] AC-6.2: The "Not yet implemented — `insights render`" usage block and the unchecked
      "Dashboards — planned" item are replaced by what actually shipped (`render` writes
      `report.html`; MCP `serve` shipped).
- [ ] AC-6.3: One short section documents this feature's rule with a real example reason string, the
      built-in artifact filename set the probe looks for, and the AC-5.4 `verify_mismatch`
      consequence.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Performance | The probe adds < 1s to `insights build` on a repo with ≤ 1,000 feature directories on a mid-range laptop (AC-3.5); `build` on this repo stays under its current wall-clock feel. | `/demo-day` timing |
| NFR-2 | Security — filesystem read path (`security` lens) | The probe follows no symlinks, reads no file contents, descends exactly one level, and composes paths only from `--repo` + a built-in filename set (AC-3.2/3.4/3.5/3.7). The constitution §4 hostile-input checklist is exercised against it: empty `--repo`, `../` traversal, absolute path, `.spark` as a file, unreadable directory — every case exits 0 or exits 1 with a named error, never a traceback. | `/peer-review` + targeted tests per hostile case |
| NFR-3 | Security & privacy — what leaves the repo | No file content, absolute path, username or home path enters the snapshot, the report or any error message; recorded probe output is counts/flags only (AC-3.6). No person-level data (constitution §6). | `/peer-review` |
| NFR-4 | Accessibility & UX (`ux` lens, constitution §4) | The caveat notice: (a) renders as a block-level element in band (1) with no new heading, no heading level skipped, and never between an `<h2>` and its own section content — verifiable from the rendered HTML; (b) carries a textual label, never color alone; (c) contrast measured via `getComputedStyle` on named pairs — notice text vs. notice background ≥ 4.5:1, notice border vs. page background ≥ 3:1, plus any new hue `/increment` introduces beyond the reused `.stale-cue` palette (AC-4.1(iv)); (d) at 375px the notice's `metric_id` list **wraps**, no horizontal scroll, and the notice is never placed inside a `.table-wrap` scroll container; (e) no new interactive element — `document.querySelectorAll('a,button,input,select,textarea,[tabindex]').length` stays `0`. | `/look-and-feel` + `/demo-day` |
| NFR-5 | Reliability / determinism (ADR-4) | Same tree ⇒ byte-identical snapshot and byte-identical `report.html`; no clock, no mtime, no directory-iteration-order dependence; determinism canary extended to a repo with a populated `.spark/` (AC-3.8). | CI canary + `/demo-day` |
| NFR-6 | CLI (`cli` lens) | No new flag ships. `build --help` documents that `build` also *reads* `<repo>/.spark/` for artifact presence (a read, never a write), per the project's "document the location in `--help`" convention. stdout stays `canonical_json`, errors stay the C2 named-error idiom. | Golden `--help` test + `/peer-review` |
| NFR-7 | Library (`library` lens) | The metric registry is public surface and its value contract changes (a previously numeric metric may now be `null`) → the package version is bumped this release (behavior changed, per CLAUDE.md's "a bump is a claim about behavior"), and the change is noted in the README (AC-6.3). Zero new runtime dependencies; the probe adds no public function beyond the one the rule needs. | `/peer-review` (public-surface diff) + `/go-live` |
| NFR-8 | Observability | N/A — synchronous CLI, no background process; the probe's outcome is itself the observable record, sealed in provenance on every build (AC-2.5) and rendered on every report (AC-4.6). | — |

## 6. Out of Scope

- **Fixing the filename mismatch in `aspark-graph`** — a real upstream gap, a neighbor-repo change.
  This feature discloses it; it does not patch the sibling (unchanged from I2's §6).
- **A second artifact parser in Insights** — reading `qa.md` *contents* to synthesize QACheck nodes
  would violate ADR-0 and the "no second parser" precedent. The probe answers exactly one question a
  graph structurally cannot ("does a file exist that you failed to parse") and reads no bytes.
- **Any new metric**, including I6's finding-density family — this feature only changes when existing
  metrics refuse to answer.
- **`snapshot-report`'s accepted B1/B2/B3 report polish** — separately accepted, not bundled here.
  B2 is referenced once in NFR-4 only as a mistake class the new notice must not repeat.
- **Aligning the summary block's `Null:` label** (`render.py:149`) to the table's "not computed"
  phrasing — user decision 2026-08-04 (C14): it would complete D6's consistency but changes
  `snapshot-report`'s shipped output, which US-4 does not scope. The residual three-words-for-one-
  state inconsistency is consciously accepted, not overlooked.
- **A per-feature evidence breakdown** ("which features have qa.md") in the snapshot or the report —
  counts only; a per-feature table is a new metric in disguise.
- **A configurable artifact-filename set, or any new CLI flag for the probe** — built-in and
  documented (AC-6.3); configurability has no requester.
- **Backfilling or migrating stored snapshots** to the new definitions — sealed history stays sealed
  (A4); `verify` honestly mismatching is the disclosure.
- **An escape hatch (`--allow-zero`, `--strict`) to get the old confident zero back** — that is the
  bug, re-exposed as a feature.
- **An in-row marker on the affected metric rows** — the §8 watch item: at 8 rows, scanning from the
  notice's id list is trivial; revisit only if I6 grows the registry substantially.
- **Threshold/gating on nulls** — `aspark-ci`'s job (constitution §3).
- **A broader README rewrite or docs restructure** beyond the three false claims and the one new
  section — `public-repo-polish` already set the structure; this is a truth patch, not a redesign.
- **Person-level metrics** — permanently out (constitution §6).

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-04 | Filesystem-presence check, or the conservative null-on-any-repo-wide-zero fallback with no disk access at all? | **Filesystem presence check** (user decision). The ADR-0 argument was accepted — a directory listing is not a second artifact parser, and the graph cannot answer "does a file exist that you failed to parse" — along with the acknowledged cost (A2). Determinism stays non-negotiable (AC-3.8). |
| C2 | 2026-08-04 | Two-metric special case, or a general registry-wide rule? | **General rule** (user decision): any registered metric whose evidence layer is entirely absent reports `null` + reason, so I6's future metrics inherit it structurally (AC-1.1, AC-1.6). The *implementation location* of the rule is `/sprint-plan`'s call, not this spec's. |
| C3 | 2026-08-04 | May the reason name the specific upstream parser gap ("v0.7.0 reads `qa-report.md`")? | **No — user confirmed 2026-08-04**, upholding the PO's deliberate override of the original brief (the alternatives "name the parser gap explicitly" and "observations + a static version-free pointer" were both put to the user and rejected). Partly: it names the gap **as an observation** — "N `qa.md` files present, 0 QA-evidence nodes in the graph" — which is the actionable half and satisfies "here's your actual bug". It does not assert the sibling's parser internals as fact (AC-2.4): Insights doesn't verify that, and the claim would silently become false on an upstream upgrade — the same class of unchecked stale claim this feature exists to remove. |
| C4 | 2026-08-04 | Does a changed null-condition need a `metric_version` bump, and is that a spec concern? | Yes to both — it is user-visible contract behavior, not an implementation detail, so it is an AC (US-5). PO recommends a **major** bump for exactly the changed metrics, with the superseded registration removed (A5). |
| C5 | 2026-08-04 | Is the README refresh part of this feature or a separate chore? | **Part of it, as a Should** (US-6). This feature changes documented metric behavior, so the README must be touched regardless; fixing the three stale claims in the same pass is near-zero marginal cost. Scope is capped at those claims plus one new section (§6). |
| C6 | 2026-08-04 | What happens when the denominator is *also* empty — two competing reasons? | Denominator-absent wins, deterministically (AC-1.4). One null, one reason. |
| C7 | 2026-08-04 | Does "no caveat rendered" mean "measured fine" or "the check never ran"? | Neither is left to inference: the probe result is sealed into provenance on every build, affected or not (AC-2.5) — the fix for exactly the invisible-disclosure failure A3 produced. **Amended by C13**: sealing it in JSON is not sufficient; AC-4.6 now requires it to render on every report, because the renderer would otherwise drop it. |
| C8 | 2026-08-04 | Does the caveat need to reach the MCP tool and `query` as well as the report? | It already does, with no extra work: the reason is sealed in the snapshot every surface reads (AC-2.6). No surface-specific disclosure logic ships. |
| C9 | 2026-08-04 | **D1 (§8, Major)** — `graph_staleness.stale` is `true` on this repo today, so two caveats stack in the same top band on the very first real run; AC-4.1 stated neither their order nor how a reader tells them apart. | Folded into **AC-4.1(iv)**: fixed order (stale cue first — staleness qualifies the caveat's own counts), a constant `NOT COMPUTED —`-style label token distinct from `STALE` so the two differ by their first word rather than by hue, reuse of `.stale-cue`'s box geometry instead of a third block shape, and any new hue pulled into NFR-4's contrast measurement. Byte-offset anchors named in **AC-4.1(v)**. |
| C10 | 2026-08-04 | **D2 (§8, Major)** — "names the affected `metric_id`s" renders an opaque identifier list; nothing on the page expands those ids (the metrics table is ID/Version/Value only, no glossary). | Folded into **AC-4.1(iii)**: the notice states count-against-total first (degrades gracefully as the list grows), then the ids, then a pointer to the Metrics table — mirroring the stale cue's existing "see Provenance for details". Full `reason` strings stay out of the top band; AC-4.2 owns the detail. §1's success signal reworded to match. |
| C11 | 2026-08-04 | **D3 (§8, Major)** — on a fresh repo the evidence layer *and* the denominator are both absent, and two defensible readings of AC-4.1 × AC-1.4 give either no notice or a notice listing every metric. | Folded into **AC-4.1(i)** and mirrored in **AC-4.3**: the trigger binds to *the reason that actually shipped on the metric*, never to the underlying condition — a denominator-absent null never raises the caveat. Keeps AC-1.4's principle end to end (one null, one reason, one cue) and leaves the first-run page identical to the empty state `/demo-day` already accepted. AC-1.4 cross-references the trigger so the coupling is visible from both ends. |
| C12 | 2026-08-04 | **D4 (§8, Major)** — AC-4.3's "no notice … anywhere in the output" literally forbade `snapshot-report`'s shipped, QA-verified `.empty-notice` block, in exactly the case where it must appear. | **AC-4.3** narrowed to "no **evidence-caveat** notice, placeholder or empty container", with explicit carve-outs naming `snapshot-report` AC-3.3's empty-facts notice (`render.py:93-99`) and AC-4.6's provenance row as unaffected. The negative test now also asserts the empty-facts notice still renders. |
| C13 | 2026-08-04 | **D5 (§8, Blocker)** — `render.py:166` builds provenance rows from a hardcoded literal list (enumerating keys dynamically only inside `graph_staleness`), so AC-2.5's sealed probe record is dropped from the HTML; C7's "no caveat ≠ no check" guarantee held in JSON only. Independently reproduced by the coordinator, not taken on report. | New **AC-4.6**: the probe's provenance record renders in the Provenance section on every report, affected or not, in the existing field/value row shape, with rows generated from the record's own keys rather than another literal — so a future provenance field cannot vanish the same way. AC-2.5 and C7 cross-reference it. Not new scope: `snapshot-report` AC-1.3 already promises provenance "verbatim … never summarized away". |
| C14 | 2026-08-04 | **D6 (§8, Minor)** — three reader-facing words for one state ("Null:", "Not computed:", and the notice's unspecified wording). Should the summary block's `Null:` label be aligned too? | **User decision: no.** The notice reuses the table's existing "not computed" phrasing (safe for `/increment`, inside AC-4.1's wording), but the summary label stays as shipped — aligning it changes `snapshot-report`'s output, which US-4 does not scope. The residual inconsistency is **consciously accepted**, and recorded in §6 so it is not re-discovered as an oversight. |
| C15 | 2026-08-04 | **D7 (§8, Minor)** — a reason beginning with a digit reads as the metric's value inside the Value column, since the `Not computed:` prefix is doing all the disambiguating work. | Routed as `/increment`-safe by the Designer, but made **testable inside AC-2.1**: no reason this feature produces begins with a digit (`reason[0].isdigit() is False`), with illustrative word-first phrasing. Cheap to check, and it is the precise confusion the feature exists to remove. |
| C16 | 2026-08-04 | **D8 (§8, Major)** — two of NFR-4's clauses were not falsifiable: "semantic HTML inside the existing heading hierarchy" (the precedent element is a bare `<p>` with no heading) and a contrast bar that never named which pairs are measured. | **NFR-4 rewritten** into five checkable clauses: block-level in band (1) with no new heading / no skipped level / never between an `<h2>` and its section content; textual label; named contrast pairs (notice text vs. notice background ≥ 4.5:1, notice border vs. page background ≥ 3:1, plus any new hue) via `getComputedStyle`; 375px wrapping of the id list and never inside a `.table-wrap`; and "no new interactive element" restated as the measurement `/demo-day` already runs (`querySelectorAll(...).length === 0`). |

## 8. Design Review

<!-- Filled by /look-and-feel. Empty design review = gate stays red for UI-facing features. -->

- **Overall impression:** The design instinct behind US-4 is right and the placement decision is
  right: a caveat that only lives in a table cell is the failure this feature exists to kill, and
  AC-4.1's top-band placement, AC-4.2's "in addition to, never instead of", AC-4.3's no-empty-
  container rule and AC-4.4's textual-label-plus-escaping requirement are all correct, precedent-
  consistent calls. Evidence base for this review: `.spark/snapshot-report/spec.md` (AC-1.4/1.6/3.2
  and its own §8), `src/aspark_insights/render.py` in full (the only HTML/CSS artifact in the
  project), and a live `insights render` of this repo's own current snapshot — not a mockup. That
  live page is what surfaces the two problems the spec does not yet address. First,
  `graph_staleness.stale` is **`true` on this repo today** (rendered evidence: two `<p
  class="stale-cue">` blocks, one directly under the summary and one inside Provenance), so the
  very first real run of this feature renders **two different caveats in the same top band**, and
  AC-4.1 states neither their relative order nor how a reader tells them apart (D1). Second, the
  caveat's *quiet* case is under-designed: AC-2.5 seals the probe result in provenance on every
  build and C7 leans on that to settle "no caveat shown vs. the check never ran" — but
  `render.py:166-179` builds the provenance table from a **hardcoded row list**, so a new
  provenance field is silently dropped from the page (D5). On the questions raised: the top band
  *is* the right home (Q1 — the problem is stacking, not placement); naming `metric_id`s alone is
  *not* enough (Q2 — D2, spec amendment); the existing `Not computed:` shape *is* strong enough at
  a glance and I am not raising a finding against it (Q3 — see Accessibility notes for the measured
  numbers and the reasoning); the empty first-run page reads correctly *only* under one of two
  possible readings of AC-1.4 × AC-4.1, and the spec does not say which (Q4 — D3); NFR-4 has two
  clauses that are not falsifiable as written (Q5 — D8). Nothing below asks for new features,
  interactivity, JS, a second toolchain, or reopens any settled scope cut; every finding is a
  presentation/structure gap inside the already-agreed scope, argued from this project's own
  precedent. `snapshot-report`'s accepted B1/B2/B3 are treated as out of scope and are not
  re-raised — only referenced once, as a class of mistake the new notice must not repeat (D8).
  Applied lens: `ux` only (`seo`/`i18n` off per constitution §2); elevated-load flag noted.

- **Heuristics findings:**

  1. **[Major] D1 — Two top-band caveats stack with no defined order and no defined way to tell
     them apart.** *Location:* AC-4.1; existing implementation `render.py:32` (`.stale-cue`),
     `render.py:154-158` and `:182-184` (the two cues), live evidence lines 30 and 33 of the
     rendered report. *Rule violated:* hierarchy + consistency & standards — AC-4.1 places the new
     notice in exactly the band `snapshot-report` AC-1.6 already reserves for the stale cue, but
     specifies no order between them and no visual differentiation. On this repo both fire on the
     first run. `render.py` offers exactly two block-notice styles (`.stale-cue`, `.empty-notice`);
     reusing `.stale-cue` yields two visually identical bold-amber blocks that a skimmer parses as
     one repeated warning, and inventing a third bespoke block style is the "third way of doing the
     same thing". AC-1.6's byte-offset test checks `<section>`/`<h2>` anchors only, so it cannot
     adjudicate two `<p>`s inside band (1). *Fix:* amend AC-4.1 to state (a) a deterministic order —
     **stale cue first, evidence caveat second**, because staleness qualifies everything below it
     *including the caveat's own observation counts*; (b) the caveat opens with a constant label
     token distinct from `STALE` (e.g. `NOT COMPUTED —`), so the two blocks are distinguishable by
     their first word, not by body text or hue; (c) the notice reuses `.stale-cue`'s box geometry
     (border width, padding, margin, weight) rather than introducing a new block shape — if
     `/increment` instead introduces a second hue, NFR-4's contrast measurement must cover that new
     pair (see D8); (d) checkable by byte offset with the anchors named explicitly (top stale-cue
     `<p>` < caveat `<p>` < `<section id="provenance">`). → **spec amendment** (adds testable
     ordering/labelling behavior — the same class as `snapshot-report` finding 2, routed to
     `/story-time` as AC-1.6 via C6).

  2. **[Major] D2 — "Names the affected `metric_id`s" gives the reader an opaque identifier list
     with no stakes and no pointer.** *Location:* AC-4.1. *Rule violated:* match to the real world
     + recognition over recall — the notice as specified renders `TRC-002,
     TRC-004-unverified-acs` and nothing else. Nothing on the page expands those ids: the metrics
     table is Metric ID / Version / Value only (`render.py:80-82`), there is no name or description
     column and no glossary. The reader is left to recall what the identifier denotes and cannot
     tell whether this is a footnote or half the report. Both existing top-band cues already do
     better: the stale cue states its consequence *and* points at where the detail lives
     ("see Provenance for details", `render.py:156`), and the summary block directly above already
     speaks in counts (`Facts / Metrics / Computed / Null`, `render.py:144-151`). *Fix:* amend
     AC-4.1 so the notice states, in this order: (a) the count of affected metrics against the
     total rendered ("2 of 8 metrics could not be computed — the evidence they count is absent from
     the graph"); (b) the affected `metric_id`s; (c) a pointer to where the full reason lives ("see
     the Metrics table below"), mirroring the stale cue's existing pattern. Count-first also makes
     the notice degrade gracefully when the list is long (a future registry where many metrics null
     at once — `ux` lens §2 large-data), which an id-list-only notice does not. Do **not** put the
     full `reason` strings in the top band: AC-2.1's reasons carry two counts plus filenames, and
     the band is a cue, not the explanation — AC-4.2 already owns the detail. → **spec amendment**
     (changes what AC-4.1 requires the notice to contain).

  3. **[Major] D3 — The notice's trigger is undefined when the evidence layer *and* the denominator
     are both absent — i.e. on the first-run/empty repo.** *Location:* AC-4.1 and AC-4.3 vs.
     AC-1.4. *Rule violated:* consistency & standards + visibility of status (`ux` lens §2, empty
     state). AC-4.1 fires "given ≥1 metric is null **because its evidence layer is absent**";
     AC-1.4 says that when the denominator is also empty the denominator-absent *reason* wins. On a
     fresh repo with no `.spark/` — the exact screen `snapshot-report`'s design review identified as
     the real first screen, and the state its `empty-state` fixture already exercises — every metric
     is null and *both* conditions hold. Two readings are equally defensible: trigger on the reason
     that actually shipped (no notice) or trigger on the underlying condition (a notice listing all
     8 metrics). The second reading puts a bold caveat block on top of an all-null table on a page
     that already reads "Facts: 0 / Null: 8" — that is the "the tool is broken" reading, not "the
     tool worked and found nothing". Two implementers can build both and pass the letter of the
     current ACs. *Fix:* amend AC-4.1 (and AC-4.3's mirror condition) to bind the trigger to **the
     reason that actually shipped on the metric**, not to the underlying condition: a metric whose
     null carries the denominator-absent reason never raises the caveat. That keeps AC-1.4's own
     principle intact end to end — one null, one reason, **one cue** — and makes the first-run page
     identical to the empty state `/demo-day` already accepted as reading correctly. State it as
     testable: rendering a snapshot in which every metric is null with a denominator-absent reason
     produces no caveat notice. → **spec amendment** (resolves a real ambiguity between two Must
     ACs; answers Q4 — the precedence rule produces the right page, but only under this reading).

  4. **[Major] D4 — AC-4.3's wording literally forbids the empty-state notice that
     `snapshot-report` requires.** *Location:* AC-4.3 vs. `snapshot-report` AC-3.3 and
     `render.py:93-99` (`<p class="empty-notice">No facts recorded for this snapshot.</p>`).
     *Rule violated:* consistency & standards — AC-4.3 says "no notice, placeholder or empty
     container appears **anywhere in the output**". Its intent is clearly "no *evidence-caveat*
     artefact", but its literal scope is the whole page, and the case it applies to (no metric
     null-for-absent-evidence) is exactly the fresh-repo case where the shipped `.empty-notice`
     block *must* appear — the block `/demo-day` credited with making the empty state read as "the
     tool worked" (`qa.md` AC-3.3 row). Read literally it would also forbid the provenance row D5
     asks for. An implementer following the letter deletes a shipped, approved, QA-verified
     element. *Fix:* narrow the wording to "no **evidence-caveat** notice, placeholder or empty
     container appears anywhere in the output", and add the explicit carve-out that
     `snapshot-report`'s AC-3.3 empty-facts notice and the AC-2.5 provenance record are unaffected.
     → **spec amendment** (AC text change; a one-line edit, but it currently contradicts an
     approved AC of the previous increment).

  5. **[Blocker] D5 — AC-2.5's sealed probe result never reaches the rendered page, so C7's
     guarantee holds in JSON only — the same unreachable-disclosure failure this feature exists to
     fix.** *Location:* AC-2.5 / C7 vs. `render.py:161-179`; also `snapshot-report` AC-1.3.
     *Rule violated:* visibility of status, and `snapshot-report` AC-1.3's own requirement that
     provenance is presented "verbatim … never summarized away". `_render_provenance` composes its
     rows from a **hardcoded list** (`as_of`, `insights_version`, `metric_registry_version`,
     `graph_source.access/.sealed`, `scope_filter.patterns/.excluded_count`) and only enumerates
     keys dynamically *inside* `graph_staleness` (`render.py:178-179`). A new top-level provenance
     field recording the probe outcome is therefore dropped from the HTML entirely. Consequences on
     the page: a reader who sees no caveat cannot distinguish "the probe ran and found evidence"
     from "the probe was inconclusive (AC-2.3) but no metric happened to be affected" — and the
     AC-2.3-inconclusive-yet-nothing-affected case is real (`.spark` is a symlink or unreadable per
     AC-3.2/3.3, while the graph does carry evidence). The reader forms the wrong belief
     ("measured fine") with nothing on the page to correct it, on the surface the spec itself calls
     "built to be skimmed and believed" (§1). That is task failure, not friction — hence Blocker,
     even though the fix is small; the caveat itself does still reach the page in the affected case,
     but the negative confirmation C7 promises does not. *Fix:* add an AC under US-4 requiring the
     probe's provenance record (AC-2.5) to be rendered in the report's Provenance section on **every**
     report, affected or not, in the same field/value row shape as the existing entries — and make
     the row generation key-driven for it rather than another hardcoded literal, so a future
     provenance field cannot silently vanish the same way. This is not new scope: it is what
     `snapshot-report` AC-1.3 already promises for provenance, which the current renderer cannot
     deliver for a new field. → **spec amendment** (new AC under US-4).

  6. **[Minor] D6 — Three different reader-facing words for one state.** *Location:*
     `render.py:149` (summary `<strong>Null:</strong>`), `render.py:61` (`Not computed: …`), and
     AC-4.1's notice (wording unspecified). *Rule violated:* consistency & standards — the same
     concept is about to be named a third way on one page, in the band where a reader first meets
     it. *Fix:* the notice reuses the table's existing reader-facing phrasing ("not computed"),
     not a new synonym ("unmeasurable", "missing", "N/A"). This fits inside AC-4.1's existing
     wording, so → **safe for `/increment`**. Aligning the summary's `Null:` label to the same word
     would complete the consistency but touches `snapshot-report`'s shipped output and is outside
     US-4's stated scope — **raising it as a question for the PO**, not applying it.

  7. **[Minor] D7 — A reason string that starts with a digit reads as a value inside the Value
     column.** *Location:* AC-2.1 (reason content) as rendered through AC-4.2 / `render.py:61`.
     *Rule violated:* recognition over recall — AC-2.1 requires the reason to state both counts, and
     the natural phrasing starts with one ("0 QA-evidence nodes in the graph, 4 `qa.md` files
     found…"). Rendered into the Value column of a metrics table, the `Not computed:` prefix is
     doing all the work of stopping a skimmer from reading a leading `0` as the metric's value —
     precisely the confusion this feature exists to remove. *Fix:* require the reason's leading
     token to be a word, not a digit (e.g. "no QA-evidence nodes found in the graph (0 of 41 ACs);
     4 matching artifact files found under `.spark/`"). Cheap, testable (`reason[0].isdigit() is
     False`), and it composes with the existing prefix. Fits inside AC-2.1's existing "states both
     observations with counts" → **safe for `/increment`**.

- **Accessibility notes:**

  8. **[Major] D8 — Two of NFR-4's five clauses are not falsifiable as written.** *Location:*
     NFR-4. *Rule violated:* constitution §4 (the accessibility bar is meant to be checkable by
     inspecting the rendered HTML, not asserted). (a) *"semantic HTML inside the existing heading
     hierarchy"* has no test: the notice sits in band (1), between `<h1>` and the first `<h2>`,
     where the precedent element (`render.py:154-158`) is a bare `<p>` with no heading at all —
     "inside the heading hierarchy" cannot pass or fail. Tighten to the precedent-matching, checkable
     form: *"the notice renders as a block-level element in band (1) with no new heading, no
     heading level skipped, and does not appear between an `<h2>` and its own section content —
     verifiable from the rendered HTML."* (b) *"text contrast ≥ 4.5:1 and any border/graphic ≥ 3:1"*
     never names **which pairs** are measured; if the notice carries a tinted background like
     `.stale-cue`'s `#fff6e5`, the meaningful pair is notice-text-vs-notice-background, not
     notice-text-vs-page-white. Tighten to name them: *notice text vs. notice background ≥ 4.5:1;
     notice border vs. page background ≥ 3:1; measured via `getComputedStyle`.* Two further
     tightenings while NFR-4 is open: *"no horizontal scroll at 375px"* should add that the notice's
     id list **wraps** and that the notice is never placed inside a `.table-wrap` scroll container —
     otherwise it inherits exactly the discoverability problem `snapshot-report`'s accepted B2
     describes (referenced as a class of mistake to avoid, not re-raised); and *"no new interactive
     element to keyboard-operate"* should be stated as the check that already exists —
     `document.querySelectorAll('a,button,input,select,textarea,[tabindex]').length` stays `0`, the
     exact measurement `qa.md` NFR-8 recorded. → **spec amendment** (NFR-4 rewording; small, but NFR
     text is spec text).

  - **Contrast — pre-verified, not a finding, if the palette is reused.** Recomputed from
    `render.py:32`: `.stale-cue` text `#7a4a00` on `#fff6e5` ≈ **6.97:1** (matches the number
    `/demo-day` measured via `getComputedStyle`, `qa.md` NFR-4 row) and its `#7a4a00` border against
    the page's `#fff` ≈ **7.48:1**; `.null-value` `#444` on `#fff` ≈ **9.74:1** (QA measured 9.7:1).
    So reusing the existing notice palette (D1's fix (c)) ships contrast-safe with margin, and the
    real risk in the top band is **distinguishability**, not legibility. These are derived from the
    CSS source, not from a live `getComputedStyle` — no browser tooling was available for this
    review, so **any new color `/increment` introduces is unverified and becomes a `/demo-day`
    measurement task** under NFR-4 as tightened above.
  - **Distinguishing the honest zero from the honest null (Q3) — verified adequate, no finding.**
    On the live page `TRC-005-extracted` renders `0.0 (n=13)` and, after this feature, `TRC-002`
    renders `Not computed: <reason>` — the two differ by a constant leading label, by italic vs.
    upright, and by length. That is a shape difference plus a text difference, not a color
    difference, so it survives greyscale and low vision; it is the fix `snapshot-report`'s own
    design review finding 4 specified, and QA confirmed it renders as intended (`qa.md` AC-3.2
    row). AC-4.2's reuse of that shape is the right call and needs no strengthening — manufacturing
    a stronger treatment here would add a fourth visual vocabulary to the page for no measured
    problem. **One watch item, deliberately not a finding at current scale:** a reader who reads the
    notice's id list must then find those rows by scanning the metrics table, and nothing marks the
    affected rows. At 8 rows this is trivial; if I6's finding-density metrics grow the registry
    substantially, revisit whether the affected rows need an in-row marker.
  - **Heading navigation — checked, not a gap, and this is why AC-4.2 is load-bearing.** A
    screen-reader user navigating by heading jumps `h1 → Provenance` and skips band (1) entirely —
    so the new notice, like the existing stale cue, is invisible to that navigation mode. It is not
    *lost*, because AC-4.2 guarantees the same information inside the `<h2>Metrics</h2>` section as
    the row's `reason`. That makes AC-4.2 an accessibility requirement, not merely redundancy:
    it must not be weakened or traded away for the top-band notice at `/sprint-plan` time.
  - **Keyboard / focus / motion:** N/A and correctly so — the notice ships zero interactive
    elements, so there is no focus order, no hover/focus state and nothing for
    `prefers-reduced-motion` to apply to (`ux` lens §5). This matches the shipped page's measured
    state (`focusableEls: 0`, `qa.md` NFR-8) and NFR-4's own "no new interactive element" clause,
    which D8 turns into the same measurement.
  - **`ux` lens items with nothing to report:** flow efficiency (§1) and forms & input (§3) — the
    page is a single static document with no navigation and no inputs; state coverage (§2) is
    covered by D3/D4 above; responsive/touch (§4) by D8's 375px tightening.

- **Design risks & required changes:**

  - **Route to `/story-time` before the gate closes — spec amendments (PO decision):** **D5**
    (Blocker — probe provenance must render, new AC under US-4), **D1** (top-band order and
    differentiation, AC-4.1), **D2** (notice states count + ids + pointer, AC-4.1), **D3** (bind
    the caveat trigger to the shipped reason, AC-4.1/AC-4.3), **D4** (narrow AC-4.3's scope so it
    stops forbidding `snapshot-report`'s empty-facts notice), **D8** (NFR-4 rewording). D1/D2/D3
    all sit in AC-4.1 and can be folded in one pass. Left unresolved, two implementers could build
    materially different top bands that both pass the letter of the current ACs — the same
    ambiguity `snapshot-report`'s C6 amendment closed for the stale cue.
  - **Safe for `/increment` to apply directly inside existing AC/NFR wording:** **D6** (the notice
    reuses the page's existing "not computed" phrasing) and **D7** (reason strings do not open with
    a digit).
  - **One question back to the PO, not applied:** should the summary block's `Null:` label
    (`render.py:149`) be aligned to the same reader-facing word as the table and the notice? It
    would complete D6's consistency but changes `snapshot-report`'s shipped output, which US-4 does
    not currently scope.
  - **Sequencing note for `/sprint-plan`:** D1's "stale cue first" ordering is not cosmetic — on a
    stale graph the probe's "0 evidence nodes" observation may itself be an artifact of staleness,
    so reading the staleness caveat *before* the evidence caveat is what stops the two from being
    read as independent facts. It costs nothing to get right at implementation time and is
    expensive to retrofit after the byte-offset test is written against the wrong order.
  - **Deferred to `/demo-day` (cannot be settled from source):** any color the notice introduces
    beyond the existing `.stale-cue` palette must be measured with `getComputedStyle` (NFR-4);
    375px wrapping of the notice's id list must be measured with
    `innerWidth`/`scrollWidth`/`clientWidth`, per this project's own "measure, don't eyeball"
    technique.
  - **Out of scope and not re-raised:** `snapshot-report`'s accepted B1 (gridline contrast), B2
    (mobile scroll affordance) and B3 (`repr()` fact values) — B2 is referenced once in D8 only as a
    mistake class the new notice must not repeat. Nothing above requires interactivity, JavaScript,
    a framework, a second toolchain, or reopens ADR-5, the no-new-flag decision, or any §6 cut.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk (A5 and C3 confirmed by the user
      2026-08-04; A6 settled at the same time; A2/A3/A4 accepted as named risks)
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected, or conflicts recorded as open questions
- [x] Design review done for UI-facing features (or marked N/A with reason) — `/look-and-feel` ran
      2026-08-04 (§8); the Blocker (D5) and all five Major spec-amendment findings (D1–D4, D8) are
      folded in and logged as C9–C13 and C16; D6/D7 logged as C14/C15
- [x] Status set to `approved` by the user (2026-08-04)
