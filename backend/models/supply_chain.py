"""Supply-chain domain models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ResourceCategory(str, Enum):
    ENERGY = "energy"
    FOOD = "food"


class SupplyChainDataSource(str, Enum):
    LIVE = "live"
    CACHE_STALE = "cache_stale"
    FALLBACK_SEED = "fallback_seed"


class CountryResourceBuckets(BaseModel):
    energy: list[str] = Field(default_factory=list)
    food: list[str] = Field(default_factory=list)


class SupplyChainConnectionsResponse(BaseModel):
    source: SupplyChainDataSource
    connections: dict[str, CountryResourceBuckets]


class SupplyChainScrapeRequest(BaseModel):
    resource: ResourceCategory


class SupplyChainScrapeData(BaseModel):
    resource: str
    source: SupplyChainDataSource
    connections: dict[str, list[str]]
