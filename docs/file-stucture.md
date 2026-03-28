# File Structure

This is the target implementation layout for the current backend plans.

```text
tinyfish-hackathon/
├── AGENTS.md
├── README.md
├── LICENSE
├── docs/
│   ├── architecture.md
│   ├── api-contracts.md
│   ├── idea-backend.md
│   └── file-stucture.md
├── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── resolution_prep/
│   │   └── debate/
│   │       ├── state.py
│   │       ├── team_subgraph.py
│   │       ├── judge_nodes.py
│   │       └── graph.py
│   ├── api/
│   │   ├── supply_chain.py
│   │   ├── news_curator.py
│   │   ├── disruptions.py
│   │   ├── resolution_prep.py
│   │   └── debate.py
│   ├── services/
│   │   ├── tinyfish_client.py
│   │   ├── llm_curation.py
│   │   ├── supply_chain_service.py
│   │   ├── news_curator_service.py
│   │   ├── disruption_monitor_service.py
│   │   ├── resolution_prep_manager.py
│   │   ├── resolution_prep_orchestrator.py
│   │   ├── country_curation_service.py
│   │   └── debate/
│   │       ├── session_orchestrator.py
│   │       ├── source_processor.py
│   │       ├── chunking.py
│   │       ├── retrieval.py
│   │       ├── team_engine.py
│   │       └── judge_engine.py
│   ├── repositories/
│   │   └── debate_session_repository.py
│   ├── scheduler/
│   │   ├── disruption_runner.py
│   │   └── resolution_background_runner.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── migrations/
│   ├── cache/
│   │   └── memory_cache.py
│   └── models/
│       ├── supply_chain.py
│       ├── news_curator.py
│       ├── disruption_event.py
│       ├── resolution_workflow.py
│       ├── country_packet.py
│       └── debate_session.py
└── frontend/
    └── src/
        └── app/
```

## Notes

- Backend owns all logic, including agentic retrieval orchestration.
- `backend/db/` is local persistence and should support JSON field storage.
- Disruption data is the core persisted domain; future features build from this event history.
- Resolution preparation reuses the same persistence layer (`workflow_id`, packet history, per-country statuses).
- API behavior is defined in `docs/api-contracts.md`.
