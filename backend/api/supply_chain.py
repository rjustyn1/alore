"""Supply-chain API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.models.supply_chain import SupplyChainScrapeRequest
from backend.services.supply_chain_service import (
    get_singapore_connections,
    scrape_supply_chain_resource,
)

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router.get("/singapore/connections")
async def singapore_connections(refresh: bool = Query(False)) -> dict:
    """Return Singapore supply-chain connections grouped by country."""
    data = await get_singapore_connections(refresh=refresh)
    return {"status": "ok", "data": data.model_dump(), "message": None}


@router.post("/scrape")
async def scrape_supply_chain(body: SupplyChainScrapeRequest) -> dict:
    """Compatibility endpoint for resource-scoped supply-chain scraping."""
    data = await scrape_supply_chain_resource(resource=body.resource.value)
    return {"status": "ok", "data": data.model_dump(), "message": None}
