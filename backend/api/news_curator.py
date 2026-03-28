"""News curator API routes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.services.news_curator_service import get_singapore_news_curation

router = APIRouter(prefix="/news-curator", tags=["news-curator"])


@router.get("/singapore")
async def singapore_news() -> dict:
    """Return curated Singapore-relevant supply-chain news."""
    data = await get_singapore_news_curation()
    return {"status": "ok", "data": data.model_dump(), "message": None}
