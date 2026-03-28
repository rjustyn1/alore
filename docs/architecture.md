# Backend Architecture (V0)

## Scope

This architecture covers three backend capabilities:
- Supply Chain Connections Scraper
- Updated News Curator
- Disruption Monitor
- Resolution Preparation Stage (Pre-Debate Curation)
- Debate Session Stage (Goal-Driven Multi-Round Simulation)

The application is disruption-centric: persisted disruption events are the core data product that future features will build on.

## Core Components

- FastAPI API Layer
- Service/Orchestration Layer
- TinyFish Retrieval Adapter
- OpenAI Curation/Classification Adapter
- In-memory Cache (for scraper/curator responses)
- Local Database with JSON support (SQLite with JSON1 for disruption event history)
- Scheduler/Worker Runner (for Disruption Monitor)
- Resolution Prep Manager + Orchestrator + Country Workers
- Debate Session Orchestrator + Team Engines + Judge Engine

## Feature 1 Architecture: Supply Chain Connections Scraper

1. Frontend calls `GET /api/v1/supply-chain/singapore/connections`.
2. API checks cache.
3. On miss or forced refresh, service runs TinyFish retrieval for Singapore import-source data.
4. LLM curation normalizes country and commodity labels and assigns `food`/`energy`.
5. Service returns deterministic payload and updates cache.

Notes:
- Latest available year only.
- Response remains schema-stable for frontend.

## Feature 2 Architecture: Updated News Curator

1. Frontend calls `GET /api/v1/news-curator/singapore`.
2. Service retrieves candidates via TinyFish (14 days first, then 31 days fallback).
3. Deduplicate by lowercased title.
4. Classify into `internal` and `external` (internal wins if both).
5. Build hook from first 2 sentences (body then snippet fallback).
6. Rank by severity, directness, freshness (UTC).
7. Return up to 3 items per bucket.

Notes:
- External relevance uses supply-chain context when available.
- No tool-calling retrieval fallback in V0.

## Feature 3 Architecture: Disruption Monitor

1. Scheduler triggers daily run in SGT.
2. Runner obtains run lock; if lock held, mark run `skipped_overlap`.
3. Collector gathers reputable source documents using TinyFish.
4. Documents are normalized for classifier input.
5. Classifier returns non-emittable or emittable candidates.
6. Filter out candidates with unknown `from_country`.
7. Filter out candidates with missing `resource_type` or `commodity`.
8. Persist one event per commodity and deduplicate using (`from_country`, `resource_type`, `commodity`).
9. Create new event if no strong match; otherwise update existing event if meaningful changes exist.
10. Persist all new and updated events.
11. Emit only new and meaningfully updated events.
12. Finish run with status `completed` or `failed`.

Notes:
- Singapore is implicit destination; events track disruption origin (`from_country`).
- Severity assigned by LLM from allowed set: `WARNING`, `CONSTRAINED`, `DISRUPTED`, `CRITICAL`.

## Feature 4 Architecture: Resolution Preparation Stage

1. Client calls `POST /api/v1/resolution/prep/start` with `event_id`.
2. Service loads disruption event from local DB.
3. Service reads substitute-country snapshots already persisted by Disruption Monitor.
4. Manager builds per-country retrieval context (country role, objective, dimensions, must-find checklist).
5. Orchestrator starts one country worker process per country.
6. Each worker uses TinyFish retrieval + curation to create canonical country packet with source traceability.
7. Kickoff returns when Singapore packet is ready.
8. Remaining country workers continue in background.
9. Workflow stage, per-country statuses, and packets are persisted under one `workflow_id`.

Notes:
- Stage prepares evidence packets for debate; it does not select final resolution.
- Country objectives are explicit:
  - Singapore: supply resilience.
  - Other countries: export profit without unacceptable domestic risk.
- Resolution prep is DB-first and does not trigger substitute scraping.

## Feature 5 Architecture: Debate Session Stage

1. Client calls `POST /api/v1/debate/start` with `workflow_id`, `topic`, `goal`, and Singapore filtered info payload.
2. Service auto-discovers substitute countries from persisted substitute snapshots and completed substitute packets in the workflow.
3. Service creates one debate graph per substitute country.
4. Each graph builds a session-scoped corpus and two team RAG views (`team_a`, `team_b`).
5. Implementation uses LangGraph (`StateGraph`) for parent orchestration and routing.
6. Parent graph flow: `setup_session -> plan_debate -> round_loop -> final_verdict`.
7. Round loop executes: `team_a_turn -> team_b_turn -> judge_round -> continue_router`.
8. Team turn subgraph executes: `refresh_strategy -> retrieve_evidence -> draft_argument -> self_critique -> finalize_argument`.
9. Ingestion, team-turn drafting, and judge synthesis call LLM when `OPENAI_API_KEY` is available, with deterministic fallback.
10. Judge node evaluates each round, updates claim ledger and score state, and emits round summary.
11. Graph stops by judge decision or round limit.
12. Service returns consolidated results keyed by substitute country.

Notes:
- Graphs run in parallel with bounded concurrency for API safety.
- Debate retrieval remains session-scoped and deterministic (no global knowledge graph).
- Per-country failures fall back to conservative mock outputs without aborting the full batch.
- Debate agent implementation lives under `backend/agents/debate/`.

## Storage Strategy

- Scraper and curator use cache for fast API responses.
- Disruption Monitor uses local database persistence.
- Resolution Preparation also uses local database persistence (`workflow_id`, packet history, statuses).
- Preferred local DB for V0: SQLite with JSON1 support.
- Database must support JSON columns to store nested structures (for example substitute snapshots, supporting evidence, future extensible metadata).
- Event persistence is append/update history oriented, not overwrite-only.
