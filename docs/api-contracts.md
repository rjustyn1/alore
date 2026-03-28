# API Contracts

## Supply Chain Connections (Singapore)

### Purpose

Return Singapore import supply-chain connections grouped by source country and resource category.

### Primary Endpoint

- Method: `GET`
- Path: `/api/v1/supply-chain/singapore/connections`

### Query Parameters

- `refresh` (optional): `true` or `false`
- Default: `false`
- Behavior:
  - `false`: return cache when available
  - `true`: force re-scrape and refresh cache

### Success Response

- Status: `200 OK`
- Body type: `application/json`
- Envelope schema:
  - `status`: `"ok"`
  - `data.source`: `live` | `cache_stale` | `fallback_seed`
  - `data.connections`: country map
  - `message`: `null`

Example:

```json
{
  "status": "ok",
  "data": {
    "source": "live",
    "connections": {
      "Indonesia": {
        "energy": ["crude_oil", "natural_gas"],
        "food": ["rice", "palm_oil"]
      },
      "Australia": {
        "energy": ["coal"],
        "food": ["wheat", "beef"]
      }
    }
  },
  "message": null
}
```

### Data Rules

- Data scope: latest available year.
- Country keys: full country names only.
- Commodity values: canonical labels only (normalized).
- Every country object should include both `energy` and `food` keys.
- Use empty array when no commodity exists for a category.

### Compatibility Endpoint

- Method: `POST`
- Path: `/api/v1/supply-chain/scrape`
- Request body:

```json
{
  "resource": "energy"
}
```

- `resource` accepted values: `energy`, `food`
- Returns envelope with:
  - `data.resource`
  - `data.source` (`live` | `cache_stale` | `fallback_seed`)
  - `data.connections` (country -> commodity array for the selected resource)

### Processing Contract (Server-Side)

1. Run TinyFish scraping agent for Singapore import-source data.
2. Curate raw scraper output with OpenAI LLM:
   - normalize country names
   - normalize commodity names
   - classify into `energy` or `food`
3. Aggregate and return stable schema.
4. Cache response in memory.

## Updated News Curator (Singapore)

### Purpose

Return recent public news relevant to Singapore supply-chain risk for `food` and `energy`, grouped as `internal` and `external`.

### Endpoint

- Method: `GET`
- Path: `/api/v1/news-curator/singapore`

### Query Parameters

- None in V0.

### Success Response

- Status: `200 OK`
- Body type: `application/json`
- Envelope schema:
  - `status`: `"ok"`
  - `data.internal`: array of ranked article objects
  - `data.external`: array of ranked article objects
  - `message`: `null`

Example:

```json
{
  "status": "ok",
  "data": {
    "internal": [
      {
        "rank": 1,
        "title": "Title Internal 1",
        "hook": "First 2 sentences 1",
        "url": "link 1"
      }
    ],
    "external": [
      {
        "rank": 1,
        "title": "Title External 1",
        "hook": "First 2 sentences 1",
        "url": "link 1"
      }
    ]
  },
  "message": null
}
```

### Retrieval Rules

- TinyFish retrieval/scraping is primary.
- Retrieve within last 14 days first.
- Expand to 31 days if relevant candidates are insufficient.
- Deduplicate by lowercased title before ranking.

### Classification Rules

- Internal:
  - explicit Singapore mention
  - direct impact discussion (supply chain, imports, logistics, food, or energy)
- External:
  - no explicit Singapore mention
  - strong implied immediate operational impact to Singapore
- If both conditions are met, classify as `internal`.

### Dependency Basis for External Classification

- Use supply-chain cache if available.
- If unavailable, use broader Singapore-relevance judgment.

### Ranking Rules

- Rank by severity, directness to Singapore impact, and freshness.
- Freshness uses article publish time in UTC.

### Edge Cases

- Return fewer than 3 items if good candidates are limited.
- Do not place the same article in both arrays.

## Disruption Monitor (Scheduled Pipeline, Singapore-Implicit)

### Purpose

Detect Singapore-relevant supply chain disruptions, persist structured events, and emit only new or meaningfully updated events.

### Trigger Contract

- Trigger type: scheduled job (not request-driven).
- Schedule: daily in SGT.
- Overlap policy: no concurrent runs.
- Run outcomes: exactly one of `completed`, `failed`, `skipped_overlap`.

### Collection Contract

- Primary retrieval method: TinyFish/TinyFetch.
- Source modes: trusted-source list and dynamic discovery/search.
- Trust policy: reputable sources only.
- Normalized raw document minimum fields:
  - `source_id`
  - `url`
  - `title`
  - `content`
  - `collected_at`

### Classification Contract

- One strong reputable source is sufficient.
- Classifier output is either:
  - non-emittable, or
  - emittable candidate with minimum fields:
    - `from_country`
    - `severity`
    - `resource_type`
    - `commodity`
    - `headline`
- Unknown `from_country` candidates must be discarded.

### Severity Contract

- Allowed values only:
  - `WARNING`
  - `CONSTRAINED`
  - `DISRUPTED`
  - `CRITICAL`
- Unconfirmed but credible alerts map to `WARNING`.

### Commodity Contract

- One disruption event must represent exactly one commodity.
- `resource_type` allowed values: `food`, `energy`.
- `commodity` must be normalized snake_case.
- If no commodity is detected, candidate must not be emitted.

### Identity, Persistence, and Update Contract

- Every new stored event must receive stable `event_id`.
- All disruptions must be stored in local database.
- Existing incidents must be updated, not recreated as unrelated new records.
- Match basis is rule-based using at least:
  - `from_country`
  - `resource_type`
  - `commodity`
- Meaningful updates include:
  - severity changed
  - headline changed
  - supporting evidence expanded

### Emission Contract

- Emit only newly created or meaningfully updated events.
- Do not re-emit unchanged events.
- Emitted payload must contain:
  - `event_id`
  - `from_country`
  - `severity`
  - `resource_type`
  - `commodity`
  - `headline`
- `source_urls` (list of supporting article links)
- Emitted payload should not contain:
  - `to_country`
  - `status`
  - `impact_scope`
  - `event_time`
  - `reason`

Example emitted payload:

```json
{
  "event_id": "evt_001",
  "from_country": "Iran",
  "severity": "CRITICAL",
  "resource_type": "energy",
  "commodity": "crude_oil",
  "headline": "Iran-linked supply disruption threatens Singapore energy imports",
  "source_urls": ["https://example.com/disruption-article"]
}
```

### Event Read Endpoints

- `GET /api/v1/disruptions/events?limit=100`
  - returns persisted events (most recent first), including `source_urls`
- `GET /api/v1/disruptions/events/{event_id}`
  - returns one persisted event by id, including `source_urls`

### Storage Flexibility Requirement

- Database schema must support future column additions.
- Database must support JSON field storage for nested structures and future extensibility.
- Preferred V0 local database: SQLite (JSON1 enabled).

## Resolution Preparation Stage (Pre-Debate Curation)

### Purpose

Start and track a country-packet curation workflow for the debate stage. The goal is to prepare source-backed context per country so later debate agents can reason about:
- Singapore objective: maintain resilient supply continuity.
- Other-country objective: capture export profit while avoiding domestic citizen risk.

This stage does not choose the final supplier. It prepares canonical country packets under one `workflow_id`.

### Kickoff Endpoint

- Method: `POST`
- Path: `/api/v1/resolution/prep/start`
- Name: `start_resolution_prep`

### Kickoff Request

```json
{
  "event_id": "evt_001",
  "resource_type": "energy",
  "commodity": "crude_oil",
  "max_substitutes": 3
}
```

Required fields:
- `event_id` (must exist in disruption DB)

Optional fields:
- `resource_type` (if omitted, backend selects from persisted substitute snapshots)
- `commodity` (if omitted, backend selects from persisted substitute snapshots)
- `max_substitutes` (default `3`, bounds `1..10`)

Country selection contract:
1. Origin country is fixed as `Singapore`.
2. Disrupted supplier country comes from the disruption event (`from_country`).
3. Substitute candidates are loaded from database snapshots produced during Disruption Monitor runs.

Prerequisite:
- `POST /api/v1/disruptions/monitor/run` must have completed and persisted substitute snapshots for the target `event_id`.

### Kickoff Idempotency/Re-use Rule

- Normalize input (for example, country list ordering and casing).
- If the same normalized input already has a workflow, return the existing `workflow_id` instead of creating a new workflow.

### Kickoff Success Response

```json
{
  "status": "ok",
  "data": {
    "workflow_id": "wf_123",
    "stage": "origin_packet_ready",
    "origin_country": "Singapore",
    "event_id": "evt_001",
    "resource_type": "energy",
    "commodity": "crude_oil",
    "origin_packet": {
      "country": "Singapore",
      "country_role": "origin",
      "resource_type": "energy",
      "commodity": "crude_oil",
      "main_ideas": [],
      "important_points": [],
      "sources": []
    },
    "reused_workflow": false
  },
  "message": null
}
```

### Retrieval Endpoint

- Method: `GET`
- Path: `/api/v1/resolution/prep/{workflow_id}`

### Retrieval Success Response

```json
{
  "status": "ok",
  "data": {
    "workflow_id": "wf_123",
    "stage": "substitute_packets_in_progress",
    "event_id": "evt_001",
    "resource_type": "energy",
    "commodity": "crude_oil",
    "country_statuses": {
      "Singapore": "completed",
      "Indonesia": "completed",
      "Malaysia": "in_progress",
      "Australia": "queued",
      "Qatar": "failed"
    },
    "packets": {
      "Singapore": {
        "country": "Singapore",
        "country_role": "origin",
        "resource_type": "energy",
        "commodity": "crude_oil",
        "main_ideas": [],
        "important_points": [],
        "sources": []
      }
    }
  },
  "message": null
}
```

### Canonical Country Packet Schema

```json
{
  "country": "Indonesia",
  "country_role": "substitute_candidate",
  "resource_type": "energy",
  "commodity": "natural_gas",
  "main_ideas": [
    "High-level point 1",
    "High-level point 2"
  ],
  "important_points": [
    {
      "dimension": "supply_capacity",
      "point": "Structured supporting point",
      "support": ["source_1", "source_2"]
    }
  ],
  "sources": [
    {
      "id": "source_1",
      "title": "Example source",
      "url": "https://example.com",
      "credibility": "high",
      "date": "2026-03-28"
    }
  ]
}
```

Allowed `country_role` values:
- `origin`
- `disrupted_supplier`
- `substitute_candidate`

Controlled dimensions:
- `supply_capacity`
- `trade_relevance`
- `cost`
- `logistics`
- `risk`
- `sustainability`

### Workflow Stages

- `queued`
- `curation_started`
- `origin_packet_in_progress`
- `origin_packet_ready`
- `substitute_packets_in_progress`
- `all_packets_ready`
- `awaiting_user_configuration`
- `failed`
- `partially_failed`

Per-country statuses:
- `queued`
- `in_progress`
- `completed`
- `failed`

### Failure Rules

- If origin packet fails, kickoff endpoint returns error and workflow may be `failed`.
- If origin succeeds and some substitutes fail, kickoff remains successful and workflow may become `partially_failed`.

### Manager-Orchestrator Context Contract (Internal)

Manager must provide scoped context to each country worker so retrieval targets correct data:

```json
{
  "country": "Malaysia",
  "country_role": "substitute_candidate",
  "commodity": "natural gas",
  "resource_type": "energy",
  "disruption_context": {
    "event_id": "evt_001",
    "from_country": "Indonesia",
    "severity": "DISRUPTED",
    "headline": "Indonesia-linked natural gas disruption pressure"
  },
  "country_objective": "increase export profit without elevating domestic supply risk",
  "dimensions": [
    "supply_capacity",
    "trade_relevance",
    "cost",
    "logistics",
    "risk",
    "sustainability"
  ],
  "must_find": [
    "current export capacity and constraints",
    "trade relevance to Singapore or region",
    "logistics feasibility and route constraints"
  ],
  "stop_condition": "all dimensions have sufficient source-backed points"
}
```

Orchestrator behavior:
- Use TinyFish as primary retrieval tool.
- Execute one country worker process per country context.
- Each worker performs bounded retrieval based on manager checklist.
- Return curated packet + evidence coverage back to manager.
- If manager marks insufficient, run another bounded retrieval pass with missing-information checklist.
- Do not re-run substitute discovery; use stored substitute snapshots as source-of-truth.

## Debate Session Stage (Batch by Substitute Country)

### Purpose

Run one goal-driven debate graph per discovered substitute country and return consolidated decision payloads keyed by country.

### Start Endpoint

- Method: `POST`
- Path: `/api/v1/debate/start`

### Request

```json
{
  "workflow_id": "wf_20260328_123000_ab12cd",
  "topic": "Which sourcing strategy best achieves the goal?",
  "goal": "Minimize supply disruption risk while keeping short-term costs acceptable",
  "input_country": "Singapore",
  "singapore_info": {
    "main_ideas": ["..."],
    "important_points": [],
    "sources": []
  },
  "max_rounds": 3,
  "max_substitutes": 4,
  "max_parallel_graphs": 2
}
```

Notes:
- Substitute countries are auto-discovered from persisted substitute snapshots + completed substitute packets.
- `max_parallel_graphs` bounds concurrent debate graphs (default `2`).
- `singapore_info` must include at least one of: `main_ideas`, `important_points`, or `sources`.
- Each substitute country is executed through a LangGraph `StateGraph` parent graph with team subgraphs and a judge node.
- Ingestion summarization, team-turn drafting, and judge synthesis use OpenAI LLM when `OPENAI_API_KEY` is present, with deterministic fallback when unavailable.

### Success Response

```json
{
  "status": "ok",
  "data": {
    "workflow_id": "wf_20260328_123000_ab12cd",
    "input_country": "Singapore",
    "substitutes": ["Qatar", "Malaysia"],
    "results": {
      "Qatar": {
        "session_id": "debate_...",
        "status": "completed",
        "winner_team_id": "team_a",
        "final_recommendation": {
          "recommended_strategy": "...",
          "why": "...",
          "confidence": 0.81
        },
        "recommended_action": "...",
        "viability_score": 0.81,
        "consensus_rationale": "...",
        "pros": [],
        "cons": [],
        "score_summary": {},
        "judge_summary": "...",
        "key_supporting_evidence": [],
        "main_tradeoffs": [],
        "main_risks": [],
        "open_questions": [],
        "team_positions": {},
        "round_summaries": [],
        "claim_ledger": []
      }
    },
    "errors": {}
  },
  "message": null
}
```

### Read Endpoints

- `GET /api/v1/debate/{session_id}`
- `GET /api/v1/debate/{session_id}/rounds`
- `GET /api/v1/debate/{session_id}/claims`

### Error Response Shape

```json
{
  "status": "error",
  "error_code": "WORKFLOW_NOT_FOUND",
  "message": "Resolution workflow not found: wf_missing",
  "session_id": null
}
```

Current error codes:
- `WORKFLOW_NOT_FOUND`
- `INVALID_DEBATE_REQUEST`
- `DEBATE_SESSION_FAILED`
- `DEBATE_SESSION_NOT_FOUND`
