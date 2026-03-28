"""Debate session API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.debate_session import DebateBatchStartRequest
from backend.services.debate.session_orchestrator import (
    get_debate_claims,
    get_debate_rounds,
    get_debate_session,
    run_debate_batch_from_workflow,
)

router = APIRouter(prefix="/debate", tags=["debate"])


def _error_detail(
    *,
    error_code: str,
    message: str,
    session_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "session_id": session_id,
    }


@router.post("/start")
async def start_debate_batch(body: DebateBatchStartRequest) -> dict:
    """Run debate graphs for discovered substitute countries."""
    try:
        result = await run_debate_batch_from_workflow(body)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Resolution workflow not found:"):
            raise HTTPException(
                status_code=404,
                detail=_error_detail(
                    error_code="WORKFLOW_NOT_FOUND",
                    message=message,
                    session_id=None,
                ),
            ) from exc
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                error_code="INVALID_DEBATE_REQUEST",
                message=message,
                session_id=None,
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_error_detail(
                error_code="DEBATE_SESSION_FAILED",
                message=str(exc),
                session_id=None,
            ),
        ) from exc

    return {"status": "ok", "data": result.model_dump(), "message": None}


@router.get("/{session_id}")
def get_debate_session_result(session_id: str) -> dict:
    """Fetch one debate session result."""
    try:
        row = get_debate_session(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_detail(
                error_code="DEBATE_SESSION_NOT_FOUND",
                message=str(exc),
                session_id=session_id,
            ),
        ) from exc
    return {"status": "ok", "data": row.model_dump(), "message": None}


@router.get("/{session_id}/rounds")
def get_debate_session_rounds(session_id: str) -> dict:
    """Fetch judge round outputs for one debate session."""
    try:
        _ = get_debate_session(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_detail(
                error_code="DEBATE_SESSION_NOT_FOUND",
                message=str(exc),
                session_id=session_id,
            ),
        ) from exc
    rounds = get_debate_rounds(session_id)
    return {"status": "ok", "data": rounds, "message": None}


@router.get("/{session_id}/claims")
def get_debate_session_claims(session_id: str) -> dict:
    """Fetch claim ledger entries for one debate session."""
    try:
        _ = get_debate_session(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_detail(
                error_code="DEBATE_SESSION_NOT_FOUND",
                message=str(exc),
                session_id=session_id,
            ),
        ) from exc
    claims = get_debate_claims(session_id)
    return {"status": "ok", "data": claims, "message": None}
