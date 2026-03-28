"""Utility for finding substitute exporter countries for a disruption event."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from backend.db.repositories import DisruptionRepository
from backend.models.supply_chain import CountryResourceBuckets
from backend.services.supply_chain_service import get_singapore_connections
from backend.services.tinyfish_client import TinyFishClient

_ALLOWED_RESOURCES = ("energy", "food")
_SEARCH_URL_TEMPLATE = "https://www.google.com/search?q={query}"
_EXPORT_SIGNAL_SCORE = {"high": 3, "medium": 2, "low": 1}
_COUNTRY_ALIAS_TO_CANONICAL = {
    "iran_islamic_republic_of": "iran",
    "islamic_republic_of_iran": "iran",
    "u_s_a": "united_states",
    "usa": "united_states",
    "u_s": "united_states",
    "us": "united_states",
    "uae": "united_arab_emirates",
}


@dataclass(slots=True)
class SubstituteCountry:
    """Candidate substitute supplier country."""

    country: str
    score: int
    reason: str
    matched_commodities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CommoditySubstituteResult:
    """Substitute candidates for one disrupted commodity."""

    resource: str
    commodity: str
    source: str
    countries: list[SubstituteCountry] = field(default_factory=list)


@dataclass(slots=True)
class SubstituteFinderResult:
    """Substitute recommendations for a disruption event."""

    event_id: str
    from_country: str
    headline: str
    substitutes: list[CommoditySubstituteResult] = field(default_factory=list)


@dataclass(slots=True)
class _ConnectionEntry:
    country: str
    resources: dict[str, set[str]]


def _canonical_country_key(country: str) -> str:
    normalized = _normalize_token(country)
    if not normalized:
        return ""
    return _COUNTRY_ALIAS_TO_CANONICAL.get(normalized, normalized)


def _is_same_country(left: str, right: str) -> bool:
    left_key = _canonical_country_key(left)
    right_key = _canonical_country_key(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    # Handles labels like "Iran, Islamic Republic of" vs "Iran".
    if left_key in right_key or right_key in left_key:
        return True
    return False


def _get_repository() -> DisruptionRepository:
    db_path = os.getenv("DISRUPTION_DB_PATH", "backend.db")
    return DisruptionRepository(db_path=db_path)


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _parse_commodities(raw: object) -> list[str]:
    if isinstance(raw, str):
        source = [raw]
    elif isinstance(raw, Sequence) and not isinstance(raw, str | bytes | bytearray):
        source = [value for value in raw if isinstance(value, str)]
    else:
        return []

    parsed: list[str] = []
    for value in source:
        normalized = _normalize_token(value)
        if normalized and normalized not in parsed:
            parsed.append(normalized)
    return parsed


def _build_connection_index(
    country_map: Mapping[str, CountryResourceBuckets],
) -> dict[str, _ConnectionEntry]:
    index: dict[str, _ConnectionEntry] = {}
    for country, buckets in country_map.items():
        key = _canonical_country_key(country)
        if not key:
            continue
        index[key] = _ConnectionEntry(
            country=country,
            resources={
                "energy": set(_parse_commodities(buckets.energy)),
                "food": set(_parse_commodities(buckets.food)),
            },
        )
    return index


def _build_goal(resource: str, commodity: str) -> str:
    label = commodity.replace("_", " ")
    return (
        f"Find major exporter countries for {label} under {resource} trade. "
        "Return JSON only in this shape: "
        '{"candidates":[{"country":"...","commodities":["..."],'
        '"export_signal":"high|medium|low","reason":"..."}]}. '
        "Prefer countries with sizeable export capacity."
    )


def _parse_signal(raw: object) -> str:
    if not isinstance(raw, str):
        return "low"
    lowered = raw.strip().lower()
    if "high" in lowered:
        return "high"
    if "medium" in lowered:
        return "medium"
    return "low"


def _extract_country_name(row: Mapping[str, object]) -> str:
    for key in ("country", "source_country", "exporter", "name"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_candidate_rows(raw_result: object) -> list[Mapping[str, object]]:
    if isinstance(raw_result, str):
        try:
            decoded = json.loads(raw_result)
        except json.JSONDecodeError:
            return []
        return _extract_candidate_rows(decoded)

    if isinstance(raw_result, Mapping):
        for key in ("candidates", "countries", "results", "items", "data"):
            extracted = _extract_candidate_rows(raw_result.get(key))
            if extracted:
                return extracted
        if _extract_country_name(raw_result):
            return [raw_result]
        return []

    if isinstance(raw_result, Sequence) and not isinstance(
        raw_result, str | bytes | bytearray
    ):
        extracted_rows: list[Mapping[str, object]] = []
        for row in raw_result:
            if not isinstance(row, Mapping):
                continue
            if _extract_country_name(row):
                extracted_rows.append(row)
        return extracted_rows
    return []


def _parse_live_candidates(
    rows: Sequence[Mapping[str, object]],
    *,
    commodity: str,
) -> list[SubstituteCountry]:
    parsed: list[SubstituteCountry] = []
    for row in rows:
        country = _extract_country_name(row)
        if not country:
            continue
        commodities = _parse_commodities(
            row.get("commodities", row.get("products", row.get("exports", [])))
        )
        signal = _parse_signal(row.get("export_signal", row.get("signal", "low")))
        reason = str(row.get("reason", row.get("evidence", ""))).strip()
        score = _EXPORT_SIGNAL_SCORE.get(signal, 1)
        if commodity in commodities:
            score += 1
        if not commodities:
            commodities = [commodity]
        parsed.append(
            SubstituteCountry(
                country=country,
                score=score,
                reason=reason or f"Large exporter signal for {commodity}.",
                matched_commodities=commodities,
            )
        )
    return parsed


async def _fetch_live_candidates(
    *,
    resource: str,
    commodity: str,
) -> list[SubstituteCountry]:
    query = quote_plus(f"top exporting countries for {commodity.replace('_', ' ')}")
    payload = await TinyFishClient().run(
        url=_SEARCH_URL_TEMPLATE.format(query=query),
        goal=_build_goal(resource=resource, commodity=commodity),
    )
    status = str(payload.get("status", "")).upper()
    if status != "COMPLETED":
        raise RuntimeError(f"TinyFish run did not complete successfully: {status}")
    rows = _extract_candidate_rows(payload.get("result"))
    candidates = _parse_live_candidates(rows, commodity=commodity)
    if not candidates:
        raise RuntimeError("TinyFish run returned no substitute candidates")
    return candidates


def _rank_candidates(
    *,
    live_candidates: Sequence[SubstituteCountry],
    disrupted_country: str,
    resource: str,
    commodity: str,
    connection_index: Mapping[str, _ConnectionEntry],
    max_candidates: int,
) -> list[SubstituteCountry]:
    by_country: dict[str, SubstituteCountry] = {}

    for candidate in live_candidates:
        country_key = _canonical_country_key(candidate.country)
        if not country_key:
            continue
        if _is_same_country(candidate.country, disrupted_country):
            continue

        score = candidate.score
        reason = candidate.reason
        connection_entry = connection_index.get(country_key)
        if connection_entry is not None:
            if commodity in connection_entry.resources.get(resource, set()):
                score += 2
                reason = f"{reason} Existing Singapore import link present."
            else:
                score += 1

        existing = by_country.get(country_key)
        if existing is None or score > existing.score:
            by_country[country_key] = SubstituteCountry(
                country=(
                    connection_entry.country if connection_entry else candidate.country
                ),
                score=score,
                reason=reason,
                matched_commodities=list(
                    dict.fromkeys(candidate.matched_commodities or [commodity])
                ),
            )
            continue

        for value in candidate.matched_commodities:
            if value not in existing.matched_commodities:
                existing.matched_commodities.append(value)

    ranked = sorted(by_country.values(), key=lambda item: (-item.score, item.country))
    return ranked[:max_candidates]


def _fallback_from_connections(
    *,
    disrupted_country: str,
    resource: str,
    commodity: str,
    connection_index: Mapping[str, _ConnectionEntry],
    max_candidates: int,
) -> list[SubstituteCountry]:
    disrupted_key = _canonical_country_key(disrupted_country)
    fallback: list[SubstituteCountry] = []
    for country_key, entry in connection_index.items():
        if not country_key:
            continue
        if country_key == disrupted_key or _is_same_country(
            entry.country, disrupted_country
        ):
            continue
        if commodity not in entry.resources.get(resource, set()):
            continue
        fallback.append(
            SubstituteCountry(
                country=entry.country,
                score=3,
                reason=(
                    "Existing Singapore import connection for this commodity; "
                    "usable as immediate substitute path."
                ),
                matched_commodities=[commodity],
            )
        )
    fallback.sort(key=lambda item: item.country)
    return fallback[:max_candidates]


async def find_substitutes_for_event(
    event_id: str,
    *,
    max_candidates: int = 5,
    repository: DisruptionRepository | None = None,
) -> SubstituteFinderResult:
    """Find substitute supplier countries for each disrupted commodity in an event."""
    if max_candidates <= 0:
        raise ValueError("max_candidates must be greater than zero")

    repo = repository or _get_repository()
    event = repo.get_event_by_id(event_id)
    if event is None:
        raise ValueError(f"Disruption event not found: {event_id}")

    resource_type = _normalize_token(event.resource_type)
    commodity = _normalize_token(event.commodity)
    impacted_pairs: list[tuple[str, str]] = []
    if resource_type in _ALLOWED_RESOURCES and commodity:
        impacted_pairs.append((resource_type, commodity))
    if not impacted_pairs:
        return SubstituteFinderResult(
            event_id=event.event_id,
            from_country=event.from_country,
            headline=event.headline,
            substitutes=[],
        )

    try:
        connections = await get_singapore_connections(refresh=False)
        connection_index = _build_connection_index(connections.connections)
    except Exception:
        connection_index = {}

    substitutes: list[CommoditySubstituteResult] = []
    for resource, commodity in impacted_pairs:
        source = "live"
        try:
            live_candidates = await _fetch_live_candidates(
                resource=resource,
                commodity=commodity,
            )
        except Exception:
            source = "fallback_connections"
            live_candidates = []

        ranked = _rank_candidates(
            live_candidates=live_candidates,
            disrupted_country=event.from_country,
            resource=resource,
            commodity=commodity,
            connection_index=connection_index,
            max_candidates=max_candidates,
        )
        if not ranked:
            source = "fallback_connections"
            ranked = _fallback_from_connections(
                disrupted_country=event.from_country,
                resource=resource,
                commodity=commodity,
                connection_index=connection_index,
                max_candidates=max_candidates,
            )
        if not ranked:
            source = "no_data"

        substitutes.append(
            CommoditySubstituteResult(
                resource=resource,
                commodity=commodity,
                source=source,
                countries=ranked,
            )
        )

    return SubstituteFinderResult(
        event_id=event.event_id,
        from_country=event.from_country,
        headline=event.headline,
        substitutes=substitutes,
    )
