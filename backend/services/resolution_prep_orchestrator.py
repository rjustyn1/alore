"""Orchestration for resolution-preparation workflows."""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Literal, cast

from backend.db.models import CountryPacketRecord, ResolutionWorkflowRecord
from backend.db.repositories import DisruptionRepository, ResolutionPrepRepository
from backend.models.country_packet import CountryPacket
from backend.models.resolution_workflow import (
    CountryPacketStatus,
    ResolutionPrepKickoffData,
    ResolutionPrepStartRequest,
    ResolutionPrepStatusData,
    WorkflowStage,
)
from backend.services.country_curation_service import curate_country_packet
from backend.services.resolution_prep_manager import (
    CountryCurationContext,
    build_country_contexts,
    evaluate_packet_sufficiency,
)

_WORKFLOW_TASKS: dict[str, asyncio.Task[None]] = {}


def _new_workflow_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"wf_{timestamp}_{uuid.uuid4().hex[:6]}"


def _get_db_path() -> str:
    return os.getenv("DISRUPTION_DB_PATH", "backend.db")


def _get_disruption_repository() -> DisruptionRepository:
    return DisruptionRepository(db_path=_get_db_path())


def _get_resolution_repository() -> ResolutionPrepRepository:
    return ResolutionPrepRepository(db_path=_get_db_path())


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _normalized_workflow_key(
    request: ResolutionPrepStartRequest,
    *,
    resource_type: str,
    commodity: str,
) -> str:
    payload = {
        "event_id": request.event_id.strip(),
        "resource_type": resource_type,
        "commodity": commodity,
        "max_substitutes": request.max_substitutes,
    }
    return json.dumps(payload, sort_keys=True)


def _select_substitute_snapshot(
    *,
    repository: DisruptionRepository,
    event_id: str,
    resource_type_override: str | None,
    commodity_override: str | None,
    max_substitutes: int,
) -> tuple[str, str, list[str]]:
    snapshots = repository.list_substitute_snapshots(event_id)
    if not snapshots:
        raise ValueError(f"Substitute snapshots not found: {event_id}")

    resource_filter = (
        resource_type_override.strip().lower() if resource_type_override else ""
    )
    commodity_filter = (
        _normalize_token(commodity_override) if commodity_override else ""
    )
    filtered = snapshots
    if resource_filter:
        filtered = [row for row in filtered if row.resource_type == resource_filter]
    if commodity_filter:
        filtered = [
            row
            for row in filtered
            if _normalize_token(row.commodity) == commodity_filter
        ]
    if not filtered:
        raise ValueError(
            f"No substitute snapshot matched requested filters for event: {event_id}"
        )

    selected = sorted(
        filtered,
        key=lambda row: (row.updated_at, row.resource_type, row.commodity),
        reverse=True,
    )[0]
    countries: list[str] = []
    for row in selected.candidates:
        if not isinstance(row, dict):
            continue
        country = str(row.get("country", "")).strip()
        if country and country not in countries:
            countries.append(country)
    return selected.resource_type, selected.commodity, countries[:max_substitutes]


async def _curate_with_manager(context: CountryCurationContext) -> CountryPacket:
    packet = await curate_country_packet(context)
    is_sufficient, missing_dimensions = evaluate_packet_sufficiency(packet)
    if is_sufficient:
        return packet
    retry_packet = await curate_country_packet(
        context,
        missing_dimensions=missing_dimensions,
    )
    return retry_packet


def _packet_from_record(record: CountryPacketRecord) -> CountryPacket | None:
    if not record.packet_json:
        return None
    try:
        return CountryPacket.model_validate(record.packet_json)
    except Exception:
        return None


def _build_kickoff_from_existing(
    workflow: ResolutionWorkflowRecord,
    *,
    repository: ResolutionPrepRepository,
) -> ResolutionPrepKickoffData:
    origin_packet: CountryPacket | None = None
    for record in repository.list_packets(workflow.workflow_id):
        if record.country.casefold() != workflow.origin_country.casefold():
            continue
        origin_packet = _packet_from_record(record)
        break
    return ResolutionPrepKickoffData(
        workflow_id=workflow.workflow_id,
        stage=cast(WorkflowStage, workflow.stage),
        event_id=workflow.event_id,
        origin_country=workflow.origin_country,
        resource_type=cast(Literal["food", "energy"], workflow.resource_type),
        commodity=workflow.commodity,
        origin_packet=origin_packet,
        reused_workflow=True,
    )


async def _run_non_origin_workers(
    *,
    workflow_id: str,
    contexts: list[CountryCurationContext],
) -> None:
    repository = _get_resolution_repository()
    workflow = repository.get_workflow_by_id(workflow_id)
    if workflow is None:
        return
    country_statuses = dict(workflow.country_statuses)
    lock = asyncio.Lock()

    async def mark_status(country: str, status: CountryPacketStatus) -> None:
        async with lock:
            country_statuses[country] = status
            repository.update_workflow(
                workflow_id=workflow_id,
                stage="substitute_packets_in_progress",
                country_statuses=country_statuses,
            )

    async def run_worker(context: CountryCurationContext) -> None:
        await mark_status(context.country, "in_progress")
        try:
            packet = await _curate_with_manager(context)
            repository.upsert_packet(
                CountryPacketRecord(
                    workflow_id=workflow_id,
                    country=context.country,
                    status="completed",
                    packet_json=packet.model_dump(),
                )
            )
            await mark_status(context.country, "completed")
        except Exception:
            repository.upsert_packet(
                CountryPacketRecord(
                    workflow_id=workflow_id,
                    country=context.country,
                    status="failed",
                    packet_json={},
                )
            )
            await mark_status(context.country, "failed")

    await asyncio.gather(*(run_worker(context) for context in contexts))

    failed = [status for status in country_statuses.values() if status == "failed"]
    in_progress = [
        status for status in country_statuses.values() if status == "in_progress"
    ]
    queued = [status for status in country_statuses.values() if status == "queued"]
    if failed and len(failed) == len(country_statuses):
        stage: WorkflowStage = "failed"
    elif failed:
        stage = "partially_failed"
    elif in_progress or queued:
        stage = "substitute_packets_in_progress"
    else:
        stage = "all_packets_ready"

    repository.update_workflow(
        workflow_id=workflow_id,
        stage=stage,
        country_statuses=country_statuses,
    )


def _register_background_task(workflow_id: str, task: asyncio.Task[None]) -> None:
    _WORKFLOW_TASKS[workflow_id] = task

    def _cleanup(done_task: asyncio.Task[None]) -> None:
        _ = done_task
        _WORKFLOW_TASKS.pop(workflow_id, None)

    task.add_done_callback(_cleanup)


async def start_resolution_prep(
    request: ResolutionPrepStartRequest,
) -> ResolutionPrepKickoffData:
    """Start or reuse a resolution-prep workflow."""
    disruption_repository = _get_disruption_repository()
    resolution_repository = _get_resolution_repository()

    event = disruption_repository.get_event_by_id(request.event_id)
    if event is None:
        raise ValueError(f"Disruption event not found: {request.event_id}")

    resource_type, commodity, substitute_countries = _select_substitute_snapshot(
        repository=disruption_repository,
        event_id=request.event_id,
        resource_type_override=request.resource_type,
        commodity_override=request.commodity,
        max_substitutes=request.max_substitutes,
    )
    normalized_key = _normalized_workflow_key(
        request,
        resource_type=resource_type,
        commodity=commodity,
    )
    existing = resolution_repository.get_workflow_by_normalized_key(normalized_key)
    if existing is not None:
        return _build_kickoff_from_existing(existing, repository=resolution_repository)

    contexts = build_country_contexts(
        event=event,
        event_id=request.event_id,
        resource_type=resource_type,
        commodity=commodity,
        substitute_countries=substitute_countries,
    )
    origin_context = next(
        (row for row in contexts if row.country_role == "origin"), None
    )
    if origin_context is None:
        raise RuntimeError("Origin country context was not constructed")

    workflow_id = _new_workflow_id()
    country_statuses = {context.country: "queued" for context in contexts}
    resolution_repository.insert_workflow(
        ResolutionWorkflowRecord(
            workflow_id=workflow_id,
            normalized_key=normalized_key,
            event_id=request.event_id,
            origin_country="Singapore",
            disrupted_supplier_country=event.from_country,
            resource_type=resource_type,
            commodity=commodity,
            stage="curation_started",
            country_statuses=country_statuses,
        )
    )

    country_statuses[origin_context.country] = "in_progress"
    resolution_repository.update_workflow(
        workflow_id=workflow_id,
        stage="origin_packet_in_progress",
        country_statuses=country_statuses,
    )
    try:
        origin_packet = await _curate_with_manager(origin_context)
        resolution_repository.upsert_packet(
            CountryPacketRecord(
                workflow_id=workflow_id,
                country=origin_context.country,
                status="completed",
                packet_json=origin_packet.model_dump(),
            )
        )
    except Exception as exc:
        country_statuses[origin_context.country] = "failed"
        resolution_repository.update_workflow(
            workflow_id=workflow_id,
            stage="failed",
            country_statuses=country_statuses,
            error_message=str(exc),
        )
        raise RuntimeError("Failed to prepare origin packet") from exc

    country_statuses[origin_context.country] = "completed"
    resolution_repository.update_workflow(
        workflow_id=workflow_id,
        stage="origin_packet_ready",
        country_statuses=country_statuses,
    )

    non_origin_contexts = [row for row in contexts if row.country_role != "origin"]
    if non_origin_contexts:
        task = asyncio.create_task(
            _run_non_origin_workers(
                workflow_id=workflow_id, contexts=non_origin_contexts
            )
        )
        _register_background_task(workflow_id, task)
    else:
        resolution_repository.update_workflow(
            workflow_id=workflow_id,
            stage="all_packets_ready",
            country_statuses=country_statuses,
        )

    return ResolutionPrepKickoffData(
        workflow_id=workflow_id,
        stage="origin_packet_ready",
        event_id=request.event_id,
        origin_country="Singapore",
        resource_type=cast(Literal["food", "energy"], resource_type),
        commodity=commodity,
        origin_packet=origin_packet,
        reused_workflow=False,
    )


def get_resolution_prep_status(workflow_id: str) -> ResolutionPrepStatusData:
    """Return persisted workflow stage, country statuses, and country packets."""
    repository = _get_resolution_repository()
    workflow = repository.get_workflow_by_id(workflow_id)
    if workflow is None:
        raise ValueError(f"Resolution workflow not found: {workflow_id}")

    packets: dict[str, CountryPacket] = {}
    for record in repository.list_packets(workflow_id):
        packet = _packet_from_record(record)
        if packet is not None:
            packets[record.country] = packet

    return ResolutionPrepStatusData(
        workflow_id=workflow.workflow_id,
        stage=cast(WorkflowStage, workflow.stage),
        event_id=workflow.event_id,
        resource_type=cast(Literal["food", "energy"], workflow.resource_type),
        commodity=workflow.commodity,
        country_statuses={
            country: cast(CountryPacketStatus, status)
            for country, status in workflow.country_statuses.items()
        },
        packets=packets,
    )
