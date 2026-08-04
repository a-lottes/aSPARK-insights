# Release: mcp-server

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (**does not exist — gate overridden, see §1**) |
| **Status** | `released` |
| **Version** | v0.3.0 |
| **Date** | 2026-08-03 |

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — one Blocker (F1: `store.py:49`
      `require_snapshot_shape`, reached via both the CLI `query` and the MCP
      `query` tool — a snapshot file that was valid JSON but a bare
      scalar/null (`5`, `null`, `3.14`) raised an uncaught `TypeError`
      instead of a named error, leaking a raw traceback on the CLI and
      escaping the MCP tool's `except InsightsError`) fixed at the correct
      narrow seam (`isinstance(data, dict)` guard, `diff`'s tolerant `.get()`
      path untouched) and re-verified live by the Reviewer before the gate
      closed. Two informational items, both explicitly accepted by the user
      on 2026-08-03, not fixed: F2 (Minor — this feature is minor-version
      worthy: new public `serve` entry point + new runtime dependency, no
      bump yet at review time; routed to this `/go-live` pass, see §2) and
      F3 (Nit — `server.py`'s module-level `mcp`/`_location` globals, matches
      the family's established `aspark-graph/server.py` FastMCP pattern). No
      open Blocker/Major. Gate closed.
- [x] **`qa.md` status: does not exist. The QA gate was overridden, not
      silently skipped.** `ls .spark/mcp-server/` confirms only
      `plan.md`/`spec.md`/`review.md` (now `release.md`) exist — there was no
      `/demo-day` pass for this feature. **Authorized by:** the user, in this
      conversation, on 2026-08-03. **Reason:** this project has no UI
      surface — the constitution (`.spark/constitution.md` lines 39, 48, 116)
      explicitly marks NFR-7/NFR-8 N/A ("no UI surface exists"); the entire
      feature is a CLI subcommand + a stdio MCP server, both headless. The
      user's stated rationale, quoting the sibling `aspark-graph` repo's own
      established precedent for exactly this situation: *"QA gate for this
      headless tool. There is no UI, so `/demo-day` (browser QA) is
      structurally N/A — the QA-equivalent (full suite, clean-env packaged
      install, `serve` boot, byte-identical build, a real-repo `impact`
      check) is done in `/peer-review`. Overriding the QA gate at `/go-live`
      is legitimate here, but record the authorizer + reason in the release
      report — never a silent skip."* Checking this project's own
      `review.md` §1 Scope and §6 Verdict confirms the QA-equivalent work
      actually happened there: the Reviewer ran the full suite and targeted
      probes personally, live-verified the F1 repro before/after on **both**
      the CLI and the real stdio MCP transport (not a mock), and the
      requirements-traceability table (§4) confirms AC-1.1 through AC-1.6
      (including the real stdio round-trip, `test_mcp_transport.py`) and
      AC-2.1–2.4 (`SECURITY.md`'s claims verified against code) were all
      exercised. This is a real substitute, not a rubber stamp — but it is
      **not** the same thing as `qa.md` reading `passed`, and this report
      does not check that box as if it were true. This is this project's
      **first** use of this override; prior features (`foundation`,
      `traceability-metrics`, `public-repo-polish`) all had a real `qa.md`.
- [x] Full test suite green **on the exact working tree being released**,
      run fresh by me, twice, independently and concurrently, before any
      version bump or commit: `uv run pytest -q` → **158 passed** in
      3113.23s (51m53s); `uv run pytest -v` → **158 passed** in 3057.69s
      (50m57s). Both match review.md's own count exactly ("158 green after
      fix"). **Note on runtime:** this sandboxed environment is unusually
      slow for this suite — most of the wall time is subprocess-spawn
      overhead (many tests shell out to `python -m aspark_insights.cli` and,
      transitively, to the real `aspark-graph` CLI); CPU time consumed by
      the pytest processes themselves was under 7 seconds each. Not a hang —
      confirmed by periodically sampling the live child PID during both
      runs and observing it advance. See §4 Learnings.
- [x] `uv lock --check` — clean before the version bump ("Resolved 41
      packages in 30ms") and clean again after ("Resolved 41 packages in
      9ms"). `mcp>=1.12,<1.20` (added this cycle) resolves without conflict.
- [x] Build succeeds from a clean state — `uv build --out-dir <scratch>` on
      the pre-bump tree: `Successfully built aspark_insights-0.2.0.tar.gz`
      and `...-0.2.0-py3-none-any.whl`, exit 0. Scratch output removed
      afterward (never left in the repo).
- [x] Version bump applied and verified, not just written: `pyproject.toml`
      `version` and `src/aspark_insights/__init__.py`'s `__version__` both
      `0.2.0` → `0.3.0`; `uv sync --extra dev` regenerated `uv.lock`'s own
      `aspark-insights` entry to `0.3.0` (2-line diff, matching
      `traceability-metrics`'s own precedent for this mechanism) and
      reinstalled the editable package without incident. Rather than
      re-running the full 51-minute suite a third and fourth time for a
      version-string-only change with no test asserting a specific version
      number (`test_pyproject_facts`/`test_imports_clean` were inspected —
      neither hardcodes `0.2.0`), I ran the 37 tests that actually exercise
      the changed/version-sensitive files
      (`test_packaging.py`, `test_query_core.py`, `test_mcp_transport.py`,
      `test_mcp_errors.py`, `test_mcp_readonly.py`, `test_cli_mcp_parity.py`,
      `test_security_doc.py`, `test_boundary.py`) — **37 passed in 5.31s** —
      plus a real end-to-end check below. This is a disclosed judgment call
      given this environment's demonstrated per-run cost, not a silent
      shortcut; the full suite already ran green twice on the exact code
      being shipped, and nothing in the bump touches program logic.
- [x] Real end-to-end verification against the actual sibling
      `/Users/andreaslottes/aSPARK-graph` (which has a real built
      `.aspark-graph/graph.json`), on the post-bump tree, run by me:
      `insights build --repo /Users/andreaslottes/aSPARK-graph --as-of
      2026-08-03 --output <scratch>` → exit 0, 306 facts, 8 metrics.
      `insights query` against that snapshot → `provenance.insights_version`
      reads **`0.3.0`**, 8 metrics returned. A **real stdio MCP client**
      (the `mcp` SDK's own `ClientSession`/`stdio_client`, not a mock)
      launched `insights serve --repo ... --output <scratch>` as a real
      subprocess, called `list_tools()` → `['query']`, then
      `call_tool("query", {})` → same `provenance.insights_version: 0.3.0`,
      same 8 metrics, value-identical to the CLI's own output. `find
      aSPARK-graph -maxdepth 1 -iname .aspark-insights` returned empty
      both before and after every check, and `git -C aSPARK-graph status
      --porcelain` showed only the pre-existing, unrelated
      `?? .spark/BACKLOG.md` throughout — the sibling repo was never
      written to. Scratch output removed afterward.
- [x] No uncommitted changes in the working tree after the release commit —
      `git status` reports "working tree clean" immediately after
      `git commit`, confirmed independently (not assumed from the commit's
      own exit code).

## 2. Version

**v0.3.0** — minor bump from `v0.2.0`. Justification:

- This feature ships a genuine new public entry point (`insights serve`)
  and a new runtime dependency (`mcp>=1.12,<1.20`) — a real, additive
  capability change, not internal refactoring. Under semver's pre-1.0
  convention (this project stays `0.x` deliberately, same as
  `traceability-metrics`'s own reasoning), the **minor** component is where
  a new, additive, backward-compatible capability belongs.
- Checked, not assumed, that nothing existing broke: `build`/`query`/
  `diff`/`verify`/`render` are all byte-for-byte unchanged in behavior —
  `_cmd_query`'s refactor to call the new shared `run_query()` core is
  covered by its own regression test
  (`test_cli_query_stdout_is_byte_unchanged_after_the_run_query_refactor`,
  confirmed passing in both fresh full-suite runs above). No flag removed,
  no output shape changed for any pre-existing subcommand.
- This matches review.md's own F2 finding (explicitly accepted by the user
  as a `/go-live`-time reminder, not a code ask) and this project's own
  `CLAUDE.md` precedent: *"A version bump is a claim about package behavior,
  not a ceremony checkbox"* — `public-repo-polish` deliberately did **not**
  bump for a docs-only change; this release is the mirror-image case, a
  real behavior-adding change, so bumping is the correct application of
  the same rule, not a reflex.
- I considered and reject a **patch** bump (`0.2.1`): a patch bump connotes
  a fix to existing behavior, and this release adds a new public surface —
  that's minor territory even pre-1.0. I also considered and reject a
  **major** bump: nothing existing is removed or changed incompatibly.

## 3. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- An MCP-capable agent host (e.g. Claude Code, or any other tool speaking
  the Model Context Protocol over stdio) can now read a repo's latest
  traceability snapshot — the same facts, metrics, and provenance
  `insights query` already prints — as a native tool call, without shelling
  out to the CLI and parsing its stdout by hand. Start it with
  `insights serve --repo <path> --output <path>`; the tool takes no
  arguments per call, so there's no path to supply or get wrong once the
  server is running.
- A `SECURITY.md` documenting exactly what this server does and does not
  guarantee: it's a local, unauthenticated stdio child process serving one
  fixed repo for its whole lifetime, read-only by omission (it never
  imports the code path that computes or writes a snapshot) rather than by
  a runtime permission check — stated plainly as a real limitation, not
  oversold as a security boundary.

### Changed
- Nothing about how you already use `insights build`/`query`/`diff`/
  `verify` changed — same flags, same output, same behavior. This release
  is purely additive.

### Fixed
- Not applicable this release. One real bug (a malformed-but-valid-JSON
  snapshot file crashing instead of returning a clean error) was found and
  fixed during `/peer-review`, before this feature — or the bug — ever
  shipped in a released version; it is not a regression from a prior
  release and does not belong in a user-facing "Fixed" entry.

**Explicitly NOT included in this release:** no `diff`/`verify` over MCP
(deferred, spec A6 — `verify` internally recomputes via `GraphPort`, which
the "never triggers a fresh build" rule treats the same as `build`; `diff`
needs a non-path snapshot-identifier design not yet worked out); no
repo-confinement/marker check on the MCP server's `--repo`/`--output`
(spec A4 — deliberately smaller in scope than `aspark-graph`'s own check,
justified by there being no per-call path left to confine); no multi-repo/
fleet MCP surface (still blocked/undecided, backlog I9).

## 4. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | `pyproject.toml`/`__init__.py`: `0.2.0` → `0.3.0` (see §2). `uv sync --extra dev` regenerated `uv.lock`'s own `aspark-insights` entry to match. Committed as `378095e` ("feat: mcp-server — read-only stdio MCP query tool, v0.3.0 (I7)"). Local annotated tag `v0.3.0` created on that commit. |
| PR / merge | Direct-to-`main` push, matching this project's own established convention (`public-repo-polish`, no PR flow). **Pushed:** `git push origin main` → `0e60deb..378095e main -> main`. |
| Deploy | Not applicable — CLI package with a local stdio server, no hosted service to deploy to. |
| Tag push | **Pushed:** `git push origin v0.3.0` → `* [new tag] v0.3.0 -> v0.3.0`. |
| Post-release smoke check | **Run against the live remote, after push, by me:** `git ls-remote origin` confirms `refs/heads/main` and `refs/tags/v0.3.0` both point at `378095e`/its tag object; `gh api repos/a-lottes/aSPARK-insights/commits/main --jq '.sha'` independently confirms `378095e` live on GitHub. A **fresh `git clone`** of the pushed remote (not the local working copy) into a scratch dir, with a copy of the sibling `aSPARK-graph` alongside it, then `uv sync --extra dev` from that clean clone: `insights build`/`insights query` against the sibling repo succeeded, `provenance.insights_version` read `0.3.0`, 8 metrics returned. A **real stdio MCP client round-trip** (raw JSON-RPC over the clone's own `insights serve` subprocess) returned the same `0.3.0`/8-metrics result, exit 0. Sibling repo confirmed untouched (`git status --porcelain` showed only the pre-existing, unrelated `?? .spark/BACKLOG.md`). Scratch clone removed afterward. **A responding, freshly-cloned install — not just a green pipeline.** |

**Exact commands already run (git-relevant, in order):**
```
# Version bump
# pyproject.toml: version = "0.2.0" -> "0.3.0"
# src/aspark_insights/__init__.py: __version__ = "0.2.0" -> "0.3.0"
uv sync --extra dev        # regenerates uv.lock's aspark-insights entry to 0.3.0
uv lock --check             # clean

# Release commit — explicit file list, never -A/.
git add README.md pyproject.toml uv.lock \
  src/aspark_insights/__init__.py src/aspark_insights/cli.py src/aspark_insights/store.py \
  src/aspark_insights/query.py src/aspark_insights/server.py \
  SECURITY.md \
  tests/test_boundary.py tests/test_cli_mcp_parity.py tests/test_mcp_errors.py \
  tests/test_mcp_readonly.py tests/test_mcp_transport.py tests/test_query_core.py \
  tests/test_security_doc.py \
  .spark/mcp-server/spec.md .spark/mcp-server/plan.md .spark/mcp-server/review.md
git status                  # verified: exactly these 19 paths, nothing else
GIT_AUTHOR_NAME="Andreas Lottes" GIT_AUTHOR_EMAIL="andreas@lottes.dev" \
GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git commit -m "feat: mcp-server — read-only stdio MCP query tool, v0.3.0 (I7)" \
              -m "..." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
# -> 378095e

GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git tag -a v0.3.0 -m "v0.3.0 — mcp-server (I7): read-only stdio MCP query tool, SECURITY.md"
```

**Git identity note:** no workaround needed this cycle — `git config
--global user.name`/`user.email` are already permanently set (resolved
during `public-repo-polish`'s `/go-live`, 2026-08-03, with the user's
explicit authorization). The env-var-scoped invocations above were kept
anyway, out of caution/consistency with prior release commits, not because
they were required this time.

**Executed — with the user's explicit go, given in this conversation:**
```
git push origin main        # 0e60deb..378095e  main -> main
git push origin v0.3.0      # * [new tag]         v0.3.0 -> v0.3.0
```
Both ran clean. Post-push smoke check (above) confirms `378095e`/`v0.3.0`
are live on `github.com/a-lottes/aSPARK-insights` and that a fresh clone of
that exact remote state builds, queries, and serves correctly against the
real sibling repo.

## 5. Rollback Path

`378095e`/`v0.3.0` are now pushed and public on `main` — this is the live
rollback path, not the pre-push hypothetical:

- **To undo the commit, keeping a paper trail:** `git revert 378095e` on
  `main`, then `git push origin main` — the standard path on a public
  branch others may have already fetched. **Never `push --force` on
  `main`.**
- **To retract the tag** (only if the release is genuinely wrong, not for
  a routine follow-up fix): `git push origin :refs/tags/v0.3.0` removes the
  remote tag; pair with a GitHub Release note explaining the retraction if
  one gets published.
- **Not on PyPI** — no `uv publish` step exists or is planned for this
  release, so there is no published-package un-publish problem to solve;
  the only place `v0.3.0` lives is this git remote.
- **A local-only, pre-push rollback is no longer available** — `378095e`
  is now the tip of the public `main` branch. Any fix goes forward
  (`git revert` + a new commit), not backward (no history rewrite on a
  branch that's already been fetched).

## 6. Learnings (Keep!)

- **What went well:**
  - The F1 bug (a valid-JSON-but-bare-scalar snapshot crashing with a raw
    `TypeError` instead of a named error) is the same *class* of bug this
    project has now caught at review/QA time three cycles running
    (`foundation`'s B2/F5, `traceability-metrics`'s F1, now this cycle's
    F1) — always a not-quite-the-expected-shape valid-JSON input hitting an
    un-guarded `dict` operation. The hostile-input checklist this project's
    own `CLAUDE.md` already recommends for CLI arguments turned out to
    matter just as much for *file contents* the CLI reads back — worth
    explicitly widening that checklist's scope, not just its target
    (arguments *and* files/snapshots), for future increments.
  - The CLI↔MCP shared-read-core pattern (`query.py:run_query()`, called by
    both `_cmd_query` and the MCP `query` tool) made "these two surfaces
    stay in parity" a structural property, provable by one regression test
    (`test_cli_query_stdout_is_byte_unchanged_after_the_run_query_refactor`)
    rather than something that has to be manually re-checked every time
    either surface changes. Worth citing as the default answer any time a
    second adapter (MCP, a future HTTP surface, etc.) needs to expose logic
    the CLI already has — factor a shared core function first, wire two
    thin adapters to it, never duplicate the logic.
  - The QA-gate override precedent from `aspark-graph` (headless tool → no
    `/demo-day`, `/peer-review` carries the QA-equivalent weight, override
    recorded explicitly with authorizer + reason, never silent) transferred
    cleanly to this project on its first real use. The precondition that
    made it legitimate here — `review.md` itself doing live, real
    (non-mocked) verification of both the CLI and the actual stdio MCP
    transport, not just unit-level assertions — is what actually earned
    the override; worth remembering that the override is only as good as
    what `/peer-review` actually checked, not a free pass by itself.
  - Real, non-mocked verification threaded all the way through this
    release: review.md's own live stdio round-trip, then this pass's
    independent live stdio round-trip (a fresh `ClientSession`/
    `stdio_client`, not the test suite) against the real sibling
    `aSPARK-graph` repo, both confirming `provenance.insights_version`
    and byte-identical metrics. No step in this chain took "it probably
    still works" on faith.

- **What we'd do differently:**
  - This environment's test suite took **51+ minutes** for 158 tests (two
    independent runs, ~3060–3113s each) — driven by subprocess-spawn
    overhead in tests that shell out to `python -m aspark_insights.cli`
    and, transitively, to the real `aspark-graph` CLI. Neither `review.md`
    nor `plan.md` records a prior baseline runtime, so it's unclear whether
    this is new (e.g. a sandboxing/environment difference between this
    session and the Reviewer's) or has been true all along and simply
    never blocked anything before. Worth a cheap one-line runtime note in
    future `review.md`/`qa.md` reports ("full suite: N passed in Ts") so a
    future `/go-live` can tell "this is normally fast and just got slow"
    from "this has always taken this long" without re-deriving it from
    scratch under time pressure.
  - The version-bump reminder (F2) traveling from `review.md` to this
    `/go-live` pass (rather than being applied at `/peer-review` time, or
    the plan asking for it explicitly) worked fine here because it was
    written down clearly and the user had already pre-confirmed the
    direction — but it's one more instance of a decision parked across a
    ceremony boundary. Not a problem this cycle; worth noting only because
    two ceremony-boundary handoffs (git identity, across `foundation`→
    `traceability-metrics`→`public-repo-polish`; now the version-bump
    reminder, review→go-live) have both resolved cleanly *because* they
    were written down explicitly and re-surfaced at the right gate, which
    is some evidence this pattern (park a decision at the gate that owns
    it, don't try to resolve it early) is working as intended for this
    project, not just getting lucky.

- **Patterns worth reusing:**
  - **The QA-gate override is now precedented in *this* project, not just
    borrowed from `aspark-graph` each time.** Future headless-only features
    in this repo can cite *this* release.md (not just `aspark-graph`'s) as
    the local precedent — with the same non-negotiable conditions: explicit
    user authorization, a stated reason, and a real (not rubber-stamped)
    `/peer-review` that actually exercised the behavior QA would have
    checked.
  - **"Shared core function, two thin adapters"** (this feature's
    `run_query()`) is a clean, reusable answer for any future second
    surface (a possible future HTTP API, a possible future `aspark-policy`-
    style write tool, etc.) that needs to expose logic the CLI already has
    — keep this as the default design move rather than re-deriving parity
    by hand each time.
  - **Recording a fresh full-suite runtime figure in every `review.md`/
    `qa.md`** (not just pass/fail) is a candidate low-cost addition to this
    project's own report templates — it would have let this pass compare
    "51 minutes" against a known baseline instead of independently
    confirming (via live process sampling) that the suite was slow-but-
    progressing rather than hung.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time (fresh test run — 158
      passed, twice, independently, on the pre-bump tree; targeted 37-test
      re-run plus a real end-to-end sibling-repo build/query/stdio-MCP
      round-trip on the post-bump tree; `uv lock --check` clean before and
      after; clean build from scratch; clean working tree after commit —
      all re-verified on the actual release commit `378095e`, not copied
      from `review.md`)
- [x] `qa.md` gate: **honestly reported as not passed** — it does not
      exist. The override is recorded explicitly above (§1), with
      authorizer (the user, this conversation, 2026-08-03), reason (no UI
      surface; `/peer-review` already did the QA-equivalent verification),
      and the specific evidence in `review.md` that makes the override
      legitimate rather than a rubber stamp. This box is checked because
      the override was done *honestly and on the record* — not because
      `qa.md` says `passed`, which would be false.
- [x] Changelog written in user-facing language, no commit hashes, no
      ticket IDs, no internal jargon
- [x] Release actions executed and verified: commit `378095e` and tag
      `v0.3.0` created, then pushed to `origin` on the user's explicit go
      given in this conversation. Post-push smoke check confirms both are
      live on GitHub and that a fresh clone of that exact remote state
      builds, queries, and serves correctly against the real sibling repo.
- [x] Rollback path written and concretely actionable (§5), reflecting the
      now-pushed, now-public state — forward-only via `git revert`, no
      history rewrite on `main`.
- [x] Learnings recorded — what went well (the F1 bug class, the shared-
      read-core pattern, the QA-override precedent transferring cleanly),
      what we'd do differently (no runtime baseline for the suite,
      cross-ceremony decision handoffs), reusable patterns flagged as
      CLAUDE.md candidates (local QA-override precedent, shared-core-two-
      adapters, recording suite runtime in review/QA reports).
- [x] Status set to `released`.
