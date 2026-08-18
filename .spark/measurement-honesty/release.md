# Release: measurement-honesty

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `preparing` |
| **Version** | v0.5.0 |
| **Date** | 2026-08-10 |

<!-- Direct-to-`main` mode: the constitution has no `Delivery & Handoff` section, so the
     project's established mode applies silently (every prior release — foundation v0.1.0,
     traceability-metrics v0.2.0, public-repo-polish, mcp-server v0.3.0, snapshot-report
     v0.4.0 — committed straight to `main` and tagged, no PR). Terminal status will be
     `released` once the outward-facing steps run. This pass is prepare-only: the local
     commit and local tag exist, nothing has been pushed. Awaiting the user's explicit go. -->

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — read in full this pass. No Blocker/Major/Minor
      findings; two Nits, both accepted by the user 2026-08-09: F1 (the caveat's
      `value is None and n` discriminator assumes a gated evidence-absent null always has
      `n>0` — true for all 8 current metrics; a latent future-metric assumption already
      documented in plan decision 5, revisit if I6 introduces a computed-value-with-`n==0`
      shape) and F2 (the key-driven provenance tail renders `artifact_probe.detail` as the
      literal `None` on non-inconclusive reports — consistent with the verbatim-provenance
      convention). The three concerns the coordinator flagged for independent scrutiny all
      held under re-derivation (see §6). Gate genuinely complete.
- [x] `qa.md` status is `passed` — read in full this pass. Hands-on browser `/demo-day`
      across three served pages plus the QA Tester's own hand-built hostile fixture. All
      US-4/NFR-4 browser ACs verified pass with measured values (byte-offset section order,
      6.97:1 / 7.48:1 contrast via `getComputedStyle`, 375px/320px zero horizontal scroll,
      zero interactive elements); US-1/US-2/US-5 build-time ACs spot-checked via real CLI;
      US-3 filesystem-safety and US-6 README covered by `/peer-review`'s 254 green tests.
      One Minor accepted by the user (B2: the live count is 10 matching qa.md/review.md
      files across 6 feature dirs vs. the spec's illustrative "4 qa.md files" — the spec
      explicitly marked that number illustrative, not prescriptive; the reason string and
      provenance agree at 10, internally consistent and truthful). No open Blocker/Major.
      Gate genuinely complete.
- [x] Full test suite green **on the exact release commit**, run fresh by me this pass —
      not copied from `review.md` (which cited 254) or `qa.md`: `uv run pytest -q` →
      **254 passed in 53.88s**, no skips, no xfails, against the real, unmocked sibling
      `aspark-graph` dogfood graph.
- [x] `uv lock --check` — clean this pass: "Resolved 41 packages in 75ms" (the lock was
      regenerated after the version bump during `/increment`; confirmed still consistent).
- [x] Build succeeds from a clean state — `uv build --out-dir <scratch>` produced both
      `aspark_insights-0.5.0.tar.gz` and `aspark_insights-0.5.0-py3-none-any.whl`, exit 0,
      artifacts carrying `0.5.0`. Scratch output removed afterward, never left in the repo.
- [x] Working tree clean before staging — `git status` showed exactly this feature's diff
      and nothing else: 5 new files (`artifact_probe.py`, `metrics/evidence.py`,
      `tests/test_artifact_probe.py`, `tests/test_evidence_rule.py`,
      `tests/fixtures/no_qa_graph.json`) plus the `.spark/measurement-honesty/` artifacts,
      and 19 modified files (`README.md`, `pyproject.toml`, `__init__.py`, `build.py`,
      `cli.py`, `registry.py`, `traceability.py`, `provenance.py`, `render.py`, `uv.lock`,
      and 9 test files). Matches `review.md`'s own scope section. No stray/unexpected file.
      Clean again immediately after the release commit and tag (confirmed, not assumed).
- [x] Version consistency confirmed, not re-litigated — the bump was decided and reviewed
      during `/increment` (AC-5.1 / NFR-7). `pyproject.toml` = `0.5.0`,
      `src/aspark_insights/__init__.py` `__version__` = `0.5.0`, and a live
      `import aspark_insights; print(__version__)` = `0.5.0` all agree. This is a real
      behavior change, not a ceremony bump (see §2) — the registry's value contract changed.

## 2. Version

**v0.5.0** — bump from `v0.4.0`. Justification (this project's "a version bump is a claim
about package behavior, not a ceremony checkbox" rule, `CLAUDE.md`):

- **This is a breaking change to a public contract, and it earns the bump.** The metric
  registry is public surface (constitution §2, `library` lens). Before this release a
  consumer diffing or reading a snapshot could assume `TRC-002` and
  `TRC-004-unverified-acs` always carried a number; after it, either can return
  `value: null`. A previously-numeric result gating to `null` is precisely the class of
  behavior change that warrants a version move — unlike `public-repo-polish`, which
  correctly shipped with **no** bump because it changed zero package behavior.
- **Where the break is signalled.** This project is pre-1.0 (`0.x`) by its own established
  convention (`snapshot-report` §2), so a package-level breaking change lands in the minor
  component: `0.4.0` → `0.5.0`. The *precise* semver signal for the broken contract lives
  one level down, on the metric definitions themselves: five metric definitions
  (`TRC-001`, `TRC-002`, `TRC-003`, `TRC-004-orphan-tasks`, `TRC-004-unverified-acs`) move
  from `metric_version` `1.0.0` → `2.0.0` (a proper major bump on the definitions whose
  reachable null-condition changed), while `TRC-005-*`, whose behavior is unchanged, stays
  `1.0.0`. That is what makes `insights diff` show a version change alongside the value
  change instead of the same definition apparently producing two answers.
- **Checked, not assumed.** The bump is already applied (working tree and now the release
  commit); I verified `pyproject.toml`, `__version__`, and a live import all read `0.5.0`,
  that `review.md`/`qa.md` tested against `0.5.0`, and that `v0.5.0` is not already a tag
  (existing tags: `v0.1.0`…`v0.4.0`). Zero new runtime dependencies (stdlib `os`/`pathlib`
  only, NFR-7). I did **not** re-derive the bump level — that decision was made and
  reviewed during `/increment` (A5, confirmed by the user 2026-08-04); my job here was to
  confirm it is consistent and honest, which it is.

## 3. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- The HTML report now shows a clear **"NOT COMPUTED"** notice near the top whenever one or
  more metrics couldn't be honestly measured — stating how many of the total were affected,
  which ones, and where to read the full reason — so a caveat can no longer be missed by not
  scrolling into a table cell. It sits directly under any existing "stale data" warning and
  is told apart from it by its first word, not by colour alone.
- The report's provenance section now discloses, on **every** report, the result of an
  on-disk check: whether your project's review/QA artifact files were actually found under
  `.spark/`, and how many. This means "no caveat shown" now reliably reads as "measured
  fine" rather than "the check silently never ran".

### Changed
- Because two metric definitions changed, they now carry a new definition version.
  Comparing a snapshot built before this release against a newer one shows that version
  change together with the value change, and verifying an old snapshot against the new
  definitions reports an honest mismatch — the tool tells you the meaning changed rather
  than pretending the old and new numbers are the same measurement. (No stored snapshot is
  rewritten; sealed history stays sealed.)

### Fixed
- Two coverage figures — acceptance-criteria-to-QA coverage, and the count of unverified
  acceptance criteria — used to report a confident, fabricated result (0% covered / every
  criterion unverified) on any project whose QA artifacts exist on disk but aren't
  recognised by the pinned analysis tool. They now honestly report **"not computed"** with
  a reason that names both what was seen (no readable QA evidence in the analysed graph)
  and what was found on disk (your QA files are present but produced nothing the tool could
  read) — turning a misleading zero into an actionable "here is your actual bug". Any metric
  whose evidence is entirely absent now behaves this way; metrics whose evidence genuinely
  exists are unchanged, exactly as before.
- The README no longer makes claims that were two releases stale: it described the report
  generator as "not yet implemented" after it had shipped, still advertised an old version,
  and listed already-shipped capabilities as "planned". The front page now matches what the
  tool actually does, and documents the new honest-null behaviour with a real example.

## 4. Release Actions

<!-- What was actually executed, with results. Direct-to-`main` mode. -->

| Action | Result |
|---|---|
| Version bump & tag | **Prepared, local only.** Bump (`0.4.0` → `0.5.0` in `pyproject.toml` + `__init__.py`, `uv.lock` regenerated) was applied during `/increment` and verified consistent this pass. Release commit `3a8419a` created locally on `main`; local annotated tag `v0.5.0` created on it (tagger: Andreas Lottes <andreas@lottes.dev>). **Not pushed.** |
| PR / merge | N/A — direct-to-`main` convention (no `Delivery & Handoff` declaration; every prior release committed straight to `main`, no PR). |
| Deploy | N/A — CLI + library package, no hosted service to deploy. |
| Post-release smoke check | **Pending — awaiting go.** Will run after push: confirm `3a8419a`/`v0.5.0` live on the remote, then a fresh `git clone` + `uv sync` + real `insights build`/`query`/`render` against the sibling `aSPARK-graph`, confirming `TRC-002`/`TRC-004-unverified-acs` render `Not computed:` and `insights_version: 0.5.0` flows through a real render. |

**Prepared this pass — local, reversible work, already done:**
```
# Version bump was applied during /increment (verified consistent, not re-applied):
#   pyproject.toml: version = "0.5.0";  __init__.py: __version__ = "0.5.0";  uv.lock regenerated
git add <explicit feature file list — never -A/.>   # 27 paths; release.md deliberately excluded
git commit -m "feat: measurement-honesty — honest null on absent evidence, artifact probe + report caveat, v0.5.0"
#  -> 3a8419a
git tag -a v0.5.0 -m "v0.5.0 — measurement-honesty: honest null on absent evidence (closes I2 A3 disclosure) ..."
```

**Pending — outward-facing, NOT executed. Each requires the user's explicit go relayed by the caller:**
```
git push origin main            # 28a5bfd..3a8419a  main -> main
git push origin v0.5.0          # * [new tag]        v0.5.0 -> v0.5.0
# then, matching the snapshot-report precedent, a separate docs commit recording THIS
# report (release.md) + its learnings, then push:
#   git add .spark/measurement-honesty/release.md && git commit -m "docs: record measurement-honesty release report and keep its learnings" && git push origin main
# then the post-release smoke check above.
```

**Status: prepared, awaiting go.** Nothing has left this machine.

## 5. Rollback Path

- **Right now (pre-push — the currently-available path):** the release commit and tag are
  local only. To discard them completely, nothing having been published:
  `git reset --hard HEAD~1` (drops commit `3a8419a`, restoring the pre-commit working-tree
  state) and `git tag -d v0.5.0` (removes the local tag). Fully reversible, no trace leaves
  the machine.
- **After push (once the go is given):** forward-only on a public branch —
  `git revert 3a8419a` on `main`, then `git push origin main`. **Never `push --force` /
  history-rewrite on `main`** (this project's standing rule).
- **To retract the tag** (only if the release is genuinely wrong, not for a routine
  follow-up fix): `git push origin :refs/tags/v0.5.0` removes the remote tag.
- **Not on PyPI** — no `uv publish` step exists or is planned; the only place `v0.5.0` would
  live is this git remote (matching `mcp-server`/`snapshot-report` precedent).
- **No deploy to roll back** — CLI + library package; "rollback" here means the git
  commit/tag, not a running service.
- **Snapshots are not migrated** — a snapshot built before this release keeps its old
  numbers and now honestly fails `insights verify` with `verify_mismatch` (AC-5.4,
  intended). "Rolling back" the definitions would re-hide the fabricated zero, so it is not
  a rollback the project wants; the forward path (`git revert`) is the only sanctioned undo.

## 6. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - **The design-review gate (`/look-and-feel`) paid for itself on a feature that doesn't
    *look* UI-heavy.** This is a metrics-honesty/registry change, yet the Designer's pass
    (spec §8) caught a genuine **Blocker (D5)** before any code was written: `render.py`
    built its provenance rows from a hardcoded literal list, so the probe's sealed
    disclosure record would have been silently dropped from the HTML — the exact
    invisible-disclosure bug class this feature exists to kill, reproduced one layer up in
    the renderer. It also surfaced five Major spec-amendment findings (D1–D4, D8: top-band
    stacking order, opaque id list, the fresh-repo trigger ambiguity, an AC that literally
    forbade `snapshot-report`'s shipped empty-notice, two non-falsifiable NFR clauses), all
    folded into ACs and logged as C9–C16. Worth keeping as evidence that "UI-facing" for the
    design gate means "produces a rendered artifact a human reads", not "looks like a web
    app" — a feature that only *touches* the report surface still earns the gate.
  - **`/peer-review` independently re-derived every flagged concern rather than trusting the
    increment's account** (review.md §5/§6): it re-checked that the build-loop invariant
    uses `raise AssertionError` (not `assert`, which `-O` strips) so the caveat discriminator
    is genuinely enforced; that the shared `MAPS_TO` evidence gate correctly nulls both
    `TRC-001` and its *inverse* `TRC-004-orphan-tasks` (a repo-wide zero `maps_to` yields an
    honest null, not a fabricated "100% orphan"); and that the probe's hostile-input safety
    is real (symlink refusal at both levels, `detail` a curated errno-class string that never
    touches `str(exc)`). This is the same adversarial-verification bar `snapshot-report`
    established for re-review, applied here to correctness invariants, not just a security fix.
  - **QA independently re-derived the security surface with its own hostile input** (qa.md B1,
    §4): the QA Tester built a fresh attribute-breaking / `<img onerror>` / `<svg onload>`
    fixture plus a *novel* top-level provenance field the prepared fixture never used, and
    the single `_esc` choke-point escaped every vector — zero script/img/svg elements, no
    external request, clean console. This extends `snapshot-report`'s "reproduce it yourself,
    don't trust the account" precedent onto the key-driven provenance tail this feature added.

- **What we'd do differently:**
  - **`/demo-day` was interrupted mid-run (an API spend-limit hit), and the recovered subagent
    output was not taken at face value** — the orchestrating conversation independently
    re-verified the most safety-critical claims (XSS escaping and byte-offset DOM ordering)
    live in the browser before accepting the pass (consistent with qa.md §4's own record of
    independent escaping/ordering re-derivation). The lesson to carry forward: when an agent's
    run is interrupted and resumed, treat its recovered output as *unverified* for the
    highest-stakes claims specifically, and re-run those checks yourself rather than trusting
    the reassembled report — the interruption is exactly when a silent gap is most likely.
    Worth a note for handling any future interrupted-agent QA/review output, not just this
    incident.
  - **The F1 Nit's "true for all 8 current metrics" framing is a latent assumption to revisit
    when I6 lands.** The caveat discriminator (`value is None and n`) is enforced today by a
    build-loop invariant on each metric's *raw* return, but a future metric returning a
    computed value with `n==0` would gate to null-with-`n==0` and escape the caveat. Already
    documented in plan decision 5 and accepted; flag it as the concrete thing to check the
    moment `debt-indicators` (I6) introduces a new metric shape, so it's caught at spec time,
    not rediscovered.

- **Patterns worth reusing** (candidates for `CLAUDE.md` / project memory):
  - **"Don't recompute what the graph already answers" extends to disclosure, not just
    computation.** The artifact probe answers exactly the one question a graph structurally
    *cannot* — "does a file exist on disk that you failed to parse?" — reading zero bytes and
    inventing no second parser (ADR-0 held). This is the constructive companion to CLAUDE.md's
    existing "disclose a new risk through an existing provenance field" note: the probe is a
    minimal, bounded new observation that turns "we can't measure this" into "here is your
    actual bug", and it is a template for any future "the graph can't see X, so state X as a
    directly-observed fact" disclosure.
  - **A changed null-condition on a shipped metric is a value-contract change and ships as a
    metric_version major bump with the superseded definition removed** — one entry per
    `metric_id`, `1.0.0` never left registered alongside `2.0.0`, so `insights verify`
    honestly mismatching an old snapshot *is* the disclosure rather than a bug to suppress.
    Worth naming as the house rule for any future metric whose reachable output shape changes.
  - **The design gate is "produces a human-read rendered artifact", not "looks like a web
    app"** (from the D5 Blocker above) — a candidate CLAUDE.md process nudge so future
    metrics/registry features that touch `render.py` are routed through `/look-and-feel`
    rather than skipped as "not really UI".

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

<!-- Prepare-only pass: pre-flight, changelog, learnings and the rollback path are done and
     checked; the outward-facing release actions are prepared but deliberately NOT executed,
     pending the user's explicit go. That box stays unchecked until push + smoke check run,
     and the status stays `preparing` until then — a prepared-but-unpublished release is a
     normal, reportable state, not a failure. -->

- [x] All pre-flight checks passed at release time (fresh this pass on the exact release
      commit `3a8419a`: 254 passed in 53.88s; `uv lock --check` clean; clean build from
      scratch producing `0.5.0` artifacts; clean working tree before staging and after the
      commit/tag; version consistent across `pyproject.toml`/`__init__.py`/live import)
- [x] Changelog written in user-facing language, no commit hashes, no ticket IDs, no
      internal jargon
- [ ] Release actions executed and verified — **prepared, awaiting go.** Local commit
      `3a8419a` and local tag `v0.5.0` created (reversible, unpushed); `git push origin main`,
      `git push origin v0.5.0`, the release-report docs commit, and the post-push smoke check
      are pending the user's explicit authorization. Rollback path written (§5).
- [x] Learnings recorded — the design gate earning its cost on a non-visual-looking feature
      (the D5 Blocker), `/peer-review`'s independent re-derivation of every flagged invariant,
      QA's own hostile-fixture re-derivation, the interrupted-`/demo-day` re-verification
      lesson, and reusable patterns (disclosure-not-recomputation; metric_version bump on a
      changed value contract; the design-gate scope nudge)
- [ ] Status set to `released` — **currently `preparing`.** Flips to `released` only after
      the outward-facing steps run on the user's go.
