# Extensions

## Manual Disruption Monitor Trigger (Demo Support)

Add a manual endpoint so demos do not need to wait for the daily scheduler.

- Method: `POST`
- Path: `/api/v1/disruptions/monitor/run`
- Purpose: trigger one Disruption Monitor run on demand.

### Expected Behavior

1. Attempt to start a monitor run immediately.
2. Reuse the same overlap lock rule as scheduled runs.
3. If a run is already active, return a `skipped_overlap` style response.
4. Persist and emit events using the same rules as scheduled runs.

### Suggested Response Shape

```json
{
  "run_id": "run_20260327_120000",
  "status": "completed",
  "trigger": "manual",
  "emitted_events": [
    {
      "event_id": "evt_001",
      "from_country": "Iran",
      "severity": "CRITICAL",
      "resource_types": {
        "energy": ["crude_oil"]
      },
      "headline": "Iran-linked disruption threatens Singapore energy imports",
      "source_urls": [
        "https://example.com/disruption-article"
      ]
    }
  ]
}
```

Allowed `status` values:
- `completed`
- `failed`
- `skipped_overlap`

## Disruption Events Read API

Expose persisted disruption events (including `source_urls`) for frontend pages.

- Method: `GET`
- Path: `/api/v1/disruptions/events`
- Query: `limit` (optional, default `100`, min `1`, max `200`)
- Returns: list of persisted events ordered by most recent update.

- Method: `GET`
- Path: `/api/v1/disruptions/events/{event_id}`
- Returns: one persisted event by id.

## Substitute Finder Utility

Backend utility for downstream scenario/planning flows to propose replacement exporters.

- Module: `backend/utils/substitute_finder.py`
- Entry function: `find_substitutes_for_event(event_id: str, max_candidates: int = 5)`
- API access: `GET /api/v1/disruptions/events/{event_id}/substitutes?max_candidates=5`
- Input source: reads disruption event by `event_id` from local DB.
- For each affected commodity:
  - attempt TinyFish scrape for major exporters,
  - rank and dedupe candidates,
  - exclude the disrupted `from_country`.
- Fallback behavior: if live scrape fails, reuse cached Singapore supply-chain connections to suggest substitutes.
- Per-commodity source flag:
  - `live`
  - `fallback_connections`
  - `no_data`
