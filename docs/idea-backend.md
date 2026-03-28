# Backend Ideas (V0)

## 1. Supply Chain Connections Scraper

### Accepts

- `GET /api/v1/supply-chain/singapore/connections`
- Optional query: `refresh=true|false` (default `false`)

### Returns

- JSON: `country -> { energy: [...], food: [...] }`
- Country key uses full country name.
- Commodity values are standardized labels.

### Used For

- Dependency baseline for Singapore supply chains.
- Input context for downstream features, especially disruption relevance checks.

### High-Level Pseudocode

1. Receive request.
2. If cache exists and `refresh=false`, return cached payload.
3. Run TinyFish retrieval for latest available-year Singapore import links.
4. Use LLM curation to normalize country and commodity naming, and classify into `energy` or `food`.
5. Build deterministic output and cache it.
6. Return response.

## 2. Updated News Curator

### Accepts

- `GET /api/v1/news-curator/singapore`

### Returns

- JSON with:
  - `internal`: ranked article list
  - `external`: ranked article list

### Used For

- Frontend recent-news risk panel around Singapore supply-chain signals.

### High-Level Pseudocode

1. Retrieve candidates with TinyFish for last 14 days.
2. Expand to 31 days if relevant coverage is insufficient.
3. Deduplicate by lowercased title.
4. Classify into `internal` or `external` with internal priority on overlap.
5. Build hook from first 2 sentences (article body, fallback to snippet).
6. Rank by severity, directness, freshness.
7. Return up to 3 items per bucket.

## 3. Disruption Monitor

### Accepts

- Scheduled pipeline (daily, SGT) with no overlapping runs.

### Returns

- Persisted disruption events in local database.
- Emitted payload only for:
  - newly created events
  - meaningfully updated existing events

Emitted payload shape:

```json
{
  "event_id": "evt_001",
  "from_country": "Iran",
  "severity": "CRITICAL",
  "resource_types": {
    "energy": ["Crude Oil"]
  },
  "headline": "Iran-linked disruption threatens Singapore energy imports"
}
```

### Used For

- Primary app data layer: disruption history and latest disruption state.
- Foundation for future app features built on top of persisted events.

### High-Level Pseudocode

1. Start scheduled run (skip if another run is active).
2. Collect reputable source documents with TinyFish.
3. Normalize raw documents and classify candidates.
4. Discard non-emittable candidates.
5. Discard candidates with unknown `from_country`.
6. Treat candidates with empty `resource_types` object as non-disruptions.
7. Match candidates to existing events using rule-based keys (`from_country` + commodity overlap).
8. If no match, create new event with stable `event_id`.
9. If match, update stored event only when meaningful changes exist.
10. Emit only new/updated events.
11. Complete run with status `completed`, `failed`, or `skipped_overlap`.

### Rules

- Severity values: `WARNING`, `CONSTRAINED`, `DISRUPTED`, `CRITICAL`.
- One strong reputable source is enough.
- Unconfirmed but credible signals map to `WARNING`.
- `resource_types` supports only `food` and `energy`.
- Include only disrupted resource keys and disrupted commodity values.
- All disruption events must be persisted.
- Preferred V0 database is local SQLite with JSON support (JSON1).

## 4. Resolution Preparation Stage

### Accepts

- `POST /api/v1/resolution/prep/start`
- `GET /api/v1/resolution/prep/{workflow_id}`

Kickoff input includes:
- `event_id` (persisted disruption event)
- `resource_type` (`food` or `energy`)
- optional `commodity`
- optional `max_substitutes`

### Returns

- Kickoff returns `workflow_id` and the origin-country packet (`Singapore`) as soon as it is ready.
- Substitute-country packet curation continues in background.
- Retrieval endpoint returns workflow stage, per-country statuses, and available packets.

### Used For

- Pre-debate curation stage that prepares structured country briefing packets.
- Shared packet store for downstream debate/resolution phases.

### High-Level Pseudocode

1. Receive kickoff payload.
2. Load disruption event from database by `event_id`.
3. Load substitute-country snapshots from database (prepared by Disruption Monitor).
4. Normalize request and check for an existing matching workflow.
5. If matching workflow exists, reuse the same `workflow_id`.
6. Manager creates an information checklist per country based on fixed dimensions and country role.
7. Orchestrator starts one country worker per country in parallel.
8. Each worker uses TinyFish retrieval + curation against manager checklist.
9. Manager evaluates whether packet information is sufficient for each country.
10. If insufficient, manager sends missing-information checklist back to orchestrator for another bounded retrieval pass.
11. Return response immediately once origin-country packet is ready.
12. Continue substitute-country workers in background.
13. Persist workflow state, country statuses, and packets under the same `workflow_id`.

### Rules

- This stage does not run debate or choose final substitute.
- Origin-country packet is response-critical; substitute packets are completion-critical.
- All packet records and status transitions are persisted.
- Repeated kickoff with same normalized input must reuse the same workflow.
- Country packet structure must be canonical and source-traceable for later phases.
- Every worker context must include country objective:
  - Singapore: maximize supply resilience.
  - Non-Singapore countries: maximize export profit while controlling domestic risk.
