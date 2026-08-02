# Spec: public-repo-polish

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-02 |

## 1. Problem & Goal

- **Problem:** The repo was just made public on GitHub (`github.com/a-lottes/aSPARK-insights`),
  matching the precedent of its shipped siblings `aSPARK-graph`/`aSPARK-policy`. Its public
  surface is not yet at their standard: the README is a 4-line placeholder stub from `foundation`
  (no install/usage/status/license section), there is **no root `LICENSE` file** despite
  `pyproject.toml` declaring `license = {text = "MIT"}`, `.gitignore` has real gaps for a public
  repo (no IDE folders, no secret-file patterns), and one already-`released` artifact
  (`.spark/traceability-metrics/release.md`, status `released`, v0.2.0) sits untracked in the
  working tree — verified via `git status`, not assumed.
- **Goal:** A stranger clicking in from GitHub understands, from the README alone, what this
  project is, its real current status (v0.2.0, real dogfooded traceability-coverage numbers —
  not the pre-I2 "Geplant" placeholder), how to install and try it, and where it sits in the
  aSPARK family — without opening internal planning docs. Licensing is unambiguous and
  machine-detectable. Nothing accidentally-committable (secrets, IDE state) is one `git add .`
  away from landing in public history.
- **Success signal:** A read-through of the README alone (no other file) answers "what is this,
  why does it exist, what can I actually run today, what license is it under" — verified at
  `/demo-day` by literally running every example command shown; `git status` reports a clean
  tree with no already-shipped artifact left uncommitted; a `licensee`-style check (or GitHub's
  own detector) recognizes the `LICENSE` file as MIT.
- **Why now:** The repo is public *today*. Every day the placeholder README/missing LICENSE
  stands is a day a first impression is being formed on a rough draft, not a decision to defer.

## 2. Target Users

- **A stranger arriving via GitHub** (the family's own audience — sibling repos already target
  this reader) deciding in under a minute whether this is relevant to them.
- **The maintainer**, who wants the public surface to honestly reflect what's shipped (v0.2.0,
  real TRC-\*/MTA-\* numbers) without overclaiming (no dashboards, no PyPI package, no
  production-readiness that doesn't exist).

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | The repo stays a single-maintainer, source-available showcase this cycle — no active solicitation of outside contributors. | Assumed; no `CONTRIBUTING.md`/issue templates in scope (see §6). |
| A2 | No PyPI publish happens in this cycle (confirmed: `release.md` §4 records `uv publish` was never run, no remote existed as of the last release). | "Advertise-able" means readable/runnable from source, not `pip install`-able. Install docs describe source-only setup. |
| A3 (verified) | No root `LICENSE` file exists despite `pyproject.toml`'s declared MIT license. | Real gap, not assumed — addressed by US-2. |
| A4 (verified) | `.spark/traceability-metrics/release.md` is untracked (`git status`: `?? .spark/traceability-metrics/release.md`) despite describing a `released` v0.2.0. | Real gap — addressed by US-4. |
| A5 | Whether a git remote is already configured (the task context says "made public," but the last-known local state per `release.md` was "no remote configured, nothing pushed") is unconfirmed from repo state alone. | Not blocking: no AC in this spec depends on a remote existing; pushing/publishing stays a `/go-live`-owned action. |

## 4. User Stories

### US-1 (Must): A self-contained, honest public README

> As a stranger arriving via GitHub, I want a README that explains what this is, why, its real
> current status, and how to try it, so that I don't have to read source code or internal
> planning docs to decide whether it's relevant to me.

**Acceptance criteria:**

- [ ] AC-1.1: Given the README, when read from the top, then within the first few lines it
      states in English what the project does (versioned metric definitions/coverage metrics
      computed from `aspark-graph`'s facts) and its real current status — v0.2.0, real dogfooded
      TRC-001..005/MTA-001..003 traceability coverage shipped; dashboards/flow/architecture-health
      metrics not yet built. It never repeats the pre-I2 "Geplant"/placeholder framing once real
      numbers exist (see Clarification C1), and never claims production-readiness, a dashboard,
      or capabilities this repo doesn't have.
- [ ] AC-1.2: Given the README's Install section, when followed literally (Python ≥3.11, `uv`, a
      sibling `aSPARK-graph` checkout at `../aSPARK-graph` per `pyproject.toml`'s `uv.sources`),
      every command shown succeeds against the real repo state; it never references an
      unpublished PyPI package (see C2).
- [ ] AC-1.3: Given the README's Usage section, when a reader copies a shown `insights` command,
      it uses the real, shipped subcommands/flags (`build|query|render|diff|verify`) — each
      example either runs directly or is explicitly labeled with its prerequisite (e.g. "requires
      a graph built via `aspark-graph build`").
- [ ] AC-1.4: Given the README, it links to `aSPARK` (Core), `aspark-graph`, and `aSPARK-policy`
      and states this project's place among them; it does **not** require opening
      `docs/ARCHITECTURE-PROPOSAL.md`, `docs/CROSS-REPO-PLAN.md`, or `.spark/BACKLOG.md` to
      understand what the project does or how to use it today — those stay internal planning
      artifacts, referenced only optionally as further reading for contributors (see C4).
- [ ] AC-1.5: Given the README, a License section names MIT and links to a real root `LICENSE`
      file (US-2) — never a dead link.
- [ ] AC-1.6: Given the README's content, it contains no local-machine-specific absolute paths
      (e.g. `/Users/<name>/...`), no internal/unpublished URLs, and no fabricated adoption or
      quality number.

### US-2 (Must): A real LICENSE file

> As a visitor (or GitHub's own license detector), I want an actual `LICENSE` file matching the
> license declared in `pyproject.toml`, so licensing is unambiguous and machine-detectable.

**Acceptance criteria:**

- [ ] AC-2.1: Given the repo root, a `LICENSE` file exists with standard MIT text and the correct
      copyright holder/year, matching `pyproject.toml`'s `license = {text = "MIT"}`.
- [ ] AC-2.2: Given GitHub's repo view, the file is close enough to the standard MIT template to
      be auto-detected as MIT — matching the `aSPARK-graph` sibling's own precedent (it ships a
      root `LICENSE` file today).

### US-3 (Must): `.gitignore` hardened for a public repo

> As the maintainer, I want `.gitignore` to cover the gaps a public repo commonly needs, so no
> IDE state, secret-like file, or extra OS artifact is ever accidentally committed.

**Acceptance criteria:**

- [ ] AC-3.1: Given the current `.gitignore`, all currently-present, correctly-ignored local
      artifacts (`.venv/`, `.pytest_cache/`, `.claude/`, `__pycache__/`, `.aspark-insights/`,
      `.aspark-graph/`, `.DS_Store`) remain ignored — no regression.
- [ ] AC-3.2: Given the verified gaps — IDE folders (`.vscode/`, `.idea/`), secret/env files
      (`.env`, `.env.*`), additional OS cruft (`Thumbs.db`) — when added, creating a throwaway
      file matching each new pattern and running `git status` shows it ignored, not untracked.
- [ ] AC-3.3: Given the updated `.gitignore`, `git status` on the real working tree reports the
      same clean state as before, plus catches the new patterns — no unrelated file newly ignored
      or un-ignored.

### US-4 (Must): Tracked history matches shipped reality

> As anyone auditing the repo, I want every artifact describing already-shipped, released work to
> actually be committed, so the public git history doesn't silently lag behind what `.spark/`
> claims was released.

**Acceptance criteria:**

- [ ] AC-4.1: Given `.spark/traceability-metrics/release.md` exists on disk (status `released`,
      v0.2.0) but is untracked today (`git status` confirms `??`), it is committed as part of
      this feature's own release, matching the precedent set for `foundation`'s own `release.md`
      (bundled as its own housekeeping commit, `00e9c02`).
- [ ] AC-4.2: Given the repo's working tree at the point this feature is released, `git status`
      reports a clean tree — no unexpected modified/untracked file left over from a prior session
      beyond this feature's own intended diff.

### US-5 (Could): Visual/branding parity with siblings

> As a visitor comparing family repos, I want this README to feel consistent with
> `aSPARK-graph`'s and `aSPARK-policy`'s (section order, tone), so the family reads as one
> product line.

**Acceptance criteria:**

- [ ] AC-5.1: Given the README, its section order is recognizably consistent with the siblings'
      (problem → install → usage → status → family position → license). An optional logo/badge
      header is a nice-to-have, not required — exact visual treatment parked for
      `/look-and-feel`/`/sprint-plan`.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Security (`security` lens) | No file touched by this feature (README, `.gitignore`, `LICENSE`) contains a local-machine-specific absolute path or secret-like string; `grep -r "/Users/"` / `/home/` on touched files returns nothing. | `/peer-review` |
| NFR-2 | Security (`security` lens) | `.gitignore`'s new patterns (`.env`, `.env.*`) actually prevent tracking: creating a throwaway matching file and running `git status` shows it ignored. | `/demo-day` |
| NFR-3 | CLI (`cli` lens) | Every CLI command shown in the README is copy-paste runnable against a real checkout, or explicitly labeled with its prerequisite — none is pseudocode presented as runnable. | `/demo-day` (literally run each example) |
| NFR-4 | Library (`library` lens) | The README's Install section accurately reflects the package's real current distribution state (source-only install, exact-pinned sibling path dependency) — no claim of PyPI availability. | `/peer-review` against `pyproject.toml`/`uv.lock` |
| NFR-5 | Evidence honesty (constitution Non-Negotiable, inherited) | Any concrete metric number shown as a README example is explicitly labeled as a dated, point-in-time run — never presented as a live/current guarantee; no adoption/quality number is invented. | `/peer-review` |
| NFR-6 | Performance | N/A — documentation/config-only feature, no runtime behavior change. | — |
| NFR-7 | Accessibility | N/A — plain Markdown rendered by GitHub, no custom UI. | — |

## 6. Out of Scope

- Rewriting, translating, or re-labeling `docs/ARCHITECTURE-PROPOSAL.md`, `docs/CROSS-REPO-PLAN.md`,
  or `.spark/BACKLOG.md`'s content, language, or their own "Geplant"/draft status — they stay
  internal planning artifacts; only the README's own claims must be current (C1, C4).
- Any new CLI functionality, bug fix, or behavior change — this is presentation/hygiene only.
- Publishing to PyPI, configuring a remote, `git push`, or any other outward `/go-live`-owned action.
- `CONTRIBUTING.md`, issue/PR templates, `CODE_OF_CONDUCT.md`, or otherwise actively soliciting
  outside contributions — no evidence this is wanted yet (A1).
- CI badges/shields or other visual embellishment beyond US-5's minimal consistency check — a
  technical "how," parked for `/sprint-plan`/`/look-and-feel`.
- Deleting or otherwise touching `.claude/worktrees/**` on disk — already correctly gitignored
  (never in public git history); local-machine hygiene, not a repo-content decision (C5).
- Any change to `src/`, `tests/`, CI workflow logic, or dependency versions.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-02 | Should the README describe status as "Geplant"/planned (the pre-I2 `BACKLOG.md`/`ARCHITECTURE-PROPOSAL.md` guardrail), or reflect that I2 already shipped real numbers? | State the current true status: v0.2.0, real dogfooded coverage metrics shipped on both named sibling repos; dashboards/flow/architecture-health still ahead. The "stays Geplant until real numbers exist" guardrail's own trigger condition was already met per `traceability-metrics/spec.md`'s own Problem statement — repeating stale language would itself be dishonest. |
| C2 | 2026-08-02 | Should Install instructions show a PyPI `pip install`? | No — not published (verified: `release.md` §4, "no remote configured... `uv publish`... none of these were run"). Install docs describe source-only setup with the pinned sibling-repo path dependency, mirroring `aSPARK-policy`'s own honest not-yet-published contributor path. |
| C3 | 2026-08-02 | May specific dogfood numbers (e.g. TRC-001's real value) appear verbatim in the README? | Only if explicitly labeled as a dated, point-in-time example run — never as a live/current claim. Avoids both staleness and any appearance of an invented number (NFR-5). |
| C4 | 2026-08-02 | Does "clean up the repo" require rewriting `docs/`/`BACKLOG.md` (partly German, references a private out-of-repo path, marked draft/unapproved)? | No — out of proportion to a presentation/hygiene cycle; a real, separate documentation feature. This spec instead requires the README to stand alone (AC-1.4) so a public reader is never forced into those internal drafts. |
| C5 | 2026-08-02 | Does "nothing embarrassing public" include the local, gitignored `.claude/worktrees/**` directory found on disk? | No — it's correctly gitignored today and has never entered public git history; local machine hygiene, not a repo-content concern. |
| C6 | 2026-08-02 | Does this feature need to configure a remote or push, since the repo was "just made public"? | No — that's a `/go-live`-owned outward action; every AC here is verifiable from local repo/file state alone (A5). |

## 8. Design Review

N/A for this feature — no interactive UI surface; the README is plain Markdown rendered by
GitHub. `/look-and-feel` may still weigh in on US-5's section-order/tone consistency as a light
touch, not a full design review.

---

## ✅ SPEC GATE

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk (A5)
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected — `security`/`cli`/`library` lenses land as NFR-1..4; "never invent a number" lands as NFR-5
- [x] Design review done for UI-facing features (or marked N/A with reason) — N/A, see §8
- [x] Status set to `approved` by the user
