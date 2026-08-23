# 📊 aspark-insights

> **Real, hand-verifiable engineering metrics computed from your repo's actual delivery graph — never a second-guessed number, never a fabricated one.**

> **Project status: shipped at `v0.10.0` — real traceability coverage, a
> self-contained HTML report, an MCP query tool, honest nulls throughout, a
> git-native mid-cycle board, and a release board (JSON and a self-contained
> dark-theme HTML page, newest release first, each feature's own documents
> viewable in place) that maps every git tag to the SPARK features that
> shipped in it.**
> You can build a snapshot today and get real Story→Task, AC→QA and Task→Code
> coverage numbers, each with its own sample size, computed against
> [aspark-graph](https://github.com/a-lottes/aSPARK-graph)'s facts, then render
> them as one offline HTML report or query them over MCP (see [Install](#install)
> and [Usage](#usage)). A metric whose underlying evidence never made it into
> the graph — not "nothing happened", but "the graph never saw it" — reports an
> honest `null` with a reason instead of a fabricated `0%` or `100%` (see
> [Absent evidence vs. a real zero](#absent-evidence-vs-a-real-zero)). Separately,
> `insights board` answers "what's landed since the last release, what's in
> flight" from local git alone — no graph, no `.spark/` — proving this tool runs
> standalone against any git repo, not only the aSPARK family (see
> [Mid-cycle board](#mid-cycle-board)), and `insights releases` maps every git
> tag to the `.spark/` features that shipped in it (see
> [Release board](#release-board)). What's still missing: flow/cycle-time
> metrics, architecture-health metrics, and policy-derived compliance metrics —
> all future increments. Not yet on PyPI — see [Install](#install) for the
> source-only setup.

---

## The problem

`aspark-graph` already knows your repo's delivery facts — which stories map to
which tasks, which acceptance criteria have a passing QA check, which tasks
trace forward into code. But a fact isn't a metric: nobody wants to hand-grep
a graph export to answer "how much of our traceability is actually covered?"

aspark-insights is the analytics layer on top: versioned metric definitions,
computed from the graph's own facts, sealed into a snapshot with full
provenance — **never a second implementation of a query the graph already
answers**, and never an invented number. When a metric has nothing to
measure yet (no stories exist, say), it reports an honest `null` with a
plain-English reason — not a fabricated `0%` or `100%`.

## Install

Requires Python ≥3.11 and [uv](https://docs.astral.sh/uv/). Not yet published
to a package index — work from a checkout, alongside a checkout of the
sibling [aspark-graph](https://github.com/a-lottes/aSPARK-graph) (this
project reads its graph output; see `pyproject.toml`'s pinned path
dependency):

```bash
git clone https://github.com/a-lottes/aSPARK-insights.git aspark-insights
cd aspark-insights
uv sync --extra dev    # installs into a local .venv, pulls in ../aSPARK-graph
uv run pytest          # the full test suite
```

The pinned sibling dependency expects `aspark-graph` checked out as
`../aSPARK-graph` relative to this repo — clone both into the same parent
directory.

## Usage

Every subcommand emits `sort_keys` JSON on stdout and a named, machine-readable
error on stderr (never a raw traceback) — the family's shared CLI contract.

```bash
# 1. Build the graph for the repo you want to measure (aspark-graph, not this tool)
uv run --directory ../aSPARK-graph aspark-graph build .

# 2. Build a snapshot — real TRC-*/MTA-* metrics, computed from that graph.
#    --output keeps insights' own derived state out of the repo you're just
#    analyzing (omitting it writes under --repo instead — fine for your own
#    repo, not what you want when --repo points at someone else's).
uv run insights build --as-of 2026-08-02 --repo ../aSPARK-graph --output /tmp/insights-scratch

# Read back the last snapshot's facts, metrics and provenance
uv run insights query --repo ../aSPARK-graph --output /tmp/insights-scratch

# Diff two snapshots (build a second one with a different --as-of first)
uv run insights diff /tmp/insights-scratch/.aspark-insights/snapshots/2026-08-01.json \
                      /tmp/insights-scratch/.aspark-insights/snapshots/2026-08-02.json

# Recompute a stored snapshot from its own recorded inputs and byte-compare
# (verify only reads/recomputes — it has no --output of its own)
uv run insights verify /tmp/insights-scratch/.aspark-insights/snapshots/2026-08-02.json --repo ../aSPARK-graph

# Render the latest snapshot as one self-contained, offline HTML report —
# writes <output>/.aspark-insights/report.html, prints its resolved path
uv run insights render --repo ../aSPARK-graph --output /tmp/insights-scratch
```

`insights build` requires a graph already built by `aspark-graph build` at the
target repo — it never builds one itself. Every metric reports a real value
with its sample size, or an honest `null` with a reason (e.g. `"no Story nodes
found in graph"`) when there's nothing to measure yet.

### Absent evidence vs. a real zero

Some metrics (currently `TRC-001`, `TRC-002`, `TRC-003`, `TRC-004-orphan-tasks`,
`TRC-004-unverified-acs`) depend on a specific graph evidence kind — a
`maps_to`, `implements`, or passing-`QACheck` `verifies` edge. If that evidence
kind's count is **zero across the whole graph**, the metric reports `null`
with a reason instead of a computed `0%`/`100%` — a repo-wide zero is exactly
as likely to mean "the graph's artifact parser never recognized your artifact
filenames" as it is to mean "nothing happened", and this project's central
promise (never invent a number) means it never guesses which.

`insights build` also checks, read-only, whether `<repo>/.spark/*/{qa.md,review.md}`
files exist on disk (never their contents — presence only, one level deep, no
symlinks followed). When they do, the null's reason names that too, turning
"we can't measure this" into "here's your actual bug":

```
no verifies-from-passing-QACheck edges found in the graph (0 of 41);
4 matching artifact file(s) found under .spark/ (qa.md, review.md)
```

The rendered HTML report surfaces this as a top-band notice naming how many
metrics were affected and where the detail lives, in addition to — never
instead of — the per-metric reason in the Metrics table.

Because this changed what some metrics' `null` conditions mean, the affected
metrics shipped a new `metric_version` (`2.0.0`) in this release — a
pre-`v0.5.0` stored snapshot legitimately fails `insights verify` with the
existing `verify_mismatch` error (its recorded values were computed against a
metric definition that no longer exists, never silently reinterpreted).

### MCP

`insights serve` runs a **read-only** stdio MCP server exposing one tool,
`query`, name-matched to the CLI subcommand it wraps:

```bash
uv run insights serve --repo ../aSPARK-graph --output /tmp/insights-scratch
```

The repo/output location is fixed once at launch — `query` takes **no arguments**, so it can never be pointed anywhere else per call, and it never triggers a fresh `build`. See [SECURITY.md](SECURITY.md) for the trust boundary and non-guarantees.

### Mid-cycle board

`insights board` is a **separate, standalone** surface — it never calls
`GraphPort` and never reads `.spark/`. It runs against any git repo, built or
unbuilt, aSPARK-flavored or not:

```bash
# JSON: commits/days since the last tag, work-type mix, local branches
uv run insights board --as-of 2026-08-13 --repo /path/to/any/git/repo

# HTML: the same data as one self-contained offline page
uv run insights board --as-of 2026-08-13 --repo /path/to/any/git/repo \
                       --format html --output /tmp/board-scratch
# writes /tmp/board-scratch/.aspark-insights/board.html
```

This is the documented **ADR-2 interim fallback**: time is properly a graph
fact once the sibling `aspark-graph` tool ships release-node data, and this
board yields to that once it exists. Until then, every field this command
produces carries a `source: "git-interim"` marker (rendered as an `INTERIM
(git-native)` notice at the top of the HTML page too) — a value from `board`
is never mistaken for a graph-sourced fact, today or later.

Same non-negotiables as everything else in this project:

- **No person-level data, ever.** No author, committer, email, or commit
  trailer (`Co-Authored-By`, `Signed-off-by`) reaches JSON or HTML — commit
  subjects are read for their leading type token only, never for identity.
- **No invented number.** A repo with no tags reports `commits: null` with a
  reason, not a fabricated `0`; a resolved tag with genuinely zero commits
  since it reports a real `0`, never confused with the null case.
- **Work-type mix is honestly degraded, not guessed.** Each commit subject's
  leading [Conventional Commit](https://www.conventionalcommits.org/) token —
  `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`,
  `style` — is classified; anything else is `unclassified`. If fewer than
  **20%** of commits since the tag carry a recognized token, the whole
  breakdown reports `null` with a reason instead of a misleading distribution
  built from too few data points.
- **Bounded, never silently truncated.** The commit list shows the most
  recent 50 with an explicit "showing N of M" note when there are more; the
  exact total count is always reported regardless.
- **Shallow clones disclose themselves.** `shallow: true` (and the HTML's "at
  least N commits…" wording) means the clone's own history may not go back
  far enough for the count to be exhaustive.

### Release board

`insights releases` maps every real git tag — plus the open window since the
latest one, as a distinguishable pseudo-release — to the `.spark/<feature>/`
directories that shipped in it, unattributed commits, and each feature's own
`spec`/`plan`/`review`/`qa`/`release` status:

```bash
# JSON: the machine-readable release map
uv run insights releases --as-of 2026-08-19 --repo /path/to/any/git/repo

# HTML: the same data as one self-contained, offline dark-theme page —
# newest release first, drill-down into each one's members and their
# 5-artifact status, each artifact's own full document content expandable
# in place (structured — real headings/tables/checklists, not raw
# Markdown syntax), static #-anchor navigation, zero JavaScript
uv run insights releases --as-of 2026-08-19 --repo /path/to/any/git/repo \
                          --format html --output /tmp/releases-scratch
# writes /tmp/releases-scratch/.aspark-insights/release-board.html
```

- **Newest release first.** The open pseudo-release window leads, then every
  real tag newest-to-oldest — a display-order flip only; `--format json`'s
  own order (and everything below the top level) is untouched.
- **A feature's own documents, not just its status, are one click away.**
  Selecting `spec.md`/`plan.md`/`review.md`/`qa.md`/`release.md` opens that
  file's real content — its actual prose, tables and findings, not just the
  extracted `Status`/`Date`. A feature that shipped in more than one release
  shows its documents once, under its first (newest) appearance; every other
  release links to it rather than repeating it. A document beyond a stated
  size, or the page beyond a stated total weight, is disclosed as such —
  never silently dropped, never grown without bound.

Like `insights board`, this never reads the graph and never invents a
release from a commit-message version string — a version only counts once
it's an actual git tag; everything since the latest one (including a
commit-message-only version like an unpushed `v0.6.0`) shows up in the
trailing `tag: null` entry instead, whose own commit/branch/work-type
figures are `insights board`'s own answer, reused verbatim, never
recomputed a second way.

- **A release can span more than one feature, and that's real, not a bug.**
  This repo's own `v0.3.0` genuinely spans three `.spark/` directories.
- **Membership is decided by changed paths, never by what a commit says
  about itself.** A commit whose subject *names* a feature while touching
  none of its files is never attributed to it by text matching — and a
  feature's own trailing "record the release report" commit routinely lands
  inside the *next* release's range, not the one it shipped under. Both are
  disclosed as they really happened.
- **An unparseable artifact status is `null` with a reason, never a guess.**
  Only the first Markdown table in a `spec.md`/`plan.md`/`review.md`/`qa.md`/
  `release.md` is ever read, and only for `Status`/`Date` — nothing else in
  the file is parsed, so a status that can't be confidently read says so
  honestly instead of pattern-matching around it.

## Project Status

- [x] Package skeleton, `GraphPort` seam to `aspark-graph`, core Fact/Snapshot/
      Provenance model with structural guardrails (`v0.1.0`)
- [x] Real TRC-001…005 (story→task, AC→QA, task→code coverage, orphan/
      unverified counts, evidence confidence-mix) and MTA-001…003 (sample
      sizes, scope-filter disclosure, graph-staleness disclosure) — computed
      and dogfooded against the family's own repos (`v0.2.0`)
- [x] Snapshot report — self-contained, offline HTML render of the latest
      snapshot (`v0.4.0`)
- [x] Measurement honesty — a repo-wide-absent evidence kind reports `null`
      with a reason (disclosing a real `.spark/` artifact if one exists)
      instead of a fabricated `0%`/`100%`, registry-wide (`v0.5.0`)
- [x] Snapshot-report scorecard redesign — per-metric cards, a folded
      confidence-mix bar, the full metrics table always retained beneath
      them (`v0.6.0`)
- [x] Git-native mid-cycle board — `insights board`, a standalone surface
      needing no graph and no `.spark/`: commits/days since the last tag,
      work-type mix, local branches, JSON or self-contained HTML (`v0.7.0`)
- [x] Release board — `insights releases`, mapping every git tag (plus the
      open window since the latest one) to the `.spark/<feature>/`
      directories that shipped in it and each one's own artifact status
      (`v0.8.0`)
- [x] Release board HTML — `insights releases --format html`, a self-
      contained dark-theme offline render matching the live aSPARK brand
      site: index of every release with drill-down into members and
      5-artifact status, zero JavaScript (`v0.9.0`)
- [x] Release board documents — newest-release-first ordering, plus each
      feature's own spec/plan/review/qa/release document content viewable
      in place (structured, real headings/tables/checklists), still one
      self-contained offline file, zero new dependencies (`v0.10.0`)
- [ ] Flow/cycle-time metrics — blocked on `aspark-graph` shipping
      release/commit time data
- [ ] Architecture-health metrics — blocked on further graph scope hygiene
- [ ] Policy-derived compliance metrics — blocked on `aspark-policy` shipping
      an enforcement engine
- [x] MCP server — read-only `query` tool, namesake to the CLI

## Position in the Product Family

| Product | Status | Responsibility |
|---|---|---|
| **[aSPARK Core](https://github.com/a-lottes/aSPARK)** | shipped, `v0.4.0` | Delivery process, roles, gates, templates |
| **[aspark-graph](https://github.com/a-lottes/aSPARK-graph)** | shipped, `v0.7.0` (on PyPI) | Traceability and engineering knowledge graph |
| **[aSPARK-policy](https://github.com/a-lottes/aSPARK-policy)** | shipped, `v0.2.0` (format + catalog; enforcement open) | Enterprise engineering standards and governance |
| **aSPARK-insights** (this repo) | shipped, `v0.8.0` (traceability metrics, HTML report, MCP server, honest nulls, standalone git board, release board) | Engineering metrics and management dashboards |

The graph delivers fact-queries; insights delivers the analytics product —
versioned metric definitions, time series over snapshots, joins, dashboards —
never recomputing what the graph already answers.

## License

[MIT](LICENSE) © 2026 Andreas Lottes. Part of the aSPARK product family.
