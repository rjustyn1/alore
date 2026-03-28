"""Resolution-prep API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.resolution_workflow import ResolutionPrepStartRequest
from backend.services.resolution_prep_orchestrator import (
    get_resolution_prep_status,
    start_resolution_prep,
)

router = APIRouter(prefix="/resolution/prep", tags=["resolution-prep"])


@router.post("/start")
async def start_resolution_prep_workflow(body: ResolutionPrepStartRequest) -> dict:
    """Start or reuse resolution-prep workflow and return origin packet first."""
    try:
        data = await start_resolution_prep(body)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Disruption event not found:"):
            raise HTTPException(status_code=404, detail=message) from exc
        if message.startswith("Substitute snapshots not found:") or message.startswith(
            "No substitute snapshot matched requested filters"
        ):
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "data": data.model_dump(), "message": None}


@router.get("/{workflow_id}")
async def get_resolution_prep_workflow(workflow_id: str) -> dict:
    """Return persisted resolution-prep workflow status and available packets."""
    try:
        data = get_resolution_prep_status(workflow_id)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Resolution workflow not found:"):
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    return {"status": "ok", "data": data.model_dump(), "message": None}
