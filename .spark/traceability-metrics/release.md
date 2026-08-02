# Release: traceability-metrics

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.2.0 |
| **Date** | 2026-08-01 |

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — one Major (F1: a non-JSON or non-executable
      staleness subprocess could leak a raw traceback, violating AC-6.2 and the
      "never a raw traceback" non-negotiable) fixed and re-verified green, plus two
      Minors (F2 cross-platform `fnmatch` case-sensitivity, F3 stale docstring) fixed.
      F4 (spec AC-1.2's wording never reconciled to the shipped pass-only behavior)
      closed by amending the spec text itself (C7) — no code change, since the shipped
      behavior was already correct. F5 (broader-than-planned staleness passthrough)
      accepted as-is (more disclosed provenance is strictly more honest). No open
      Blocker/Major/Minor. Gate closed.
- [x] `qa.md` status is `passed` — every TRC-*/MTA-* number independently hand-recomputed
      from raw `graph.json` against the real `aSPARK-graph` (1348 nodes/1569 edges) and this
      repo's own real graph, exact match every time, including the two-entry TRC-004 split,
      the three-entry TRC-005 confidence-mix, and the 476-node worktree-exclusion count named
      in the spec's own Problem statement. One Major test-environment gap (B4: the real
      `aSPARK-policy` target proved genuinely unbuildable — a pre-existing, unrelated
      `TemplateDriftError` in that repo's own `spec.md`, not a defect in this feature) resolved
      by the user accepting a scratch-fixture substitute. One Minor (F1: raw Python exception
      text leaking into otherwise-clean named-error messages) fixed and re-verified. F2/F3
      accepted/informational. No open Blocker/Major/unresolved Minor. Gate closed.
- [x] Full test suite green **on the release commit itself**, re-run fresh, twice: once
      before staging (`uv run pytest -v` → **128 passed**, matching the expected count) and
      once again after both commits landed (`uv run pytest -q` → **128 passed**). `uv sync
      --extra dev` resolved cleanly (41 resolved, 39 checked) and `uv lock --check` was clean
      both before and after the version bump.
- [x] Build succeeds from a clean state — `uv run insights build --help` and both
      `insights build` invocations below ran clean, including a full re-install triggered by
      the version bump (`uv` rebuilt and reinstalled the editable `aspark-insights` package
      mid-test-run without incident).
- [x] No uncommitted changes in the working tree — `git status` reports "nothing to commit,
      working tree clean" after both commits, and again after the post-release smoke check.
- [x] Real end-to-end build re-run against the actual sibling repo (not a fixture), **before
      committing and again after**, on the exact release commit: `insights build --repo
      /Users/andreaslottes/aSPARK-graph --as-of 2026-08-01 --output <scratch>` → exit 0 both
      times. Every metric value matched the QA report's independently hand-verified numbers
      exactly: TRC-001 `0.8604651162790697`/n=43, TRC-002 `0.1`/n=160, TRC-003
      `0.37681159420289856`/n=69, TRC-004-orphan-tasks `1`/n=69, TRC-004-unverified-acs
      `144`/n=160, TRC-005-declared `0.36363636363636365`/extracted `0.0`/inferred
      `0.6363636363636364` (n=11), `scope_filter.excluded_count: 476`. `find
      /Users/andreaslottes/aSPARK-graph -maxdepth 1 -iname .aspark-insights` returned empty
      both before and after — sibling repo confirmed untouched.
- [x] Real end-to-end build re-run against **this repo's own real graph** (this feature's
      whole point is real dogfood data), before and after committing: TRC-001 `1.0`/n=14,
      TRC-002 `0.0`/n=41 (the A3 filename-mismatch caveat — a real, honestly-computed 0%, not
      a crash or a fabricated number), TRC-003 `0.875`/n=24, TRC-004-orphan-tasks `0`/n=24,
      TRC-004-unverified-acs `41`/n=41, TRC-005-declared `1.0`/extracted `0.0`/inferred `0.0`
      (n=13) — matches QA's own self-repo hand-computation exactly. `provenance.insights_version`
      correctly reads `0.2.0` post-bump.
- [x] Determinism re-verified independently of the canary's own CI fixture: built this repo's
      own graph twice to two separate scratch outputs with identical `--as-of`, `shasum -a 256`
      on both → identical hash (`09a99ca3eb...`), `diff` reported no differences.

## 2. Version

**v0.2.0** — minor bump from `v0.1.0`. Justification:

- This release adds a genuine new capability (real TRC-001..005/MTA-001..003 computation
  against real graphs, ScopeFilter exclusion, staleness disclosure) — not a bug fix and not
  merely internal scaffolding. Under semver's own "initial development" convention (`0.x.y`),
  the **minor** component (`x`) is the right place to record a new, additive, backward-compatible
  feature; the **patch** component (`z`) is reserved for fixes to what's already there.
- Stays pre-1.0 deliberately, matching the prior release's own stated 1.0 bar: dashboards
  (I5), policy resolution (I8), and flow/architecture metrics (I3/I4) are all still ahead per
  the backlog, and the constitution's own open question ("set a performance number once I2
  ships real computation") is exactly the kind of not-yet-stabilized surface a 0.x version
  communicates honestly.
- Nothing about this release removes or changes the shape of anything I1 shipped in a
  breaking way — every provenance/model change (`MetricValue.n`, `Provenance.scope_filter`,
  `Provenance.graph_staleness`) is additive, and no prior snapshot exists in production to be
  broken by it (the only prior artifacts are fixtures, already regenerated as a stated,
  non-silent clean break per plan §5 risk table).

## 3. Changelog

<!-- Next-developer-facing language — the spec's own Target Users section (§2) names the
     aSPARK-graph/aSPARK-policy maintainers and the Insights maintainer building I3+, not an
     external end user. -->

### Added
- Real, hand-verifiable coverage numbers computed straight from your repo's actual graph:
  what share of your stories trace down to a task (TRC-001), what share of your acceptance
  criteria have a passing QA check verifying them (TRC-002), and what share of your tasks
  trace forward into code (TRC-003) — every one of these carries its own sample size right
  next to the percentage, so a coverage number over 5 items is never mistaken for one over
  500.
- A clear count of exactly which tasks have no trace at all and exactly which acceptance
  criteria are unverified (TRC-004) — reported as two separate, honest numbers rather than
  one blended ratio that would hide which one is actually the problem.
- A breakdown of how much of your traceability picture rests on links you declared yourself
  versus links the tooling had to infer (TRC-005) — so a high coverage number is never
  mistaken for a strongly-evidenced one.
- Every metric now honestly reports "nothing to measure yet" (a `null` value with a plain-English
  reason) instead of a misleading 0% or 100% whenever your repo genuinely has zero of the
  relevant thing (e.g. no stories at all yet) — never a fabricated number.
- A built-in filter that automatically excludes known duplicate-file noise (like editor/agent
  worktree copies) from every coverage number before it's computed, and now tells you exactly
  what was excluded and how much, right in the output — so a scoped result is never mistaken
  for the whole repo.
- Every snapshot now tells you whether the graph it was built from was still up to date with
  your repo on disk at build time — so a stale snapshot's numbers are never presented as
  unconditionally fresh. Numbers are still computed even when the graph is stale; you're just
  told so.
- `insights query` now prints the real metrics alongside the facts and provenance it already
  showed — no more empty metrics array.

### Changed
- Nothing about how you invoke `insights build`/`query` changed — no new flags, no new
  subcommands. The same commands you already know now return real numbers instead of an
  empty catalog.

### Fixed
- A build could previously crash with a raw internal error message (rather than a clear,
  named one) if the graph's own freshness-check subprocess returned something unexpected —
  now it always degrades to an honest "freshness unknown, here's why" instead.
- Error messages for a malformed or corrupted graph file used to embed a bare internal Python
  error string; they now read as a plain-English description of what's actually wrong with
  the input (e.g. "has an entry missing required field 'type'").

**Explicitly NOT included in this release** (future increments, per the backlog): no
dashboards or HTML rendering (`render` remains the loud, honest `not_implemented` stub);
no policy-derived metrics; no flow/cycle-time or DORA-style metrics (I3); no architecture-health
metrics (I4, blocked on further graph scope hygiene); no per-feature drill-down of the orphan/
unverified counts (today's numbers are repo-wide aggregates); no CLI-configurable scope-exclude
patterns beyond the built-in default set.

## 4. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Bundling decision | Three files were finished, approved artifacts from earlier this session but **not part of this feature's own reviewed diff**: `.spark/constitution.md` (drafted via `/charter`, all open questions confirmed by the user in-session), `.spark/foundation/release.md` (the prior release's own report, status `released`, never committed because I1's `/go-live` predated this repo having any commit to attach it to), and `CLAUDE.md` (conventions doc, created with the user's explicit consent after `foundation` shipped). `review.md` explicitly recorded it *ignored* these three as "unrelated prior-session work" when scoping its diff review. **Judgment call made:** committed these three as a separate, preceding housekeeping commit (`00e9c02`, "docs: record foundation's release report, project constitution, and conventions") rather than folding them into the feature release commit — so each commit's diff matches exactly what was reviewed under that feature's own gates, and the I2 feature commit stays a clean, auditable unit. This is a judgment call, not a given: if the user prefers a single commit (or three separate ones), both commits are still local-only and trivially reversible (`git reset --soft`/`--hard` against `86b2beb`) before anything is ever pushed. |
| Version bump & tag | `pyproject.toml`: `0.1.0` → `0.2.0` (minor bump, see §2). `src/aspark_insights/__init__.py`'s `__version__` constant updated to match (nothing reads it dynamically from `pyproject.toml`; `uv.lock`'s own `aspark-insights` package entry updated to `0.2.0` as a side effect of `uv sync`/rebuild — a 2-line diff, verified). `METRIC_REGISTRY_VERSION` in `build.py` deliberately left at `0.1.0` — its own code comment states it versions the registry's *mechanism/contract* (register/get/list), not the catalog's contents, and that contract didn't change shape in this feature. Committed as `7ef4a43` ("feat: traceability-metrics — real TRC-001..005/MTA-001..003 (I2)"). Created local annotated tag `v0.2.0` on that commit. **Local only — no push**, consistent with there being no remote configured. |
| PR / merge | Not applicable — no remote configured, nothing to open a PR against. |
| Deploy | Not applicable — this is a CLI package, not a service; there is nowhere to "deploy" it to. |
| Post-release smoke check | Ran after both commits landed, against the actual committed state: `git status` → clean. `uv run pytest -q` → **128 passed**. `insights build --help` → usage text documenting the real-metrics behavior, exit 0. `insights build --repo /Users/andreaslottes/aSPARK-graph --as-of 2026-08-01 --output <scratch>` → exit 0, same exact metric values as the pre-commit run, `insights_version: 0.2.0` in provenance, sibling repo confirmed untouched afterward. `insights build --repo /Users/andreaslottes/aSPARK-insights --as-of 2026-08-01 --output <scratch>` → exit 0, same exact metric values as the pre-commit run. `git status` confirmed clean again after the smoke check itself. |

**Exact commands run (git-relevant excerpt, in order):**
```
# Bundling / housekeeping commit (see judgment call above)
git add .spark/constitution.md .spark/foundation/release.md CLAUDE.md
git status                 # verified only these 3 files staged
GIT_AUTHOR_NAME="Andreas Lottes" GIT_AUTHOR_EMAIL="andreas@lottes.dev" \
GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git commit -m "docs: record foundation's release report, project constitution, and conventions" \
              -m "..." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
# -> 00e9c02

# Version bump
# pyproject.toml: version = "0.1.0" -> "0.2.0"
# src/aspark_insights/__init__.py: __version__ = "0.1.0" -> "0.2.0"
uv sync --extra dev        # regenerates uv.lock's aspark-insights entry to 0.2.0
uv run pytest -q           # 128 passed, re-verified post-bump

# Feature release commit
git add .gitignore pyproject.toml uv.lock \
  src/aspark_insights/__init__.py src/aspark_insights/build.py src/aspark_insights/cli.py \
  src/aspark_insights/model/provenance.py src/aspark_insights/model/value.py \
  src/aspark_insights/ports/graph.py \
  src/aspark_insights/metrics/collectors.py src/aspark_insights/metrics/scope.py \
  src/aspark_insights/metrics/traceability.py \
  tests/fixtures/trace_graph.json tests/test_boundary.py tests/test_build.py \
  tests/test_build_metrics.py tests/test_build_staleness.py tests/test_cli_stubs.py \
  tests/test_collectors.py tests/test_determinism_canary.py tests/test_graph_integration.py \
  tests/test_model.py tests/test_provenance_schema.py tests/test_registry.py \
  tests/test_scope.py tests/test_traceability.py \
  .spark/traceability-metrics/spec.md .spark/traceability-metrics/plan.md \
  .spark/traceability-metrics/review.md .spark/traceability-metrics/qa.md
git status                 # verified: nothing untracked left, no .venv/, __pycache__/,
                            # .pytest_cache/, .aspark-insights/, .aspark-graph/, .DS_Store, .claude/
GIT_AUTHOR_NAME="Andreas Lottes" GIT_AUTHOR_EMAIL="andreas@lottes.dev" \
GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git commit -m "feat: traceability-metrics — real TRC-001..005/MTA-001..003 (I2)" \
              -m "..." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
# -> 7ef4a43

GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git tag -a v0.2.0 -m "v0.2.0 — traceability-metrics (I2): real TRC-001..005/MTA-001..003, ScopeFilter, staleness disclosure"
```

**Git identity note:** re-checked before committing — no `user.name`/`user.email` has been
configured on this machine since `foundation`'s release (confirmed via `git config --list
--show-origin`, same as last time: no output). Per the standing "never touch git config" rule,
the same env-var-scoped workaround from the prior release was reused: `GIT_AUTHOR_*`/
`GIT_COMMITTER_*` set only for the exact `git commit`/`git tag` invocations, no config file
touched. Identity used: `Andreas Lottes <andreas@lottes.dev>`, same as `86b2beb`/`v0.1.0`.
**Flagging again**, as `foundation`'s own release report and this project's constitution (§5)
both already recommended: a persistent local identity should be configured before the *next*
`/go-live` pass, so this workaround doesn't need repeating a third time.

**Pending — outward-facing, requires explicit human go (none currently applicable):** there is
still no remote configured, no PR target, and no deploy target for this CLI package — identical
to `foundation`'s state. If/when a remote is added, the outstanding outward-facing actions at
that point would be `git push -u origin main` and `git push origin v0.1.0 v0.2.0` (both tags),
and — only if the family decides to publish this package — `uv publish` or equivalent. None of
these were run, and none should be run without a separate, explicit go once a remote exists.

## 5. Rollback Path

There is now a real prior state to roll back to (`v0.1.0` / `86b2beb`), unlike `foundation`'s
first release. Concretely, since nothing has been pushed anywhere:

- **To undo the tag only:** `git tag -d v0.2.0`.
- **To undo both commits and return exactly to the released `foundation` state:**
  `git reset --hard 86b2beb` — clean, since neither commit has been pushed or seen by anyone
  else, and `git status` confirms the working tree is clean right now (no uncommitted work would
  be lost).
- **To undo only the feature commit but keep the housekeeping commit:**
  `git reset --hard 00e9c02` (or `git revert 7ef4a43` if a paper trail of the rollback itself is
  preferred over rewriting history).
- **To undo only the housekeeping commit but keep the feature:** not directly reversible with a
  single `reset` once both are stacked (the feature commit doesn't touch the housekeeping files,
  so `git rebase --onto` or a manual `git revert 00e9c02` would work if ever needed — an unlikely
  request, since the housekeeping commit is pure documentation with zero code coupling).
- **Nothing external depends on either commit yet** — no remote, no consumers, no published
  package, no CI run against either commit. Rollback carries zero blast radius today.
- **Once this is pushed** (a future, separate, authorized step): rollback would then mean
  `git revert` (never `push --force` on a shared branch) for a mistake found after the fact, or
  simply not tagging/publishing a package release from this commit if the mistake is caught
  before that outward step.

## 6. Learnings (Keep!)

- **What went well:**
  - Both gates found *real* bugs, not process theater. Review's own F1 (a staleness-subprocess
    failure that would have leaked a raw traceback) is precisely the same bug *class* as
    foundation's B2/F1/F5 — the discipline of re-checking "never a raw traceback" on every new
    I/O boundary, not just the ones that failed last time, paid off again. QA's independent,
    from-raw-graph-data hand-recomputation of every single TRC-*/MTA-* number (not "read the
    output and it looked plausible") is what actually earned confidence in this release's
    headline claim — every number in this report's pre-flight section matches QA's own
    hand-computed figures exactly, both before and after the release commit.
  - The A3 caveat (this repo's own current-convention `.spark/` filenames make the installed
    `aspark-graph` report zero QACheck/Finding nodes, so TRC-002 legitimately reads 0.0 here)
    was reproduced for real, twice now — once by `/increment`'s own T11 integration test, once
    independently by QA — and both times correctly recognized as a real, honestly-computed
    number rather than a bug. That consistency is a good sign the "evidence honesty"
    non-negotiable is actually load-bearing in practice, not just in the spec's prose.
  - The `/peer-review` → spec-amendment loop (F4/C7: AC-1.2's wording was reconciled to match
    the shipped, reviewed pass-only behavior rather than either silently drifting or forcing a
    behavior change to match stale spec text) is a clean example of fixing the *right* side of
    a spec/code disagreement — the shipped logic was already the more coherent, honesty-aligned
    choice.
  - QA's B4 (the real `aSPARK-policy` dogfood target proving genuinely unbuildable due to an
    unrelated `TemplateDriftError` in that repo's own `spec.md`) is exactly the kind of
    cross-repo, out-of-scope discovery worth surfacing rather than working around — QA
    correctly declined to fix another product's tracked content mid-QA, and the user made the
    call to accept a scratch-fixture substitute rather than have QA improvise a workaround.
  - The TRC-004 "two distinct entries, never blended into one ratio" pattern and TRC-005's
    "multi-way breakdown ships as multiple immutable registry entries, not a dict-valued
    `MetricValue.value`" (plan §6 deviation) are both clean, reusable answers to "what happens
    when one spec'd metric has more than one denominator" — worth keeping as the house style
    for any future multi-part metric, rather than re-litigating per feature.

- **What we'd do differently:**
  - The A1 assumption ("both dogfood repos have a graph built before `/demo-day`") was wrong in
    practice for `aSPARK-policy`, and this was discovered reactively by QA rather than checked
    as an environment-readiness step before `/demo-day` started. A cheap "confirm both named
    dogfood targets are actually buildable" pre-check at `/sprint-plan` or the start of
    `/demo-day` — the same spirit as this project's own "confirm git identity before
    `/go-live`" lesson from `foundation` — would have caught the `TemplateDriftError` earlier
    and cheaper, and possibly in time to file it as a heads-up to `aSPARK-policy`'s own
    maintainers before this cycle's QA needed to route around it.
  - Local git identity is *still* unconfigured on this machine, for the second release in a
    row, despite `foundation`'s own release report and this project's constitution (§5)
    explicitly flagging it as something to fix before the next `/go-live`. The env-var
    workaround is a fine mitigation, but the underlying recommendation clearly isn't
    self-enforcing just by being written down once — worth a harder nudge (e.g. a `/sprint-plan`
    or `/increment` startup check that fails loudly if `git config --list --show-origin` is
    empty) rather than relying on the report being re-read.
  - The `METRIC_REGISTRY_VERSION` vs. package `__version__` split (one bumped, one deliberately
    not) is correct per its own documented rationale, but it's a subtle distinction a future
    contributor could easily get wrong in either direction (bumping both reflexively, or
    forgetting the registry version exists at all when a metric's *computation* — not just its
    presence — changes). Worth a one-line comment cross-reference between the two constants'
    definitions, or a test asserting they're allowed to diverge, so the "same version bump
    doesn't have to mean the same thing" design intent survives past the person who wrote it.

- **Patterns worth reusing:**
  - **File this as a follow-up for `aSPARK-policy`'s own maintainers, not fixed here:** its
    `.spark/format-json-schema/spec.md` has a `TemplateDriftError`-triggering heading shape
    (`### US-6 — dropped (A2 resolved to Option A)`) that the installed `aspark-graph`'s parser
    can't handle — a real, verified, out-of-scope data-quality bug discovered as a byproduct of
    this release's own QA, worth relaying to that repo's maintainers as a candidate bug report
    (flagging for the user's awareness/decision, not auto-filed).
  - **A3's "reuse existing disclosure, don't invent a second flag" design** (trusting
    `graph_source.access`/staleness provenance to carry the filename-mismatch risk rather than
    adding a bespoke field) is a good instance of the constitution's own "don't recompute what
    the graph already answers" principle applied one level up — to *disclosure*, not just
    computation. Worth citing as precedent the next time a new risk tempts a bespoke new
    provenance field.
  - **Keeping a feature's own reviewed diff and any unrelated-but-ready housekeeping commits
    separate** (this release's bundling judgment call) is a reusable convention: it keeps each
    commit's diff matching exactly what its own review/QA gates actually examined, which matters
    for any future audit or bisect of "what did `/peer-review` actually look at when it passed
    this."
  - Candidate for `CLAUDE.md`/shared memory: "when `/demo-day` or `/go-live` depends on a named
    external dogfood repo being in a buildable state, verify that assumption as an environment
    check at the *start* of the phase that needs it, not as a reactive discovery mid-testing."

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time (fresh test run — 128 passed, twice; fresh
      real-sibling-repo build; fresh real-self-repo build; clean working tree — all re-verified
      on the actual release commit `7ef4a43`, not copied from `review.md`/`qa.md`)
- [x] Changelog written in user-facing (next-developer-facing) language, no commit hashes, no
      ticket IDs, no internal jargon
- [x] Release actions executed and verified for everything in scope (two local commits + local
      tag `v0.2.0`) — outward-facing actions (push, PR, deploy, publish) correctly **not**
      executed: there is no remote, no PR target, and no deploy target for this CLI package,
      identical to `foundation`'s own state. This is a reportable, intentional "prepared,
      awaiting go" state, not a failure.
- [x] Rollback path written and concretely actionable (see §5) — user confirmed both judgment
      calls: (1) keep the housekeeping/feature split as two separate commits, and (2)
      prepare-only (local commit + tag, no push) is the entirety of what's actionable, same
      reasoning as `foundation`'s own release.
- [x] Learnings recorded — what went well, what we'd change, reusable patterns, and follow-ups
      flagged for the user's awareness (the `aSPARK-policy` `TemplateDriftError`, the
      still-unconfigured git identity)
- [x] Status set to `released` — confirmed by the user.
