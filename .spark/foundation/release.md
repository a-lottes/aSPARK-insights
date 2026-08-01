# Release: foundation

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.1.0 |
| **Date** | 2026-07-31 |

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — 3 rounds, all findings (F1, F2, F3, F5) fixed and
      re-verified by re-execution; F4 (unreachable dead-code branch) accepted as-is by user
      decision. Gate closed.
- [x] `qa.md` status is `passed` — 3 rounds of hands-on CLI testing; all findings (B1–B5)
      closed and independently re-verified live; B6 (argparse exit-2 on pre-dispatch errors)
      accepted as informational. Gate closed.
- [x] Full test suite green on the release commit — re-ran myself, fresh, twice (once before
      committing, once after touching `.gitignore`): `uv run pytest -v` → **80 passed** both
      times. `uv lock --check` → exit 0 both times.
- [x] Build succeeds from a clean state — `uv sync --extra dev` resolved cleanly (41 resolved,
      39 checked); `uv build` produced `dist/aspark_insights-0.1.0.tar.gz` and a wheel with no
      errors (artifacts deleted afterward — gitignored, not part of the commit).
- [x] No uncommitted changes in the working tree — `git status` shows "nothing to commit,
      working tree clean" after the release commit, and again after the post-release smoke
      check (nothing written to the repo itself; all builds during this session targeted the
      sibling repo with `--output` redirected to a scratch dir).
- [x] Real end-to-end build re-run against the actual sibling repo (not a fixture): `insights
      build --repo /Users/andreaslottes/aSPARK-graph --output <scratch>` → exit 0, valid
      `sort_keys` JSON, and `find /Users/andreaslottes/aSPARK-graph -maxdepth 1 -iname
      .aspark-insights` came back empty both before and after — sibling repo confirmed
      untouched.

**One staging-hygiene finding, caught and corrected during this pass (not a code issue):**
`git add -A` initially staged `.claude/scheduled_tasks.lock` and `.claude/settings.local.json`
— local Claude Code session/tool state (a PID+session-ID lock file and local permission
settings), not project source, and not something any human author would want in a public git
history. Neither file was in the caller's explicit exclusion list, but it failed the "eyeball
what's included" check. I unstaged both, added `.claude/` to `.gitignore`, confirmed
`test_gitignore_excludes_derived_state_not_spark` still passes (it only asserts
`.aspark-insights/` present and `.spark` absent as substrings — unaffected), re-ran the full
suite (still 80 passed), and re-staged before committing. Flagging this explicitly since it's
a judgment call outside the pre-approved exclusion list.

**Git identity note:** no `user.name`/`user.email` was configured anywhere on this machine
(local or global — `git config --list --show-origin` showed neither). Per the hard rule
"NEVER update the git config," I did not run `git config user.name/email` (not even
locally). Instead I set `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_NAME`/
`GIT_COMMITTER_EMAIL` as environment variables scoped to the single `git commit`/`git tag`
invocations only — no config file was touched. Identity used: `Andreas Lottes
<andreas@lottes.dev>`, matching `pyproject.toml`'s `authors` field and the known user email.
Flagging this so the human user can confirm this identity is what they want attached to the
repo's commit history going forward (and configure it persistently themselves, since I
deliberately did not).

## 2. Version

**v0.1.0** — first release, no bump (there is nothing to bump from). Justification:

- This is the literal first commit this repo will ever have; semver's own convention for
  "initial development" is `0.x.y`, and `0.1.0` — "first working release, expect breaking
  changes" — fits exactly: real metrics (I2), dashboards (I5), and policy resolution (I8) are
  all still to come, and the spec itself frames this feature as scaffolding for those, not a
  stable 1.0 surface.
- Matches the value already committed to `pyproject.toml` (`version = "0.1.0"`) — no dispute
  to resolve.
- Matches family precedent: per `.spark/BACKLOG.md` §2, sibling `aspark-policy` is itself at
  `v0.1.0` in its early phase; `aspark-graph` (now `v0.7.0`) and `aSPARK` Core (`v0.3.1`) both
  presumably started the same way. No family-wide versioning scheme document was found beyond
  this local precedent — defaulting to semver, as instructed, is consistent with what the
  siblings already do.
- Bump level: N/A — this is the baseline, not a bump.

## 3. Changelog

<!-- Next-developer-facing language, since the spec's own Target Users section (§2) says
     there is no external end user yet for this feature. -->

### Added
- A new installable package, `aspark-insights`, on the family's standard Python stack
  (`uv`, `hatchling`, Python ≥3.11) — a fresh clone can `uv sync` and get a working,
  reproducible environment with no dependency drift.
- A single, well-defined seam (`GraphPort`) to the sibling `aspark-graph` project, with a CLI
  adapter and a version-pinned library adapter — nothing else in the codebase reads the
  graph's file format or internals directly, so that coupling stays contained and its
  eventual retirement stays visible in every output.
- Five command-line subcommands (`build`, `query`, `render`, `diff`, `verify`), all producing
  consistent JSON output and consistent exit codes, so future capabilities have a settled
  shape to slot into rather than inventing their own conventions each time.
- `insights build --as-of <date>` reads a graph and produces a sealed, self-documenting
  snapshot — a JSON file that always records what it was measured against, what date it
  represents, and how it was produced, so a number can be explained later without re-running
  anything.
- A hard guarantee that building the same inputs always produces byte-identical output —
  checked automatically on every commit going forward, so a silent, non-reproducible change
  to how a snapshot is built would be caught immediately rather than surfacing later as a
  puzzling wrong number.
- Input validation on the snapshot date (`--as-of`): a malformed or maliciously crafted value
  is now rejected outright with a clear error, rather than being usable to make the tool write
  a file somewhere unintended.
- A metric registry mechanism ready for real metric definitions to be added later, without
  needing to redesign how metrics are declared or looked up — ships with zero real metrics
  in this release.
- Every command fails the same way when something goes wrong: a clear, structured error
  message and a non-zero exit code — never a raw internal crash dump, on any command, on any
  malformed input tried so far.

### Changed
- Not applicable — this is the first release.

### Fixed
- Not applicable in the traditional sense — nothing shipped before this. However, worth
  naming: several issues that would otherwise have shipped in this very first release were
  found and closed before it ever went out, including a way to make the tool write a file to
  an arbitrary location via a crafted input, two situations where malformed input produced a
  raw crash instead of a clear error, an ordering bug that could make "read back the last
  result" return the wrong one, and a case where the tool would silently create files inside
  a different, unrelated project folder without warning. None of these ever reached a real
  user — full details are in `.spark/foundation/review.md` and `.spark/foundation/qa.md`.

**Explicitly NOT included in this release** (by design, future increments): no real metric
definitions (traceability, flow, architecture-health, debt, or DORA-related numbers) — the
registry mechanism ships empty; no dashboards or HTML rendering (`render` is an intentional,
loud stub that always fails clearly rather than silently producing nothing); no policy
resolution (the policy seam exists but always reports "not available yet," honestly, never a
fabricated result).

## 4. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | `pyproject.toml` already at `0.1.0` (no bump needed — first release). Ran `git init`; staged everything via `git add -A`, caught and excluded local `.claude/` session state (see Pre-Flight notes), re-staged. Committed as root commit `86b2beb` ("feat: foundation — package skeleton, GraphPort, CLI, determinism canary (I1)"). Created local annotated tag `v0.1.0` on that commit. **Local only — no push.** |
| PR / merge | Not applicable — there is no remote configured and this is the first commit; there is nothing to merge into. |
| Deploy | Not applicable — this is a CLI package, not a service; there is nowhere to "deploy" it to. (A future increment may add PyPI/registry publishing — not in scope here.) |
| Post-release smoke check | Ran after the commit, against the actual committed state: `insights build --help` → usage text, exit 0. `insights build --repo /Users/andreaslottes/aSPARK-graph --output <scratch>` → exit 0, valid sealed snapshot JSON, sibling repo confirmed untouched (`.aspark-insights/` absent in it, before and after). `git status` in this repo confirmed clean after both checks — the smoke check itself didn't dirty the release commit. |

**Exact commands run (in order, git-relevant excerpt):**
```
git init
git add -A
git status                 # caught .claude/ leak
git reset .claude/
# appended ".claude/" to .gitignore
git add -A
git status                 # verified clean staging: no .venv/, __pycache__/,
                            # .pytest_cache/, .aspark-insights/, .DS_Store, .claude/
GIT_AUTHOR_NAME="Andreas Lottes" GIT_AUTHOR_EMAIL="andreas@lottes.dev" \
GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git commit -m "feat: foundation — package skeleton, GraphPort, CLI, determinism canary (I1)" \
              -m "..." -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
GIT_COMMITTER_NAME="Andreas Lottes" GIT_COMMITTER_EMAIL="andreas@lottes.dev" \
  git tag -a v0.1.0 -m "v0.1.0 — foundation (I1): package skeleton, GraphPort, CLI skeleton, determinism canary"
```

**Pending — outward-facing, requires explicit human go (none currently applicable):** there is
no remote to push to, no PR to open, and no deploy target. If/when a remote is added later,
the outstanding outward-facing actions at that point would be: `git push -u origin main` and
`git push origin v0.1.0`, and — only if the family decides to publish this package —
`uv publish` or equivalent to a package index. None of these were run, and none should be run
without a separate, explicit go once a remote actually exists.

## 5. Rollback Path

This is the first commit this repository will ever have, so "rollback" doesn't mean "restore
the prior working version" — there is no prior version. Concretely, until a remote exists and
someone else has cloned this repo, rollback is trivial and total:

- **To undo the tag only:** `git tag -d v0.1.0`.
- **To undo the commit and return to the pre-init state:** `rm -rf .git` (removes all git
  history; the working tree files remain exactly as they are now, since nothing besides `.git/`
  itself was touched by this commit) — or, to keep the initialized repo but with zero commits,
  `git update-ref -d refs/heads/main`.
- **Nothing external depends on this yet** — no remote, no consumers, no published package, no
  CI run against this commit (the `.github/workflows/ci.yml` file exists but has never
  triggered, since nothing has been pushed anywhere). Rollback carries zero blast radius today.
- **Once this is pushed** (a future, separate, authorized step): rollback would then mean
  `git revert` (never `push --force` on a shared branch) for a mistake found after the fact, or
  simply not tagging/publishing a package release from this commit if the mistake is caught
  before that outward step.

## 6. Learnings (Keep!)

- **What went well:**
  - QA's hands-on, adversarial CLI testing caught a genuine, severe security bug (B5:
    unvalidated `--as-of` was a path-traversal/arbitrary-file-write primitive) that peer
    review's own test suite had not surfaced — a clear example of why "verify by execution,
    hands-on, outside-in" earns its own dedicated phase rather than trusting a green test
    suite as sufficient.
  - The review process's own re-review discipline caught a bug (F5) introduced while fixing
    another (F1) — the first fix closed the read/parse traceback path but left a
    handler-side `KeyError` path open on wrong-shape-but-valid JSON. Nobody shipped this
    silently; round 2 of re-review caught it before the gate ever went green.
  - Both gates insisted on re-executing exact repros rather than trusting a diff or a fix
    summary — this pattern (re-run the *exact* failing command, not just the new test) is
    what actually closed each finding with confidence, and is worth treating as a durable
    team habit, not a one-off diligence choice for this feature.
  - The C4 decision to require a real, pinned, installed sibling repo for integration testing
    (rather than mocking `aspark-graph`) is precisely what let both B5 and B2 (malformed
    `graph.json`) surface — a mock would have hidden both.

- **What we'd do differently:**
  - `--as-of` input validation (B5) and the wrong-shape/malformed-graph traceback hardening
    (B2/F1/F5) were all found reactively, late, by QA/re-review, rather than being part of
    the original task DoDs in the plan. A lightweight "hostile-input checklist" (empty file,
    non-dict JSON, path-traversal strings, missing keys) applied at `/increment` time for any
    CLI accepting user-controlled strings used in file paths would likely have caught these
    earlier and cheaper.
  - The `--output` flag (B1's fix) was a genuine, reasonable product decision, but it was
    discovered only because QA happened to point the tool at a real neighboring repo and
    noticed the side effect. Worth a standing convention for the family: any tool that reads
    from `--repo X` and also writes derived state should default-document where it writes, in
    its own `--help`, from the very first draft — not as an after-the-fact fix.
  - Local git identity (`user.name`/`user.email`) being entirely unconfigured on this machine
    was only discovered at the release step, forcing a workaround (env-var-scoped identity)
    under the "never touch git config" rule. Worth surfacing earlier in the loop (e.g. at
    `/sprint-plan` or `/increment` time) that this is a from-scratch, never-`git init`-ed repo,
    so the human sets up their preferred commit identity ahead of the release ceremony rather
    than at the last gate.

- **Patterns worth reusing:**
  - The named-error taxonomy (`errors.py`, each carrying a machine-readable `reason`) plus a
    single `canonical_json()` byte-stable serializer is a clean, small pattern worth
    replicating in any future family CLI — it's what made NFR-3 ("never a raw traceback")
    both enforceable and cheaply testable.
  - Keeping `require_snapshot_shape()` as a *separate* function from `read_snapshot_dict()`
    (rather than folding validation into the read path) is a good instance of "don't
    over-generalize a fix" — it closed the real gap (F5) without silently changing `diff`'s
    deliberately tolerant behavior. Worth calling out as a reusable review heuristic: when
    fixing a validation gap, check whether *every* caller of the read path actually wants the
    same strictness before centralizing it.
  - `--output`-style redirection for any CLI that both *reads from* and *writes derived state
    into* a path the caller supplies is a good default pattern for the whole family to adopt,
    documented in `--help` itself, not just in code comments.
  - This release report's own git-identity workaround (env-var-scoped `GIT_AUTHOR_*` /
    `GIT_COMMITTER_*` for a single commit, instead of touching `.git/config` or
    `~/.gitconfig`) is a reusable technique worth keeping in mind for any future from-scratch
    repo's first commit under the same "never touch git config" constraint.
  - Candidate for the project's `CLAUDE.md` / shared memory: "for any new, not-yet-`git
    init`-ed family repo, confirm local git commit identity is configured *before* the first
    `/go-live` pass" — a small process nudge that would have avoided today's workaround
    entirely.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time (fresh test run, fresh build, fresh
      real-sibling-repo build, clean working tree — all re-verified on the actual release
      commit, not copied from `review.md`/`qa.md`)
- [x] Changelog written in user-facing (next-developer-facing) language, no commit hashes,
      no ticket IDs, no internal jargon
- [x] Release actions executed and verified for everything in scope (local commit + local tag)
      — outward-facing actions (push, PR, deploy, publish) correctly **not** executed: there is
      no remote, no PR target, and no deploy target for this CLI package. This is a reportable,
      intentional "prepared, awaiting go" state, not a failure — and there is currently no
      specific "go" pending since nothing outward-facing is applicable yet.
- [x] Rollback path written and concretely actionable (trivial and total, given this is the
      first commit with zero external dependents)
- [x] Learnings recorded — what went well, what we'd change, reusable patterns, and one
      candidate flagged for `CLAUDE.md`/shared project memory
- [x] Status set to `released` — confirmed by the user: prepare-only (local `git init`, commit,
      annotated tag) was the entirety of what's actionable, since no remote/PR/deploy target
      exists yet. Setting up a remote and pushing is a separate, future, explicitly-authorized
      step whenever the user is ready — not a blocker on calling this first release done-done.
