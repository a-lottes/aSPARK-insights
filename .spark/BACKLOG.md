# Backlog — aSPARK-insights

**Stand:** 2026-07-25 · **Repo-Version:** — (noch kein Code, noch kein `git init`) · **Reifegrad:** Geplant
**Master-Dokument:** `~/aSPARK Doku/REVIEW-RESPONSE.md` (normative Cross-Repo-Verträge in §5)
**Architektur:** [`docs/ARCHITECTURE-PROPOSAL.md`](../docs/ARCHITECTURE-PROPOSAL.md) (Draft 2) ·
Cross-Repo-Deltas: [`docs/CROSS-REPO-PLAN.md`](../docs/CROSS-REPO-PLAN.md)

> **Für die Session in diesem Repo.** Autonom lesbar — was du über die Nachbarn wissen musst,
> steht in §2. Reihenfolge ist Abhängigkeitsreihenfolge.
>
> **Vor dem ersten Commit entscheiden:** ob `.spark/` hier öffentlich wird (Präzedenz: Core und
> graph getrackt/öffentlich, policy lokal — Master-Dokument §6). Das Repo ist noch nicht
> `git init`-ed; die Entscheidung ist noch frei.

## 1. Wo dieses Repo steht

Leeres Repo. Insights ist das vierte Produkt der Familie („Geplant" auf Website und im
Handbuch) und beantwortet „how are we doing?" aus Graph, git-abgeleiteter Zeit und — später —
Policy-Validierung. Die zwei Sätze, die jede Session hier binden:

> **Grenze (ADR-0):** Der Graph liefert Fakten-Queries (auch aggregierte wie `dora`);
> insights liefert das Analytik-Produkt — versionierte Metrik-Definitionen, Zeitreihen über
> Snapshots, Joins, Dashboards. Nichts nachrechnen, was der Graph schon beantwortet.
>
> **Determinismus (ADR-4):** Kein `datetime.now()` im Ableitungspfad. `as_of` ist Eingabe und
> steht in der Provenance jedes Snapshots. Snapshot zweimal bauen ⇒ byte-identisch (CI-Kanarie).

Härteste Design-Konsequenz vorab: **keine Metriken auf Personenebene, nie** — gemessen werden
Systeme, Features, Code. Und keine erfundenen Zahlen: MTTR bleibt `null` mit Begründung (wie
in G2 entschieden).

## 2. Was du über die Nachbar-Repos wissen musst

### `aspark-graph` v0.5.0 — Shipped; die Hauptquelle

CLI + MCP namensgleich, JSON auf stdout (`sort_keys=True`), Exit 1 bei ungebautem Graph.
Queries: `get_node` · `story_trace` · `impact` · `gate_health` · `staleness` · `find_nodes` ·
`get_neighbors` · `shortest_path`. **Geplant dort (Sofort):** G1 `release-nodes`
(Release/Commit-Knoten mit Datum, Kanten `released_as`/`part_of`) und G2 `dora-query`
(3 von 4 DORA-Metriken, MTTR ehrlich `null`). **Von hier vorgeschlagen:** G6 `export`
(Bulk-Vertrag §5/C5), G7 `scope-excludes` (49/98 File-Knoten sind Worktree-Duplikate!),
G8 `provenance-header`, `touches`-Attribut auf `part_of` (§5/C3-Erweiterung).

**Bindend für dieses Repo:** Bulk-Zugriff bis G6 nur über den einen Interim-Adapter in
`ports/graph.py` (versionsgepinnt, Ablaufdatum G6, `"graph_access": "library-interim"` in der
Provenance). Niemals `.aspark-graph/graph.json` direkt parsen.

### `aspark-policy` v0.1.0 — Frühphase; noch keine Quelle

11 Packs + JSON-Schema, aber kein Resolver, keine CLI. Anschluss erst nach dortigem
P3 (`check-compiler`): dessen Report-Form wird der Validation-Vertrag für I8. Bis dahin:
Null-Adapter, Compliance-Ansichten **ausgeblendet, nicht simuliert**.

### `aSPARK` Core v0.3.1 — Shipped; Lieferant der Artefakte

Die `.spark/`-Templates sind über Vertrag §5/C1 mit dem Graph gekoppelt (`TemplateDriftError`
bei Drift). Insights erbt Ausfälle laut: fehlender/kaputter Graph ⇒ Fehler, nie ein leeres
Dashboard. Der Handbuch-„Metrics contract" (§7.3, Core → Insights) ist zum Rückzug
vorgeschlagen — nicht darauf bauen.

## 3. Features in Abhängigkeitsreihenfolge

### I1 · `foundation` — Gerüst, Modell, Determinismus-Kanarie

**Priorität: Sofort. Hängt an nichts.** Familien-Stack (Python ≥ 3.11, `uv`, `hatchling`,
`argparse`, committed `uv.lock`), Paket `aspark_insights` mit `ports/` (GraphPort: CLI-Adapter
+ Interim-Lib-Adapter; PolicyPort: Null-Adapter), `model/` (Fact, Snapshot, Provenance,
MetricValue), Metrik-Registry (ADR-3: reine Funktionen, einzeln versioniert), CLI-Skelett
`build | query | render | diff | verify` im C2-Idiom, `.aspark-insights/` als zweites
Derived-State-Verzeichnis (gitignored). CI-Kanarie: zweimal bauen, byte-vergleichen.

```
/spark foundation — Repo-Gerüst für aspark-insights im Familien-Stack: Paket, Ports
(GraphPort mit CLI- und versionsgepinntem Interim-Lib-Adapter, PolicyPort als Null-Adapter),
Fact/Snapshot/Provenance-Modell, Metrik-Registry als versionierte reine Funktionen, CLI-Skelett
(build/query/render/diff/verify, JSON auf stdout, sort_keys, Exit 1 mit benanntem Fehler),
Determinismus-Kanarie im CI (Doppel-Build byte-identisch). Bindend: kein datetime.now() im
Ableitungspfad (as_of ist Eingabe), .aspark-insights/ ist löschbar und deterministisch
rebuildbar. Details in docs/ARCHITECTURE-PROPOSAL.md §4–§6.
```

### I2 · `traceability-metrics` — die ersten echten Zahlen

**Priorität: Sofort nach I1. Läuft gegen graph v0.5.0, braucht keinen Nachbar-Change.**
TRC-001…005 (Story→Task-, AC→QA-, Task→Code-Coverage, Orphans via `gate_health`,
Confidence-Mix) + MTA-001…003 (n pro Metrik, Frische via `staleness`, ScopeFilter-Ausschlüsse
in der Provenance — Interim-Gegenstück zu G7). Snapshot-Store mit versiegelter Provenance.
Dogfood: Zahlen auf den Familien-Repos — dort liegt heute z. B. **132 ACs / 16 `verifies`**.

```
/spark traceability-metrics — TRC-001..005 und MTA-001..003 als erste Registry-Metriken,
berechnet über den GraphPort gegen aspark-graph v0.5.0; ScopeFilter mit Ausweis der
Ausschlüsse (.claude/worktrees/** u. a.) in der Snapshot-Provenance; Snapshot-Store unter
.aspark-insights/. Abnahme: reale Coverage-Zahlen auf aSPARK-graph und aSPARK-policy,
Doppel-Build byte-identisch, n wird pro Metrik mitgeliefert. Kein Nachbar-Repo-Change nötig.
```

### I3 · `flow-metrics` — Zeit, aus dem Graph

**Blockiert durch G1 + G2 im graph-Repo** (dort „Sofort"; `touches`-Erweiterung für
FLW-005/007 — sonst dokumentierter Interim-Git-Adapter als Fallback, ADR-2). `dora` wird
**durchgereicht und verpackt** (Definition-Version + Provenance), nie nachgerechnet. Dazu
Phasendauern, WIP (Zeitreihe über Snapshots), Rework-Quote. MTTR: `null` durchreichen.

### I4 · `architecture-health` — ARC-001…004

Import-Zyklen (SCCs), Instabilität `Ce/(Ca+Ce)`, Kopplungstrend, God-Files. **Ehrlich erst
mit sauberem Scope** — nach G7, sonst nur mit ScopeFilter und ausgewiesener Verzerrung.

### I5 · `dashboards` — statisches HTML, drei Rollen + Team-Betriebsmodell

Self-contained HTML (ADR-5: offline-first, air-gap, kein zweiter Toolchain) für Developer /
Architect / Engineering Manager, aus dem Snapshot-JSON. Renderer verweigert Trendlinien
unter n-Schwelle (MTA-001). Nach I2.

**Dazu der Multi-Developer-Betrieb** (Proposal §8.1): Zeitreihen-Assembly aus einem
Snapshot-Verzeichnis plus dokumentierte CI-Workflow-Vorlagen — CI baut pro Merge auf `main`
(`insights build --as-of <commit-datum>`, nie die Runner-Uhr), legt Snapshots als Artefakt
oder auf einem Metrics-Branch ab und veröffentlicht die Dashboards. Lokale Snapshots sind
Wegwerf-Ansichten; die geteilte Zeitreihe lebt in CI. Gleicher Commit ⇒ byte-identische
Zahlen lokal wie in CI (Determinismus-Kanarie). Schwellwert-Gating bleibt aspark-ci.

### I6 · `debt-indicators` — DBT-001…004

Finding-Dichte/-Hotspots (heute möglich), Stale-Artifacts (nach G1), Untested-Change-Rate
(nach G2, `is_test`). Nach I3.

### I7 · `mcp-server` — Insights für Agenten

Read-only-MCP über Snapshots, namensgleich zur CLI (Familien-Idiom). Nach I2. Vorher
`SECURITY.md` im Geist von G3 (kleiner: keine Pfad-Parameter nach außen, kein Build-Tool
über MCP exponieren).

### I8 · `policy-metrics` — Compliance-Analytik

**Blockiert durch policy P1–P3 + `Policy`-Knoten im Graph** (dort bewusst erst nach stabilen
Regel-IDs). DBT-005/006, ARC-005, MTA-004 (Mechanik- vs. `review`-Anteil — nie mischen).

### I9 · `fleet` — Mehr-Repo-Aggregation

**Blockiert durch Entscheidung** „per-Repo-Transparenz vs. Fleet zuerst" (offene Frage 1 im
Architektur-Vorschlag). Bis dahin nicht anfangen.

## 4. Bewusst nicht in diesem Backlog

| Idee | Warum nicht |
|---|---|
| Personen-/Entwickler-Metriken | **Nie.** Zerstört das Vertrauen, auf dem die Evidenz beruht; korrumpiert die Datenquelle. Design-Constraint, keine Einstellung. |
| Eigener Git-Parser | Zeit ist nach G1/G2 ein Graph-Fakt. Zwei Ableitungen derselben Wahrheit sind das Silo, das die Plattform abschafft (ADR-2). Nur der dokumentierte Fallback, falls `touches` abgelehnt wird. |
| DORA nachrechnen | `query dora` (G2) wird verpackt, nicht dupliziert (ADR-0). |
| Schwellwert-Enforcement | Messen hier, Durchsetzen in aspark-ci (konsumiert insights-JSON). Handbuch §2.4. |
| BI-/Warehouse-Anschluss, Ticket-Integration | JSON raus reicht; Ticket-Metadaten sind genau die Quelle, die ersetzt wird (§2.1.5). |
| LLM im Ableitungspfad | P1. Agenten lesen via MCP; kein KPI wird generiert. |
| MTTR erfinden | `null` mit Begründung ist das Produkt, nicht die Lücke (wie G2). |
| Shared `aspark-common` | Von der Familie schon beantwortet (P5: keine Kopplungsschmuggel-Bibliotheken); der Export-Vertrag G6/C5 ersetzt den Bedarf. |
