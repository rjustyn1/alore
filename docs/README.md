# Tinyfish Hackathon Workspace

This repository is a documentation-first scaffold for a multi-service AI product built with:
- `frontend/`: Next.js app (App Router)
- `backend/`: FastAPI service
- `agents/`: LangGraph workflows
- `infra/`: Docker and deployment configuration
- `tests/`: unit, integration, and end-to-end coverage

The code structure above is the intended project layout for the hackathon build. The docs in this repo define how we design, implement, verify, and review work as the codebase grows.

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (or current active LTS)
- `uv` for Python dependency and task management
- `npm` for frontend dependencies

### 2. Install dependencies

```bash
uv sync
npm install --prefix frontend
```

### 3. Configure environment

```bash
cp .env.example .env
```

Only use variables defined by the project. Do not invent undocumented env vars.

### 4. Run services

Backend:

```bash
uv run uvicorn backend.main:app --reload
```

Frontend:

```bash
npm run dev --prefix frontend
```

## Project Docs

- `AGENTS.md`: contributor and agent execution rules
- `docs/architecture.md`: architecture boundaries and flow
- `docs/dev-setup.md`: local setup and troubleshooting
- `docs/testing.md`: testing strategy and command matrix
- `docs/api-contracts.md`: API behavior and contract norms
- `docs/code-review.md`: pull request and review quality bar

## Disruption Event Granularity

- Disruption monitor now persists one event per commodity.
- Canonical event fields are `resource_type` and `commodity` (not `resource_types`).
- Legacy multi-commodity rows are backfilled into single-commodity rows with new `event_id` values.

## Transferable Cache (Supply Chain and News)

- Supply-chain and news services now use both in-memory cache and JSON file cache.
- Default cache files:
  - `backend/cache/runtime/supply_chain.json`
  - `backend/cache/runtime/news_curator.json`
- Optional env overrides:
  - `SUPPLY_CHAIN_CACHE_FILE`
  - `NEWS_CACHE_FILE`

To transfer cache to another machine, copy those JSON files and keep the same paths (or set env overrides to their new locations).

## Recommended Development Flow

1. Read relevant docs before changing behavior.
2. Keep changes small and scoped.
3. Run nearest-relevant checks first, then broaden as needed.
4. Update documentation when behavior or contracts change.
5. Include root cause, trade-offs, and verification in PR notes.

## Verification Commands

Use these before calling work complete:

```bash
uv run ruff check backend
uv run ruff format --check backend
uv run pyright
npm run lint --prefix frontend
uv run pytest tests/unit
uv run pytest tests/integration
```

For small changes, run the nearest relevant checks first. For cross-cutting changes, run the full suite.

## Principles

- Favor targeted fixes over broad refactors.
- Keep business logic outside route handlers.
- Prefer server components in frontend code unless client state is required.
- Add type hints for all new Python functions.
- Avoid new dependencies unless they are clearly justified.
