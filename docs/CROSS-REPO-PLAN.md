# Cross-Repo-Plan — was der Aufbau von aSPARK-insights in den Nachbar-Repos ändert

**Stand:** 2026-07-25 · **Herkunft:** [ARCHITECTURE-PROPOSAL.md](ARCHITECTURE-PROPOSAL.md) Draft 2
**Ziel-Dokumente:** `~/aSPARK Doku/REVIEW-RESPONSE.md` (Master) · die drei Repo-Backlogs

> **Verfahren.** Die Repo-Sessions sehen einander nicht; es gilt nur, was im Master-Dokument
> steht (dessen §5-Regel). Dieses Dokument ist der **Änderungsvorschlag**: erst hier reviewen,
> dann in einem Zug in Master + betroffene Backlogs übernehmen. Nichts davon ist selbst schon
> normativ.
>
> **Leitprinzip-Check.** „Nichts Neues, bis das Ausgelieferte verbunden ist" — jede vorgeschlagene
> Position verdrahtet oder härtet Vorhandenes bzw. bereits Geplantes. Einziges neues Konzept:
> der Export-Vertrag (C5), und der ersetzt eine heute nötige Interims-Kopplung.

---

## 1. Änderungen am Master-Dokument (`REVIEW-RESPONSE.md`)

### 1.1 Lesereihenfolge ergänzen

| Wer | Liest |
|---|---|
| Session im insights-Repo | `~/aSPARK-insights/.spark/BACKLOG.md` + `~/aSPARK-insights/docs/ARCHITECTURE-PROPOSAL.md` |

### 1.2 §5 — Vertrag C3 erweitern (`touches` auf `part_of`)

Zusatz zur Kanten-Tabelle in C3, **vor** Umsetzung von G1 einplanen:

> | Kante | Richtung | Attribute |
> |---|---|---|
> | `part_of` | `Commit` → `Feature` | `touches`: sortierte Liste aus `{spec, plan, review, qa, release, src, test}` — welche Artefakt-Klassen der Commit berührt hat. Quelle: Pfadliste aus `git.py::commits_touching`, deterministisch. |
>
> Begründung: Phasendauern (Specify→…→Keep) und Rework-Quote sind sonst nicht ableitbar, und
> insights dürfte sie nicht selbst aus git ableiten, ohne einen zweiten Git-Parser neben dem
> Graph zu etablieren (ADR-2 im insights-Repo). Billig: die Pfade liegen in `commits_touching`
> bereits vor, es fehlt nur die Klassifikation nach Verzeichnis/Dateiname.

### 1.3 §5 — neuer Vertrag C5: Graph-Export (graph → insights)

> ### C5 — Graph-Export-Vertrag (graph → insights)
>
> Wird von insights als einziger Bulk-Lesepfad genutzt (Einzel-Queries bleiben C2).
>
> ```
> aspark-graph query export [--repo PATH]
> ```
>
> - Ausgabe: das kanonische Graph-Dokument (`nodes` + `edges`), identisch zum persistierten
>   Inhalt von `.aspark-graph/graph.json`, JSON auf stdout, `sort_keys=True`, Exit 0.
> - Graph nicht gebaut: stderr + Exit 1 (wie C2).
> - **Normativ:** Knoten-/Kantentypen und Pflicht-Attribute aus `model.py` plus C3
>   (Release/Commit) sind damit Vertragsbestandteil gegenüber insights. Umbenennungen sind
>   Breaking Changes und brauchen einen koordinierten insights-Change.
> - Bis C5 ausgeliefert ist, nutzt insights einen bibliotheksbasierten Interim-Adapter
>   (`import aspark_graph`, versionsgepinnt, eine Datei) — **mit Ablaufdatum C5** und sichtbar
>   in jeder Snapshot-Provenance (`"graph_access": "library-interim"`).

### 1.4 §4-Tabellen ergänzen

„Sofort" ergänzen um:

| # | Maßnahme | Repo | Neues Konzept? |
|---|---|---|---|
| 12 | Default-Scope-Excludes im Builder (`.claude/worktrees/**`, `.venv/**`, `node_modules/**`) | **graph** | nein — Datenqualitäts-Bug |
| 13 | insights-Foundation + Traceability-Metriken gegen v0.5.0 (I1/I2) | **insights** | ja (neues Repo, konsumiert nur Vorhandenes) |

„Danach" ergänzen um: `query export` als Vertrag C5 (**graph**, G6) · Provenance-Header in
`graph.json` (**graph**, G8; Handbuch §10.3 verspricht ihn bereits) · Flow-Metriken in insights
nach G1/G2 (I3).

### 1.5 §6-Tabelle ergänzen

| Repo | `.spark` in `.gitignore`? | Konsequenz |
|---|---|---|
| `aSPARK-insights` | **offen — Repo ist noch nicht `git init`-ed** | Vor dem ersten Push bewusst entscheiden (Präzedenz: Core/graph öffentlich, policy lokal). |

### 1.6 Handbuch-Korrektur vormerken (läuft über Core-Item C2, siehe §3)

Der „Metrics contract — workflow and gate telemetry as structured events" (Handbuch §7.3,
Producer: Core, Consumer: Insights) wird **ersatzlos zurückgezogen**: Zeitdaten kommen nach
G1/G2 aus dem Graph (git-abgeleitet, retroaktiv — was Events nie könnten), Zustände aus den
Artefakten. Ein Event-Emitter widerspräche zudem der zustandslosen Engine („die Artefakte
sind der Zustand", §11.2). Insights' Abhängigkeitszeile in §7.2 ändert sich entsprechend:
`aSPARK Core → Insights` entfällt; es bleiben Graph und Policy.

---

## 2. Neue Einträge für `~/aSPARK-graph/.spark/BACKLOG.md`

Einbaufertig im Format des Backlogs. Nummerierung schließt an G5 an.

---

### G6 · `export-query` — der Graph als Bulk-Lesevertrag

**Priorität: Danach, idealerweise direkt nach G1** (dann enthält der Export Release/Commit von
Anfang an). Erster Konsument: `aSPARK-insights` (Coverage-Metriken brauchen den ganzen Graphen,
nicht Einzel-Queries — Einzelaufrufe wären O(Features × Stories) Subprozesse).

Aufwand ist klein: die Persistenz ist bereits kanonisch (`sort_keys`, stabile Ordnung wegen
AC-1.2) — `export` ist im Kern „lade Graph, drucke kanonisch auf stdout". Der Wert liegt im
Vertragsstatus: ohne Export liest insights entweder `.aspark-graph/graph.json` direkt (verboten,
Anti-Corruption-Regel) oder importiert `aspark_graph` als Bibliothek (Interims-Kopplung mit
Ablaufdatum). Mit Export ist insights ein reiner CLI-Konsument wie die Core-Gates.

```
/spark export-query — neue Query `export`, die das kanonische Graph-Dokument (nodes + edges,
identisch zum Inhalt von .aspark-graph/graph.json) als JSON auf stdout ausgibt, sort_keys=True,
Exit-Verhalten wie alle Queries (Graph nicht gebaut → stderr + Exit 1). CLI und MCP namensgleich.
Damit werden Knoten-/Kantentypen und Pflicht-Attribute zum Vertrag gegenüber aSPARK-insights
(Master-Dokument §5/C5) — Umbenennungen sind ab dann koordinierte Breaking Changes.
```

---

### G7 · `scope-excludes` — Worktrees und Vendor-Verzeichnisse nicht indexieren

**Priorität: Sofort. Datenqualitäts-Bug im ausgelieferten Produkt, kein Feature.** Verifiziert
am eigenen Repo (2026-07-25): von 98 File-Knoten liegen **49 in `.claude/worktrees/`**, und alle
49 verschatten eine echte Datei — die Hälfte der Code-Schicht ist ein Duplikat. Jede
`impact`-Antwort und jedes Kopplungsmaß ist damit heute um ~2× verzerrt, und C1 (graph-gates in
Core) verdrahtet genau diese Antworten gerade in die Gates.

Umfang:
- Default-Excludes im Builder: `.claude/worktrees/**`, `.venv/**`, `node_modules/**`,
  `.git/**` — plus projektspezifische Erweiterung über Konfiguration (Handbuch §A.1 sieht
  `include`/`exclude` bereits vor; hier reicht die minimale Form).
- Ausgeschlossenes wird beim Build **gemeldet** (Anzahl, Muster), nicht still verworfen —
  insights übernimmt die Zahl in seine Snapshot-Provenance.
- Determinismus: Excludes sind Teil der Build-Eingabe, gleiche Eingaben → gleicher Graph.

```
/spark scope-excludes — Default-Ausschlussmuster im Builder (.claude/worktrees/**, .venv/**,
node_modules/**, .git/**) plus minimale exclude-Konfiguration. Belegter Anlass: 49 von 98
File-Knoten des eigenen Repos stammen aus einem Claude-Code-Worktree und duplizieren die echte
Code-Schicht 1:1 — impact/gate_health sind damit verzerrt, während Core-Item C1 sie in die
Gates verdrahtet. Ausschlüsse werden beim Build gemeldet (Anzahl + Muster). Byte-stabiler
Rebuild (AC-1.2) bleibt erhalten.
```

---

### G8 · `provenance-header` — der Graph bürgt für seine eigenen Eingaben

**Priorität: Danach.** Das Handbuch (§10.3) führt „full provenance sealing (commit hash,
builder version, output digest)" bereits als „planned for a future release" — hier wird es ein
Backlog-Item statt eines Versprechens. Erster Konsument: insights, dessen Snapshots heute
selbst `git rev-parse HEAD` + Datei-Digest notieren müssen (`"sealed": false`) und damit nur
belegen können, *welchen* Graphen sie lasen — nicht, dass er zu diesem Commit gehört.

Umfang: `provenance`-Block in `graph.json` (builder-Version, Quell-Commit, Digest über den
kanonischen Inhalt), Ausgabe auch über `query export` (G6) und eine kleine
`query provenance`. Achtung Selbstbezug: der Digest deckt den Inhalt **ohne** den
Provenance-Block ab, sonst ist er nicht berechenbar.

```
/spark provenance-header — graph.json um einen provenance-Block ergänzen (builder-Version,
Quell-Commit, sha256-Digest über den kanonischen Inhalt ohne den Block selbst) und über die
Queries export/provenance zugänglich machen. Löst das Handbuch-Versprechen aus §10.3 ein;
erster Konsument ist aSPARK-insights (bis dahin markieren dessen Snapshots "sealed": false).
Byte-Stabilität: gleiche Eingaben → identischer Block.
```

---

### Scope-Notiz zu G1 (vor Umsetzung lesen)

> **Aus dem insights-Plan:** `part_of`-Kanten bitte mit `touches`-Attribut anlegen (sortierte
> Liste aus `{spec, plan, review, qa, release, src, test}` — welche Artefakt-Klassen der Commit
> berührt hat; Klassifikation aus der Pfadliste, die `commits_touching` ohnehin hat). Ohne das
> sind Phasendauern und Rework-Quote nicht ableitbar, und insights müsste einen zweiten
> Git-Parser bauen — genau die Doppel-Wahrheit, die die Plattform vermeidet. Vertragsform in
> Master-Dokument §5/C3 (Erweiterung, siehe Cross-Repo-Plan §1.2).

---

## 3. Ergänzungen für `~/aSPARK/.spark/BACKLOG.md` (Core)

Keine neuen Items — zwei Scope-Notizen an bestehenden:

### Zu C2 · `handbook-maturity`

> **Aus dem insights-Plan, im selben Durchgang erledigen:**
> 1. Handbuch §7.3: den „Metrics contract" (Core → Insights, „workflow and gate telemetry as
>    structured events") als **zurückgezogen** kennzeichnen — ersetzt durch git-abgeleitete
>    Zeitdaten im Graph (G1/G2), die retroaktiv funktionieren, was Events nie könnten. §7.2
>    entsprechend: Abhängigkeit `Insights → Core` entfällt.
> 2. Handbuch §3.5 + §6.4.3: einen Grenzsatz ergänzen — *der Graph liefert Fakten-Queries
>    (auch aggregierte wie `dora`), insights liefert das Analytik-Produkt: versionierte
>    Metrik-Definitionen, Zeitreihen über Snapshots, Joins mit Policy, Dashboards.* Verhindert,
>    dass die beiden Produkte einander in die Spur laufen (ADR-0 im insights-Repo).

### Zu C4 · `release-evidence`

> **Zweiter Konsument:** neben der DORA-Query (G2) hängt auch `aSPARK-insights` an
> `Release.date`/`Release.commit` (Flow-Metriken I3). Ändert nichts am Scope — erhöht nur die
> Priorität, die Kopftabelle von `release-notes.md` deterministisch befüllbar zu machen.

---

## 4. Ergänzung für `~/aSPARK-policy/.spark/BACKLOG.md`

Keine neuen Items — eine Scope-Notiz:

### Zu P3 · `check-compiler`

> **Aus dem insights-Plan:** die Ausgabeform des Compilers (Findings mit Regel-ID, Severity,
> Ort, Evidenz — getrennt nach maschinell vs. `review`-Klasse) wird der **Validation-Vertrag**
> für `aSPARK-insights` (Compliance-Metriken I8: Violation-Dichte, Waiver-Debt,
> Mechanik-vs.-Urteil-Anteil). Beim Umsetzen die Form im Master-Dokument §5 als Vertrag
> festhalten; stabile Regel-Identifier sind dafür Voraussetzung (liegt auf der P1/P2-Linie,
> die auch die `Policy`-Knoten im Graph entsperrt). insights konsumiert **nur** maschinelle
> Ergebnisse als Metrik-Input; `review`-Aufträge erscheinen getrennt (MTA-004), nie in
> Durchschnitte gemischt.

---

## 5. Wellenplan — wer wann, mit Abhängigkeiten

| Welle | graph | Core | policy | insights |
|---|---|---|---|---|
| **1 · Sofort** | G1 (mit `touches`) → G2 · G3 · **G7** | C1 · C2 (mit §7.3-Rückzug) | P1 | **I1 · I2** — erste echte Zahlen, nur gegen v0.5.0 |
| **2 · Danach** | **G6** · G5 ⇄ C3 · G8 | C4 (nach G1) · C3 ⇄ G5 | P2 · P4–P6 | **I3** (nach G1/G2) · I4 (nach G7) · I5 (inkl. CI-Snapshot-Aufnahme = geteilte Team-Zeitreihe) · I7 |
| **3 · Später** | G4 (PyPI) · `Policy`-Knoten (nach P1/P2) | — | **P3** (+ Vertrag in §5) | I6 · **I8** (nach P3 + Policy-Knoten) · I9 (nach Entscheid Fleet vs. lokal) |

Kein Zirkel: insights konsumiert nur; alle Pfeile zeigen zur Stabilität (Handbuch §7.1).
I1/I2 hängen an nichts — der Beweis („echte Coverage-Zahlen auf den Familien-Repos") ist
sofort lieferbar und stärkt die Positionierung „Zwei Produkte, ein Beweis", statt ihr ein
drittes Versprechen hinzuzufügen.

---

## 6. Offene Entscheidungen vor dem Einpflegen

1. **`touches` in G1 aufnehmen — ja/nein?** Bei Nein: insights baut den dokumentierten
   Interim-Git-Adapter (ADR-2-Fallback) und FLW-005/007 bleiben Näherungen.
2. **G7-Priorität bestätigen** („Sofort" begründet über C1-Gates; alternativ in G3 falten —
   dort ist ohnehin Größen-/Tiefenbegrenzung beim Parsen geplant).
3. **insights' `.spark/` öffentlich oder lokal?** Vor `git init` entscheiden (§1.5).
4. **Reihenfolge G6 vs. I2:** I2 startet mit dem Interim-Adapter und wechselt bei G6 — oder
   G6 zieht vor I2 und der Interim-Adapter entsteht nie. Zweiteres ist sauberer, kostet aber
   graph-seitig einen kleinen Einschub vor bzw. neben G1.
