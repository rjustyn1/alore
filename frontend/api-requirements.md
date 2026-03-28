# Alore — API Requirements

## Auth Context

- Single analyst user (no multi-user for now)
- All endpoints authenticated via Bearer token
- No role differentiation yet — treat every request as `role: analyst`

---

## Conventions

- REST, JSON
- Base path: `/api/v1`
- Dates: ISO 8601 (`2026-03-27T10:00:00Z`)
- Status codes: `200` success, `201` created, `400` bad input, `404` not found, `500` server error
- Error shape: `{ "error": "message string" }`
- Pagination: `?page=1&limit=20`, response includes `{ data: [...], total, page, limit }`
- Enum values are lowercase strings (e.g. `"disrupted"`, `"food"`, `"conditional"`)

---

## Feature Inventory & Data Needs

### 1. Home Dashboard (`/dashboard`)

Displays a world map with Singapore's supply connections. Shows overall network status at a glance.

**Needs:**

- All supply routes (country, sector, status, note)
- All news signals (headline, snippet, sector tag, url)
- Current scrape frequency setting for the user

**Actions:**

- `GET /routes` — fetch all supply routes
- `GET /news` — fetch latest news signals (most recent 20)
- `GET /settings` — fetch user settings (includes `scrape_frequency`)
- `PATCH /settings` — update `scrape_frequency` (`"1h"|"6h"|"12h"|"1d"|"3d"|"7d"`)

---

### 2. Scenario Simulator (`/scenario`)

User types a "what if" prompt, app sends it to Claude, returns a chain-reaction JSON, rendered as expandable steps.

**Needs:**

- No persistent data needed — results are ephemeral per session

**Actions:**

- `POST /scenarios/run` — send prompt to Claude, stream or return chain-reaction result
  - Request: `{ "prompt": string }`
  - Response: `{ scenario, summary, severity, chain: [...steps], mitigations: [...] }`
- `POST /scenarios` — optionally save a completed scenario
  - Request: full scenario result object
- `GET /scenarios` — list saved scenarios (paginated)
- `DELETE /scenarios/:id`

**Scenario object:**

```json
{
  "id": "uuid",
  "created_at": "iso date",
  "prompt": "What if China restricts food exports?",
  "scenario": "short title",
  "summary": "2-3 sentence summary",
  "severity": "stable|mild|urgent",
  "chain": [
    {
      "step": 1,
      "entity": "China",
      "sector": "food",
      "severity": "urgent",
      "impact": "short title",
      "detail": "detail text",
      "timeframe": "immediate|short-term|medium-term|long-term"
    }
  ],
  "mitigations": ["action 1", "action 2"]
}
```

---

### 3. Sentry (`/sentry`)

Monitors 8 signals across 5 sectors. Shows live status, last-checked time, recent detections. User can trigger a manual sweep.

**Needs:**

- All signals with current value, threshold, status, last-checked time
- Recent detections feed (last 20)

**Actions:**

- `GET /signals` — fetch all monitored signals
- `PATCH /signals/:id` — update a signal's threshold or enabled state
  - Request: `{ "threshold": string, "enabled": boolean }`
- `GET /detections` — fetch recent detection events (paginated)
- `POST /sweep` — trigger a manual sweep across all sources
  - Response: `{ "job_id": "uuid", "status": "running" }` (async)
- `GET /sweep/:job_id` — poll sweep status
  - Response: `{ "status": "running|complete", "detections": [...] }`

**Signal object:**

```json
{
  "id": "uuid",
  "name": "China Export Controls",
  "sector": "food",
  "value": "34% tariff",
  "threshold": "New restrictions",
  "change": "ESCALATED",
  "direction": "up|down|stable|mild",
  "status": "triggered|mild|watching",
  "checked_at": "iso date",
  "sources_count": 4
}
```

**Detection object:**

```json
{
  "id": "uuid",
  "created_at": "iso date",
  "signal_id": "uuid",
  "signal_name": "China Export Controls",
  "sector": "food",
  "severity": "urgent|mild|stable",
  "message": "detail text"
}
```

---

### 4. Debate History (`/history`)

Lists all completed AI minister debates. User can filter by verdict, expand a card to see full report.

**Needs:**

- All saved debates, newest first
- Filterable by `final_position`

**Actions:**

- `GET /debates` — list debates, supports `?final_position=conditional` filter (paginated)
- `GET /debates/:id` — single debate detail
- `POST /debates` — save a completed debate (called client-side after synthesis finishes)
- `DELETE /debates/:id`
- `DELETE /debates` — clear all (bulk delete)

**Debate object:**

```json
{
  "id": "uuid",
  "created_at": "iso date",
  "route": {
    "country": "China",
    "code": "CN",
    "sector": "food",
    "status": "disrupted",
    "note": "Tariff escalation — 34% duty active"
  },
  "goal": "cost|risk|resilience",
  "selected_news_count": 2,
  "synthesis": {
    "final_position": "proceed|conditional|monitor|hold|abort",
    "viability_score": 0.72,
    "pros": ["string", "string"],
    "cons": ["string", "string"],
    "rationale": "string",
    "recommended_action": "string",
    "urgency": "low|medium|high"
  }
}
```

---

## Shared / Reference Data

### Routes

Static for now, but should be manageable via API later.

- `GET /routes` — all supply connections
- `PATCH /routes/:code/:sector/status` — update status (`"stable"|"mild"|"disrupted"`)

**Route object:**

```json
{
  "country": "China",
  "code": "CN",
  "lat": 35.9,
  "lon": 104.2,
  "sector": "food",
  "note": "Tariff escalation — 34% duty active",
  "status": "disrupted"
}
```

### News

Currently hardcoded, should be scraped and served via API.

- `GET /news` — latest signals, sorted by recency, filterable by `?sector=food`

**News object:**

```json
{
  "id": "uuid",
  "created_at": "iso date",
  "sector": "food",
  "headline": "China raises tariffs 34%",
  "snippet": "detail text",
  "url": "https://..."
}
```

---

## Summary Table

| Method | Path                         | Purpose                            |
| ------ | ---------------------------- | ---------------------------------- |
| GET    | /routes                      | All supply connections             |
| PATCH  | /routes/:code/:sector/status | Update route status                |
| GET    | /news                        | Latest news signals                |
| GET    | /signals                     | All sentry signals                 |
| PATCH  | /signals/:id                 | Update signal threshold/enabled    |
| GET    | /detections                  | Recent detection events            |
| POST   | /sweep                       | Trigger manual source sweep        |
| GET    | /sweep/:job_id               | Poll sweep job status              |
| POST   | /scenarios/run               | Run "what if" via Claude           |
| GET    | /scenarios                   | Saved scenarios list               |
| POST   | /scenarios                   | Save a scenario                    |
| DELETE | /scenarios/:id               | Delete a scenario                  |
| GET    | /debates                     | Debate history (filterable)        |
| GET    | /debates/:id                 | Single debate                      |
| POST   | /debates                     | Save a debate                      |
| DELETE | /debates/:id                 | Delete a debate                    |
| DELETE | /debates                     | Clear all debates                  |
| GET    | /settings                    | User settings                      |
| PATCH  | /settings                    | Update settings (scrape_frequency) |
