"""Disruption monitor API routes."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from backend.services.disruption_monitor_service import (
    get_persisted_event,
    list_persisted_events,
    run_monitor_once,
)
from backend.utils.substitute_finder import find_substitutes_for_event

router = APIRouter(prefix="/disruptions", tags=["disruptions"])


@router.post("/monitor/run")
async def run_disruption_monitor() -> dict:
    """Trigger one manual disruption monitor run."""
    data = await run_monitor_once(trigger="manual")
    return {"status": "ok", "data": data.model_dump(), "message": None}


@router.get("/events")
async def list_disruption_events(
    limit: int = Query(100, ge=1, le=200),
) -> dict:
    """Return persisted disruption events for frontend consumption."""
    data = list_persisted_events(limit=limit)
    return {
        "status": "ok",
        "data": [row.model_dump() for row in data],
        "message": None,
    }


@router.get("/events/{event_id}")
async def get_disruption_event(event_id: str) -> dict:
    """Return one disruption event including source URLs."""
    try:
        data = get_persisted_event(event_id)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Disruption event not found:"):
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    return {"status": "ok", "data": data.model_dump(), "message": None}


@router.get("/events/{event_id}/substitutes")
async def get_substitutes_for_event(
    event_id: str,
    max_candidates: int = Query(5, ge=1, le=20),
) -> dict:
    """Return substitute supplier candidates for one disruption event."""
    try:
        data = await find_substitutes_for_event(
            event_id=event_id,
            max_candidates=max_candidates,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Disruption event not found:"):
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return {"status": "ok", "data": asdict(data), "message": None}
