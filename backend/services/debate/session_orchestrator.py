"""Session orchestrator for batch debate runs across substitute countries."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone

from backend.agents.debate.graph import (
    run_debate_from_country_packets as run_debate_graph,
)
from backend.db.repositories import DisruptionRepository, ResolutionPrepRepository
from backend.models.country_packet import CountryPacket
from backend.models.debate_session import (
    DebateBatchResult,
    DebateBatchStartRequest,
    DebateFinalResult,
    DebateSessionArtifacts,
)
from backend.repositories.debate_session_repository import (
    get_debate_session_repository,
)
from backend.services.debate.judge_engine import (
    build_fallback_result,
)

logger = logging.getLogger(__name__)


def _utc_now_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _db_path() -> str:
    return os.getenv("DISRUPTION_DB_PATH", "backend.db")


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _extract_packet(record_packet: Mapping[str, object]) -> CountryPacket | None:
    try:
        return CountryPacket.model_validate(record_packet)
    except Exception:
        return None


def _select_substitute_countries(
    *,
    workflow_id: str,
    max_substitutes: int,
    input_country: str,
) -> tuple[str, dict[str, Mapping[str, object]]]:
    resolution_repo = ResolutionPrepRepository(db_path=_db_path())
    disruption_repo = DisruptionRepository(db_path=_db_path())

    workflow = resolution_repo.get_workflow_by_id(workflow_id)
    if workflow is None:
        raise ValueError(f"Resolution workflow not found: {workflow_id}")

    packet_rows = resolution_repo.list_packets(workflow_id)
    substitute_payloads: dict[str, Mapping[str, object]] = {}
    for row in packet_rows:
        if row.status != "completed":
            continue
        packet = _extract_packet(row.packet_json)
        if packet is None:
            continue
        if packet.country.casefold() == input_country.casefold():
            continue
        if packet.country_role != "substitute_candidate":
            continue
        substitute_payloads[packet.country] = row.packet_json

    snapshots = disruption_repo.list_substitute_snapshots(workflow.event_id)
    ranked_candidates: list[tuple[float, str]] = []
    preferred = [
        row
        for row in snapshots
        if row.resource_type == workflow.resource_type
        and _slug(row.commodity) == _slug(workflow.commodity)
    ]
    snapshot_row = preferred[0] if preferred else (snapshots[0] if snapshots else None)
    if snapshot_row is not None:
        for candidate in snapshot_row.candidates:
            if not isinstance(candidate, Mapping):
                continue
            country = str(candidate.get("country", "")).strip()
            if country:
                raw_score = candidate.get("score", 0.0)
                try:
                    if isinstance(raw_score, int | float | str):
                        score = float(raw_score)
                    else:
                        score = 0.0
                except Exception:
                    score = 0.0
                ranked_candidates.append((score, country))

    ranked_candidates.sort(key=lambda row: (-row[0], row[1].casefold()))
    snapshot_candidates: list[str] = []
    for _, country in ranked_candidates:
        if country not in snapshot_candidates:
            snapshot_candidates.append(country)

    selected: list[str] = []
    for country in snapshot_candidates:
        if country in substitute_payloads and country not in selected:
            selected.append(country)
        if len(selected) >= max_substitutes:
            break

    if len(selected) < max_substitutes:
        for country in sorted(substitute_payloads):
            if country in selected:
                continue
            selected.append(country)
            if len(selected) >= max_substitutes:
                break

    selected_payloads = {country: substitute_payloads[country] for country in selected}
    return workflow.resource_type, selected_payloads


async def _run_country_debate_graph(
    *,
    request: DebateBatchStartRequest,
    substitute_country: str,
    substitute_info: Mapping[str, object],
) -> DebateFinalResult:
    """Run one country-pair debate using the debate agent graph."""
    team_stances = {
        "team_a": "diversification-first sourcing for Singapore resilience",
        "team_b": (
            f"profit-preserving export offer from {substitute_country} with "
            "domestic-risk safeguards"
        ),
    }

    session_id = (
        f"debate_{_utc_now_token()}_{_slug(request.workflow_id)}_"
        f"{_slug(substitute_country)}_{uuid.uuid4().hex[:4]}"
    )
    logger.info("Debate session start: %s (%s)", session_id, substitute_country)

    graph_state = await run_debate_graph(
        session_id=session_id,
        topic=request.topic,
        goal=request.goal,
        input_country=request.input_country,
        substitute_country=substitute_country,
        input_country_info=_as_mapping(request.singapore_info),
        substitute_country_info=substitute_info,
        max_rounds=request.max_rounds,
        team_a_stance=team_stances["team_a"],
        team_b_stance=team_stances["team_b"],
    )
    result = graph_state.final_result
    if result is None:
        raise RuntimeError(f"Debate graph completed without final result: {session_id}")

    get_debate_session_repository().save(
        DebateSessionArtifacts(
            session_id=session_id,
            country=substitute_country,
            result=result,
            rounds=list(graph_state.judge_rounds),
            claims=list(graph_state.claim_ledger),
        )
    )
    logger.info("Debate session complete: %s (%s)", session_id, substitute_country)
    return result


async def run_debate_batch_from_workflow(
    request: DebateBatchStartRequest,
) -> DebateBatchResult:
    """Create one debate graph per substitute country and run in parallel."""
    logger.info("Debate batch start: workflow=%s", request.workflow_id)
    resource_type, substitute_map = _select_substitute_countries(
        workflow_id=request.workflow_id,
        max_substitutes=request.max_substitutes,
        input_country=request.input_country,
    )
    _ = resource_type

    if not substitute_map:
        fallback_result = build_fallback_result(
            session_id=f"debate_{_utc_now_token()}_{uuid.uuid4().hex[:6]}",
            topic=request.topic,
            goal=request.goal,
            fallback_country="no_substitute_available",
        )
        return DebateBatchResult(
            workflow_id=request.workflow_id,
            input_country=request.input_country,
            substitutes=[],
            results={"no_substitute_available": fallback_result},
            errors={
                "no_substitute_available": "No substitute packets found in workflow"
            },
        )

    semaphore = asyncio.Semaphore(request.max_parallel_graphs)
    results: dict[str, DebateFinalResult] = {}
    errors: dict[str, str] = {}

    async def run_one(
        substitute_country: str,
        substitute_info: Mapping[str, object],
    ) -> tuple[str, DebateFinalResult]:
        async with semaphore:
            try:
                result = await _run_country_debate_graph(
                    request=request,
                    substitute_country=substitute_country,
                    substitute_info=substitute_info,
                )
                return substitute_country, result
            except Exception as exc:
                logger.exception(
                    "Debate graph failed for substitute country %s", substitute_country
                )
                errors[substitute_country] = str(exc)
                fallback = build_fallback_result(
                    session_id=(
                        f"debate_{_utc_now_token()}_{_slug(substitute_country)}_"
                        f"{uuid.uuid4().hex[:4]}"
                    ),
                    topic=request.topic,
                    goal=request.goal,
                    fallback_country=substitute_country,
                )
                get_debate_session_repository().save(
                    DebateSessionArtifacts(
                        session_id=fallback.session_id,
                        country=substitute_country,
                        result=fallback,
                        rounds=[],
                        claims=[],
                    )
                )
                return substitute_country, fallback

    tasks = [run_one(country, payload) for country, payload in substitute_map.items()]
    settled = await asyncio.gather(*tasks)
    for country, result in settled:
        results[country] = result

    logger.info("Debate batch complete: workflow=%s", request.workflow_id)
    return DebateBatchResult(
        workflow_id=request.workflow_id,
        input_country=request.input_country,
        substitutes=list(substitute_map.keys()),
        results=results,
        errors=errors,
    )


async def run_debate_from_country_packets(
    *,
    topic: str,
    goal: str,
    input_country: str,
    substitute_country: str,
    input_country_info: Mapping[str, object],
    substitute_country_info: Mapping[str, object],
    max_rounds: int = 3,
) -> DebateFinalResult:
    """Run one direct country-pair debate from provided packet payloads."""
    team_stances = {
        "team_a": f"{input_country} resilience-first sourcing strategy",
        "team_b": (
            f"{substitute_country} profit-preserving export strategy with "
            "domestic safeguards"
        ),
    }
    session_id = (
        f"debate_{_utc_now_token()}_{_slug(input_country)}_"
        f"{_slug(substitute_country)}_{uuid.uuid4().hex[:4]}"
    )
    graph_state = await run_debate_graph(
        session_id=session_id,
        topic=topic,
        goal=goal,
        input_country=input_country,
        substitute_country=substitute_country,
        input_country_info=input_country_info,
        substitute_country_info=substitute_country_info,
        max_rounds=max_rounds,
        team_a_stance=team_stances["team_a"],
        team_b_stance=team_stances["team_b"],
    )
    result = graph_state.final_result
    if result is None:
        raise RuntimeError(f"Debate graph completed without final result: {session_id}")

    get_debate_session_repository().save(
        DebateSessionArtifacts(
            session_id=session_id,
            country=substitute_country,
            result=result,
            rounds=list(graph_state.judge_rounds),
            claims=list(graph_state.claim_ledger),
        )
    )
    return result


def get_debate_session(session_id: str) -> DebateFinalResult:
    row = get_debate_session_repository().get(session_id)
    if row is None:
        raise ValueError(f"Debate session not found: {session_id}")
    return row.result


def get_debate_rounds(session_id: str) -> list[dict[str, object]]:
    rounds = get_debate_session_repository().get_rounds(session_id)
    return [row.model_dump() for row in rounds]


def get_debate_claims(session_id: str) -> list[dict[str, object]]:
    claims = get_debate_session_repository().get_claims(session_id)
    return [row.model_dump() for row in claims]
