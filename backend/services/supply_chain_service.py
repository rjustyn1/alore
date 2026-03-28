"""Supply-chain orchestration for Singapore connections."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections.abc import Mapping, Sequence

from backend.cache.file_cache import JsonFileCache
from backend.cache.memory_cache import MemoryCache
from backend.models.supply_chain import (
    CountryResourceBuckets,
    ResourceCategory,
    SupplyChainConnectionsResponse,
    SupplyChainDataSource,
    SupplyChainScrapeData,
)
from backend.services.tinyfish_client import TinyFishClient

logger = logging.getLogger(__name__)

_TRADE_SOURCE_URL = "https://oec.world/en/profile/country/sgp"
_RESOURCE_GOALS: dict[ResourceCategory, str] = {
    ResourceCategory.ENERGY: (
        "Find where Singapore imports energy from. "
        "Focus on source countries and energy commodities."
    ),
    ResourceCategory.FOOD: (
        "Find where Singapore imports food from. "
        "Focus on source countries and food commodities."
    ),
}

_FALLBACK_BY_RESOURCE: dict[ResourceCategory, dict[str, list[str]]] = {
    ResourceCategory.ENERGY: {
        "Indonesia": ["crude_oil", "natural_gas"],
        "Malaysia": ["natural_gas", "petroleum_products"],
        "Saudi Arabia": ["crude_oil"],
        "Qatar": ["liquefied_natural_gas"],
        "United Arab Emirates": ["crude_oil"],
        "Australia": ["coal", "liquefied_natural_gas"],
    },
    ResourceCategory.FOOD: {
        "Malaysia": ["palm_oil", "poultry", "vegetables"],
        "Indonesia": ["rice", "palm_oil", "spices"],
        "Thailand": ["rice", "sugar", "fruits"],
        "Australia": ["wheat", "dairy", "beef"],
        "Brazil": ["soybeans", "coffee", "poultry"],
        "India": ["rice", "spices", "seafood"],
    },
}

_CONNECTIONS_CACHE: MemoryCache[SupplyChainConnectionsResponse] = MemoryCache()
_CONNECTIONS_PERSISTED_CACHE: JsonFileCache[SupplyChainConnectionsResponse] = (
    JsonFileCache(
        path=os.getenv(
            "SUPPLY_CHAIN_CACHE_FILE", "backend/cache/runtime/supply_chain.json"
        ),
        serializer=lambda value: value.model_dump(mode="json"),
        deserializer=lambda payload: SupplyChainConnectionsResponse.model_validate(
            payload
        ),
    )
)


def _sanitize_commodity(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _parse_commodity_list(raw: object) -> list[str]:
    if isinstance(raw, str):
        source_values = [raw]
    elif isinstance(raw, Sequence) and not isinstance(raw, str | bytes | bytearray):
        source_values = [v for v in raw if isinstance(v, str)]
    else:
        return []

    parsed: list[str] = []
    for value in source_values:
        commodity = _sanitize_commodity(value)
        if commodity and commodity not in parsed:
            parsed.append(commodity)
    return parsed


def _parse_country_map(raw: Mapping[str, object]) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for country, commodities in raw.items():
        if not isinstance(country, str):
            continue
        country_name = country.strip()
        if not country_name:
            continue
        values = _parse_commodity_list(commodities)
        if values:
            parsed[country_name] = values
    return parsed


def _parse_connection_rows(raw: Sequence[object]) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for row in raw:
        if not isinstance(row, Mapping):
            continue

        country: str | None = None
        for key in ("country", "source_country", "partner", "name"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                country = value.strip()
                break

        if country is None:
            continue

        commodities: object = []
        for key in ("commodities", "imports", "products", "items", "commodity"):
            if key in row:
                commodities = row[key]
                break
        values = _parse_commodity_list(commodities)
        if not values:
            continue

        bucket = parsed.setdefault(country, [])
        for value in values:
            if value not in bucket:
                bucket.append(value)
    return parsed


def _extract_connections(raw_result: object) -> dict[str, list[str]]:
    if isinstance(raw_result, str):
        try:
            decoded = json.loads(raw_result)
        except json.JSONDecodeError:
            return {}
        return _extract_connections(decoded)

    if isinstance(raw_result, Mapping):
        wrapped = raw_result.get("connections")
        if isinstance(wrapped, Mapping):
            parsed = _parse_country_map(wrapped)
            if parsed:
                return parsed
        if isinstance(wrapped, Sequence) and not isinstance(
            wrapped, str | bytes | bytearray
        ):
            parsed = _parse_connection_rows(wrapped)
            if parsed:
                return parsed

        for key in ("imports", "sources", "countries", "data", "result"):
            value = raw_result.get(key)
            if isinstance(value, Mapping):
                parsed = _parse_country_map(value)
                if parsed:
                    return parsed
            if isinstance(value, Sequence) and not isinstance(
                value, str | bytes | bytearray
            ):
                parsed = _parse_connection_rows(value)
                if parsed:
                    return parsed
        return _parse_country_map(raw_result)

    if isinstance(raw_result, Sequence) and not isinstance(
        raw_result, str | bytes | bytearray
    ):
        return _parse_connection_rows(raw_result)

    return {}


def _build_goal(resource: ResourceCategory) -> str:
    base_goal = _RESOURCE_GOALS[resource]
    return (
        f"{base_goal} Return only valid JSON in this exact shape: "
        '{"connections":{"Country Name":["commodity_one","commodity_two"]}}. '
        "Use snake_case for commodity names and include at least 5 countries."
    )


def _copy_connections(
    connections: Mapping[str, CountryResourceBuckets],
) -> dict[str, CountryResourceBuckets]:
    copied: dict[str, CountryResourceBuckets] = {}
    for country, values in connections.items():
        copied[country] = CountryResourceBuckets(
            energy=list(values.energy),
            food=list(values.food),
        )
    return copied


def _build_fallback_connections() -> dict[str, CountryResourceBuckets]:
    merged: dict[str, CountryResourceBuckets] = {}
    for resource, connections in _FALLBACK_BY_RESOURCE.items():
        for country, commodities in connections.items():
            bucket = merged.setdefault(country, CountryResourceBuckets())
            target = (
                bucket.energy if resource == ResourceCategory.ENERGY else bucket.food
            )
            for commodity in commodities:
                normalized = _sanitize_commodity(commodity)
                if normalized and normalized not in target:
                    target.append(normalized)
    return merged


async def _fetch_resource_connections(
    client: TinyFishClient,
    resource: ResourceCategory,
) -> dict[str, list[str]]:
    payload = await client.run(url=_TRADE_SOURCE_URL, goal=_build_goal(resource))
    status = str(payload.get("status", "")).upper()
    if status != "COMPLETED":
        raise RuntimeError(f"TinyFish run did not complete successfully: {status}")
    connections = _extract_connections(payload.get("result"))
    if not connections:
        raise RuntimeError("TinyFish run returned no usable connection data")
    return connections


async def _fetch_live_combined() -> dict[str, CountryResourceBuckets]:
    client = TinyFishClient()
    energy_connections, food_connections = await asyncio.gather(
        _fetch_resource_connections(client, ResourceCategory.ENERGY),
        _fetch_resource_connections(client, ResourceCategory.FOOD),
    )
    merged: dict[str, CountryResourceBuckets] = {}
    for country, commodities in energy_connections.items():
        bucket = merged.setdefault(country, CountryResourceBuckets())
        for commodity in commodities:
            if commodity not in bucket.energy:
                bucket.energy.append(commodity)
    for country, commodities in food_connections.items():
        bucket = merged.setdefault(country, CountryResourceBuckets())
        for commodity in commodities:
            if commodity not in bucket.food:
                bucket.food.append(commodity)
    return merged


async def get_singapore_connections(
    refresh: bool = False,
) -> SupplyChainConnectionsResponse:
    """Return combined country -> {energy, food} payload with cache support."""
    cache_entry = _CONNECTIONS_CACHE.get()
    if cache_entry is None:
        persisted_entry = _CONNECTIONS_PERSISTED_CACHE.get()
        if persisted_entry is not None:
            cache_entry = _CONNECTIONS_CACHE.set(persisted_entry.value)

    if cache_entry and not refresh:
        return SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections=_copy_connections(cache_entry.value.connections),
        )

    try:
        live_connections = await _fetch_live_combined()
        live_response = SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections=live_connections,
        )
        _CONNECTIONS_CACHE.set(live_response)
        _CONNECTIONS_PERSISTED_CACHE.set(live_response)
        return SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections=_copy_connections(live_connections),
        )
    except Exception as exc:
        logger.warning("Live TinyFish scrape failed; using fallback path (%s)", exc)
        if cache_entry:
            return SupplyChainConnectionsResponse(
                source=SupplyChainDataSource.CACHE_STALE,
                connections=_copy_connections(cache_entry.value.connections),
            )
        return SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.FALLBACK_SEED,
            connections=_build_fallback_connections(),
        )


async def scrape_supply_chain_resource(resource: str) -> SupplyChainScrapeData:
    """Return compatibility response for one resource category."""
    combined = await get_singapore_connections(refresh=False)
    normalized_resource = resource.lower().strip()

    if normalized_resource == "energy":
        connections = {
            country: values.energy for country, values in combined.connections.items()
        }
    elif normalized_resource == "food":
        connections = {
            country: values.food for country, values in combined.connections.items()
        }
    else:
        connections = {}

    return SupplyChainScrapeData(
        resource=normalized_resource,
        source=combined.source,
        connections=connections,
    )
