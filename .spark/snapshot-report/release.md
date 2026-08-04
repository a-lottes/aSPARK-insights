# Release: snapshot-report

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.4.0 |
| **Date** | 2026-08-04 |

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — one Blocker (F1: a snapshot that is
      valid JSON and passes `require_snapshot_shape`'s top-level check but
      carries a wrong sub-shape entry — a metric missing `value`/`reason`/
      `n`, a non-list `facts` — made `render_html` raise a raw
      `KeyError`/`TypeError` that escaped `main`'s `except InsightsError`;
      `run_render` now wraps `render_html` in
      `except (AttributeError, KeyError, TypeError)` and re-raises
      `SnapshotUnreadableError`, narrowly scoped to `render` only —
      `query`/`verify` untouched) fixed and re-verified in a genuinely
      adversarial re-review (the Reviewer tried to route around the fix
      with list-of-non-dicts, `None` elements, int `metric_id`, null
      `provenance`, non-dict `graph_staleness` and could not). One Nit
      (F2: a metric with `value != None` but `n == None` showed a bare
      value; now renders `(n unavailable)`, confirmed unreachable today —
      all 12 real `MetricValue` constructions always pass `n` — fixed
      anyway for honesty). No open Blocker/Major. Gate closed by the user
      2026-08-04.
- [x] `qa.md` status is `passed` — this project's first genuine hands-on
      browser `/demo-day`. All 17 Must/Should ACs and 6 browser-observable
      NFRs verified pass in a real browser, including mechanical checks
      (byte-offset section ordering, measured contrast ratios, a
      JS-verified 375px viewport with zero horizontal scroll) and the QA
      Tester independently re-deriving the F1 security fix with their own
      hand-crafted hostile snapshot. Three Minor findings (B1: table
      gridline contrast ≈2.85:1 vs the 3:1 non-text threshold; B2: no
      visual affordance hinting wide tables scroll internally at 375px;
      B3: dict-valued fact fields render as Python `repr()`, not JSON) —
      all explicitly **accepted by the user on 2026-08-04**, not fixed,
      recorded in `qa.md`'s Findings table and QA GATE checklist. No open
      Blocker/Major. Gate closed by the user 2026-08-04.
- [x] Full test suite green **on the exact working tree being released**,
      run fresh by me, not copied from review/QA's own numbers:
      - Pre-bump (working tree as review/QA saw it): `uv run pytest -q` →
        **194 passed** in 124.56s — matches review.md's re-review count
        exactly ("Full suite re-run: 194 passed").
      - Post-bump (after the version edit + `uv sync`, on the exact tree
        that became commit `7e52db4`): `uv run pytest -q` → **194 passed**
        in 29.09s.
      - **One disclosed flake in between, not on the release tree, not
        hidden:** a single background run during this pass (while I was
        concurrently running a live `insights build`/`render` round-trip
        against the real sibling `aSPARK-graph` repo — genuine resource
        contention, not test logic) showed `1 failed, 193 passed` — the
        failure was `test_mcp_stdio_transport_round_trip` timing out
        waiting 10s for a stdio subprocess response, an MCP-server test
        wholly unrelated to this feature's `render.py`/`cli.py` diff.
        Re-run in isolation immediately after: **2 passed in 1.59s**. The
        two full-suite runs cited above (both fully green, no exclusions)
        bracket this flake in time, so it is not being papered over — it's
        recorded here as an environment-timing artifact, consistent with
        this project's own `mcp-server` release.md §6 note about
        subprocess-spawn overhead in this sandboxed environment, not a
        regression in the code being released.
- [x] `uv lock --check` — clean before the version bump ("Resolved 41
      packages in 31ms") and clean again after ("Resolved 41 packages in
      32ms").
- [x] Build succeeds from a clean state — `uv build --out-dir <scratch>`
      (pre-bump tree, `0.3.0`) and confirmed again structurally via
      `uv sync --extra dev` rebuilding the editable install at `0.4.0`
      after the bump: `Successfully built aspark_insights-0.3.0.tar.gz` /
      `...-0.3.0-py3-none-any.whl`, exit 0. Scratch output removed
      afterward, never left in the repo.
- [x] Working tree clean before staging, and clean again immediately after
      the release commit — `git status` → `nothing to commit, working
      tree clean` (confirmed independently, not assumed from the commit's
      exit code). Before this pass, nothing had been committed for this
      feature: `git log --oneline -5` showed `3382942` (the last
      `mcp-server` docs commit) as `HEAD`, and `git status` showed the
      full uncommitted `snapshot-report` diff — new
      `src/aspark_insights/render.py`, new `tests/test_render.py`, new
      `.spark/snapshot-report/{spec,plan,review,qa}.md`, edited `cli.py`,
      edited `tests/test_cli_stubs.py`, edited `.spark/constitution.md`
      (the `ux`-lens amendment, in scope for this commit — see §3
      Release Actions).
- [x] Confirmed the "zero breakage to other subcommands" claim behind the
      version bump myself, not on the review's say-so: `git diff
      src/aspark_insights/cli.py` (pre-commit) shows the entire diff is
      the `render` subparser (`--repo`/`--output` flags added) and
      `_cmd_render`'s body (`NotImplementedStub` raise → real
      `run_render()` call); `_cmd_build`/`_cmd_query`/`_cmd_diff`/
      `_cmd_verify`/`_cmd_serve` are untouched in the diff.
- [x] Real end-to-end verification against the actual sibling
      `/Users/andreaslottes/aSPARK-graph` (real built `.aspark-graph/
      graph.json`), on the post-bump tree, run by me: `insights build
      --repo /Users/andreaslottes/aSPARK-graph --as-of 2026-08-04
      --output <scratch>` → exit 0, real facts/metrics. `insights render
      --repo /Users/andreaslottes/aSPARK-graph --output <scratch>` → exit
      0, `{"report": "<absolute path>/.aspark-insights/report.html"}`.
      Opened the written file directly: `<tr><td>insights_version</td>
      <td>0.4.0</td></tr>` — the new version genuinely flows through a
      real render, not just the version string in `pyproject.toml`.
      `git -C aSPARK-graph status --porcelain` returned empty both before
      and after every check — the sibling repo was never written to.
      Scratch output removed afterward.

## 2. Version

**v0.4.0** — minor bump from `v0.3.0`. Justification:

- This feature turns `insights render` from a permanent
  `NotImplementedStub` (raised since `foundation`, I1) into real, working
  output — a genuine, additive, backward-compatible public-CLI-behavior
  change, not internal refactoring or a docs/config-only change. It is
  the same shape as `mcp-server`'s own `0.2.0` → `0.3.0` bump: a real new
  capability, zero breakage.
- Checked, not assumed, that nothing existing broke: confirmed the `cli.py`
  diff touches only the `render` subparser and `_cmd_render` — `build`/
  `query`/`diff`/`verify`/`serve` are all byte-for-byte unchanged in the
  diff, no flag removed, no output shape changed for any pre-existing
  subcommand. Zero new runtime dependencies (unlike `mcp-server`, which
  added `mcp>=1.12,<1.20` — this release adds none).
- Matches this project's own `CLAUDE.md` precedent: *"A version bump is a
  claim about package behavior, not a ceremony checkbox"* —
  `public-repo-polish` correctly shipped with **no** bump (docs-only,
  zero `src/`/`tests/` change); `mcp-server` correctly bumped minor (real
  new public entry point). This release is squarely in `mcp-server`'s
  category: a real capability change with a working CLI surface, so
  bumping minor is the correct application of the rule, not a reflex.
- Considered and reject **patch** (`0.3.1`): a patch bump connotes a fix
  to existing behavior; this replaces a permanent stub with working
  behavior for the first time — that's new-capability territory, not a
  fix. Considered and reject **major**: nothing existing is removed or
  changed incompatibly, and this project stays pre-1.0 (`0.x`) by its own
  established convention, where the minor component is where additive,
  backward-compatible capability changes land.
- Notable framing: this is "the last of the five original C2 subcommands"
  (`build`/`query`/`diff`/`verify`/`render`) to go from stub to real — a
  milestone worth naming in the release commit, but not on its own a
  reason to bump differently than the behavior change itself warrants.

## 3. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- `insights render` now works. Point it at a repo with a snapshot already
  built (`insights build`), and it produces a real, self-contained HTML
  report of that snapshot's facts, metrics, and provenance — one file,
  viewable fully offline in any browser, no server and no external
  fonts/scripts/styles fetched over the network. It prints the report's
  absolute path on success (`insights render --repo <path>`).
- The report shows every metric honestly: a null metric never renders as
  a blank — it shows the real reason it couldn't be computed (e.g. "no
  Story nodes found in graph"), and every computed value is shown
  alongside its sample size so you can judge how much to trust it.
- A repo with no facts yet (an empty or very early project) gets a real,
  clearly-styled "no facts recorded" notice in the report — not a bare,
  confusing empty table that looks broken.
- The report is built to be readable at a glance and on a phone: a
  summary of fact/metric/computed/null counts sits right under the
  title, headings and tables use real semantic HTML (not styled `<div>`
  soup), color is never the only signal for a "stale" warning, and the
  page adapts down to a 375px-wide screen without any sideways
  page-level scrolling.
- Every value the report displays that comes from the analyzed repo
  itself (subject IDs, metric IDs, provenance strings, and so on) is
  fully escaped before it's written into the page, so nothing in the
  underlying data — however unusual — can inject or execute markup or
  script in your browser when you open the report.

### Changed
- Nothing about how you already use `insights build`/`query`/`diff`/
  `verify`/`serve` changed — same flags, same output, same behavior.
  This release is purely additive.

### Fixed
- Not applicable this release. Two issues (a malformed-but-technically-
  valid snapshot crashing the report instead of returning a clean error;
  a metric missing its sample size showing a bare value) were found and
  fixed during `/peer-review`, before this feature — or either bug —
  ever shipped in a released version. Neither is a regression from a
  prior release, so neither belongs in a user-facing "Fixed" entry
  (matching this project's own `mcp-server` release precedent for the
  same situation).

**Explicitly NOT included in this release:** the original three-persona
(Developer/Architect/Engineering Manager) role-differentiated dashboard
concept from the backlog's I5 entry — this release ships one
single-audience static report; the multi-persona version stays reserved
for a future I5b, pending evidence a second real consumer exists. No new
CLI flags beyond `--repo`/`--output` on `render` itself. No interactivity
beyond static HTML (no expand/collapse, no client-side JS at all).

## 4. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | `pyproject.toml`/`src/aspark_insights/__init__.py`: `0.3.0` → `0.4.0`. `uv sync --extra dev` regenerated `uv.lock`'s own `aspark-insights` entry to match (clean 2-line diff, same mechanism as `mcp-server`'s own precedent). Committed locally as `7e52db4` ("feat: snapshot-report — insights render, real self-contained HTML report, v0.4.0 (I5)"). Local annotated tag `v0.4.0` created on that commit. **Pushed** with the user's explicit go. |
| PR / merge | Not opened — direct-to-`main` convention. **Pushed:** `git push origin main` → `3382942..7e52db4 main -> main`. |
| Deploy | Not applicable — CLI package, no hosted service to deploy to. |
| Tag push | **Pushed:** `git push origin v0.4.0` → `* [new tag] v0.4.0 -> v0.4.0`. |
| Post-release smoke check | **Run against the live remote, after push:** `git ls-remote origin` and `gh api repos/a-lottes/aSPARK-insights/commits/main` both confirm `7e52db4` live on GitHub. A **fresh `git clone`** of the pushed remote (not the local working copy), with a copy of the sibling `aSPARK-graph` alongside it, then `uv sync --extra dev` from that clean clone: `insights build`/`insights render` against the sibling repo succeeded, `insights_version: 0.4.0` confirmed embedded in the rendered HTML. **Opened the rendered report in a real browser** (this project's now-standard post-`/demo-day` technique) — confirmed a genuine, correctly-rendered page: 306 real facts, 8 metrics, all computed, `graph_staleness.stale: False` correctly showing no stale cue this time. Sibling repo confirmed untouched throughout. Scratch clone removed afterward. |

**Local, reversible work completed this pass (already done, nothing
further needed from the user for these):**
```
# Version bump — already applied and committed
# pyproject.toml: version = "0.3.0" -> "0.4.0"
# src/aspark_insights/__init__.py: __version__ = "0.3.0" -> "0.4.0"
uv sync --extra dev        # regenerated uv.lock's aspark-insights entry to 0.4.0
uv lock --check             # clean

# Release commit — explicit file list, never -A/.
git add pyproject.toml uv.lock src/aspark_insights/__init__.py \
  src/aspark_insights/cli.py src/aspark_insights/render.py \
  tests/test_cli_stubs.py tests/test_render.py \
  .spark/constitution.md \
  .spark/snapshot-report/spec.md .spark/snapshot-report/plan.md \
  .spark/snapshot-report/review.md .spark/snapshot-report/qa.md
git commit -m "feat: snapshot-report — insights render, real self-contained HTML report, v0.4.0 (I5)" ...
# -> 7e52db4

git tag -a v0.4.0 -m "v0.4.0 — snapshot-report (I5): insights render, real self-contained HTML report"
```

**Executed — with the user's explicit go, given in this conversation:**
```
git push origin main        # 3382942..7e52db4  main -> main
git push origin v0.4.0      # * [new tag]         v0.4.0 -> v0.4.0
```
Both ran clean. Post-push smoke check (above) confirms `7e52db4`/`v0.4.0`
are live on `github.com/a-lottes/aSPARK-insights` and that a fresh clone of
that exact remote state builds, renders, and displays correctly in a real
browser against the real sibling repo.

## 5. Rollback Path

`7e52db4`/`v0.4.0` are now pushed and public on `main` — this is the live
rollback path, not the pre-push hypothetical:

- **To undo the commit, keeping a paper trail:** `git revert 7e52db4` on
  `main`, then `git push origin main` — the standard path on a public
  branch others may have already fetched. **Never `push --force` on
  `main`.**
- **To retract the tag** (only if the release is genuinely wrong, not for
  a routine follow-up fix): `git push origin :refs/tags/v0.4.0` removes
  the remote tag.
- **Not on PyPI** — no `uv publish` step exists or is planned for this
  release, matching `mcp-server`'s own precedent; the only place `v0.4.0`
  lives is this git remote.
- **No deploy to roll back** — CLI package; "rollback" here means the git
  commit/tag, not a running service.
- **A local-only, pre-push rollback is no longer available** — `7e52db4`
  is now the tip of the public `main` branch. Any fix goes forward
  (`git revert` + a new commit), not backward.

## 6. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - This is this project's **first genuinely hands-on `/demo-day`** —
    every prior feature (`foundation`, `traceability-metrics`,
    `public-repo-polish`, `mcp-server`) was headless, either N/A by the
    constitution or explicitly overridden. The value it added over
    `/peer-review`'s source-level read was concrete, not theoretical: the
    QA Tester independently *measured* contrast ratios instead of trusting
    the reviewer's flagged-color note (finding the real 2.85:1 gridline
    number, B1), *mechanically* confirmed byte-offset section ordering and
    a JS-verified 375px zero-horizontal-scroll instead of eyeballing a
    screenshot, and — most tellingly — built their **own** hand-crafted
    hostile snapshot to re-derive the F1 security fix independently rather
    than trust the review's account of it. A source read can prove a fix
    exists in the code; only a live re-derivation proves it actually
    closes the hole an attacker would try. Worth keeping as the bar for
    "QA passed" going forward, not just for UI features.
  - The Reviewer's re-review approach (§6.1 of `review.md`) — trying to
    actively **route around** the F1 fix (list-of-non-dicts, `None`
    elements, an int `metric_id`, a null `provenance`, a non-dict
    `graph_staleness`) rather than just confirming the patch's diff
    "looks right" — is exactly the adversarial posture that makes a
    re-review meaningful. A re-review that only checks "is the described
    fix present" is much weaker than one that tries to break it again with
    different inputs than the original repro used.
  - The `ux` lens's mid-session activation via `/charter` (this project's
    first UI-facing feature) worked cleanly: it was grounded in the
    *actual* scoped-down I5 deliverable (single-audience static HTML, no
    framework/routing/auth) rather than a generic "this is a web thing now"
    relabeling, it correctly left the project `type` as `cli`+`library`
    rather than reclassifying to `web-app`, and it replaced the
    Accessibility quality bar's placeholder `N/A` with concrete,
    falsifiable criteria (semantic HTML, measured contrast, keyboard
    operability, explicitly-out-of-scope ARIA-live) that QA then actually
    exercised. The elevated-load flag (4 lenses active) it triggered didn't
    visibly slow anything down this cycle, but it's worth watching whether
    a 5th lens someday genuinely strains a single review/QA pass.
  - The security fix (F1) is, again, the same *class* of bug this project
    has now caught three-plus cycles running — a valid-JSON-but-wrong-shape
    input hitting an unguarded operation — but this is the first time it
    was **QA-independently re-derived**, not just review-verified. That's
    a stronger form of evidence than any prior cycle produced for the same
    bug class.

- **What we'd do differently:**
  - The one flaky-test surprise this pass (`test_mcp_stdio_transport_round_
    trip` timing out at 10s during a background suite run while I was
    concurrently doing live subprocess-heavy CLI work) reinforces the
    `mcp-server` release's own §6 note about this sandboxed environment's
    subprocess-spawn sensitivity — but this time it showed up as an
    intermittent single-test flake rather than a uniformly slow suite.
    Worth explicitly not running heavy concurrent subprocess work (e.g. a
    real end-to-end sibling-repo build/render check) *while* a full-suite
    run is also in flight in future `/go-live` passes — sequence them,
    don't parallelize, even though it costs a few extra minutes of wall
    time.
  - Nothing about the F2 Nit's "confirmed unreachable today" framing was
    revisited this pass — it's still true (all 12 `MetricValue`
    constructions pass `n`), but as more metrics get added in future
    increments, it's worth eventually asking whether `n` should become a
    non-optional field on `MetricValue` itself (a type-level guarantee)
    rather than an invariant re-confirmed by inspection each time — not
    urgent, but a candidate to name explicitly next time `MetricValue`
    itself changes.

- **Patterns worth reusing:**
  - **Adversarial re-review** (actively trying to route around a fix with
    different malformed inputs than the original repro, not just
    confirming the described fix is present) is a concrete, reusable
    technique worth naming explicitly as this project's re-review bar,
    not just something that happened to occur this cycle.
  - **QA independently re-deriving a security fix with its own
    hand-crafted hostile input**, rather than trusting the review's
    account, is the browser-QA-era equivalent of the same discipline —
    both are candidates for this project's `CLAUDE.md` as a named
    practice ("never take a fix on the reviewer's/tester's predecessor's
    word — reproduce it yourself with your own input").
  - **Measuring, not eyeballing, visual-surface claims** (contrast
    ratios via `getComputedStyle`, viewport scroll via
    `scrollWidth`/`clientWidth`, section order via byte offsets in
    `outerHTML`) is now this project's established technique for any
    future UI-facing QA pass, alongside the existing "render Markdown
    through GitHub's real API" technique from `public-repo-polish`.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time (fresh test run — 194
      passed pre-bump, 194 passed post-bump, one disclosed unrelated flake
      bracketed by both green runs and explained, not hidden; `uv lock
      --check` clean before and after; clean build from scratch; clean
      working tree before staging and again after the commit — all
      re-verified on the actual release commit `7e52db4`, not copied from
      `review.md`/`qa.md`)
- [x] Changelog written in user-facing language, no commit hashes, no
      ticket IDs, no internal jargon
- [x] Release actions executed and verified: commit `7e52db4` and tag
      `v0.4.0` created, then pushed to `origin` on the user's explicit go.
      Post-push smoke check confirms both are live on GitHub and that a
      fresh clone of that exact remote state builds, renders, and
      displays correctly in a real browser against the real sibling repo.
- [x] Rollback path written and concretely actionable (§5), reflecting the
      now-pushed, now-public state — forward-only via `git revert`, no
      history rewrite on `main`.
- [x] Learnings recorded — what went well (the first real `/demo-day`'s
      concrete added value, the adversarial re-review posture, the `ux`
      lens's clean mid-session activation), what we'd do differently
      (don't run heavy concurrent subprocess work alongside a full-suite
      run; the `MetricValue.n` optionality question to revisit later),
      reusable patterns flagged as `CLAUDE.md` candidates (adversarial
      re-review, independently re-deriving security fixes, measuring not
      eyeballing visual claims).
- [x] Status set to `released`.
