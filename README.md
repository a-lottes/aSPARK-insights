# 📊 aspark-insights

> **Real, hand-verifiable engineering metrics computed from your repo's actual delivery graph — never a second-guessed number, never a fabricated one.**

> **Project status: shipped at `v0.2.0` — real traceability coverage, not yet dashboards.**
> You can build a snapshot today and get real Story→Task, AC→QA and Task→Code
> coverage numbers, each with its own sample size, computed against
> [aspark-graph](https://github.com/a-lottes/aSPARK-graph)'s facts (see
> [Install](#install) and [Usage](#usage)). What's still missing: dashboards
> (static HTML), flow/cycle-time metrics, architecture-health metrics, and
> policy-derived compliance metrics — all future increments. Not yet on PyPI —
> see [Install](#install) for the source-only setup.

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

# Not yet implemented — exits 1 with a named error rather than succeeding silently
uv run insights render
```

`insights build` requires a graph already built by `aspark-graph build` at the
target repo — it never builds one itself. Every metric reports a real value
with its sample size, or an honest `null` with a reason (e.g. `"no Story nodes
found in graph"`) when there's nothing to measure yet.

### MCP

`insights serve` runs a **read-only** stdio MCP server exposing one tool,
`query`, name-matched to the CLI subcommand it wraps:

```bash
uv run insights serve --repo ../aSPARK-graph --output /tmp/insights-scratch
```

The repo/output location is fixed once at launch — `query` takes **no arguments**, so it can never be pointed anywhere else per call, and it never triggers a fresh `build`. See [SECURITY.md](SECURITY.md) for the trust boundary and non-guarantees.

## Project Status

- [x] Package skeleton, `GraphPort` seam to `aspark-graph`, core Fact/Snapshot/
      Provenance model with structural guardrails (`v0.1.0`)
- [x] Real TRC-001…005 (story→task, AC→QA, task→code coverage, orphan/
      unverified counts, evidence confidence-mix) and MTA-001…003 (sample
      sizes, scope-filter disclosure, graph-staleness disclosure) — computed
      and dogfooded against the family's own repos (`v0.2.0`)
- [ ] Dashboards — static HTML, offline-first (planned)
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
| **aSPARK-insights** (this repo) | shipped, `v0.2.0` (real traceability metrics; dashboards ahead) | Engineering metrics and management dashboards |

The graph delivers fact-queries; insights delivers the analytics product —
versioned metric definitions, time series over snapshots, joins, dashboards —
never recomputing what the graph already answers.

## License

[MIT](LICENSE) © 2026 Andreas Lottes. Part of the aSPARK product family.
