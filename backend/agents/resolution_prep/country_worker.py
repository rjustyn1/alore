"""Country-level curation worker for resolution preparation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Literal, cast
from urllib.parse import quote_plus

from backend.agents.resolution_prep.manager import CountryCurationContext
from backend.models.country_packet import (
    CountryNegotiationBrief,
    CountryPacket,
    CountryPacketDimension,
    CountryPacketPoint,
    CountryPacketSource,
)
from backend.services.tinyfish_client import TinyFishClient

_SEARCH_URL_TEMPLATE = "https://www.google.com/search?q={query}"


def _normalize_dimension(value: str) -> CountryPacketDimension | None:
    cleaned = re.sub(r"[^a-z]+", "_", value.strip().lower()).strip("_")
    mapping: dict[str, CountryPacketDimension] = {
        "supply_capacity": "supply_capacity",
        "trade_relevance": "trade_relevance",
        "cost": "cost",
        "logistics": "logistics",
        "risk": "risk",
        "sustainability": "sustainability",
    }
    return mapping.get(cleaned)


def _normalize_commodity(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _build_query(context: CountryCurationContext) -> str:
    query = (
        f"{context.country} {context.commodity.replace('_', ' ')} "
        f"exports capacity logistics domestic risk Singapore"
    )
    return _SEARCH_URL_TEMPLATE.format(query=quote_plus(query))


def _build_goal(
    context: CountryCurationContext,
    missing_requirements: Sequence[str] | None = None,
) -> str:
    missing_text = ""
    if missing_requirements:
        missing_text = (
            f" Prioritize missing requirements: {', '.join(missing_requirements)}."
        )
    must_find = "; ".join(context.must_find)
    return (
        "Curate a country packet for supply-chain resolution preparation. "
        "The packet must be sufficient for negotiating a workable deal. "
        "Return JSON only in this exact shape: "
        '{"country":"...","country_role":"...","resource_type":"energy|food",'
        '"commodity":"snake_case","main_ideas":["..."],'
        '"important_points":[{"dimension":"supply_capacity","point":"...",'
        '"support":["source_1"]}],'
        '"sources":[{"id":"source_1","title":"...","url":"https://...",'
        '"credibility":"high|medium|low|unknown","date":"YYYY-MM-DD"}],'
        '"negotiation_brief":{"priorities":["..."],'
        '"concession_options":["..."],"non_negotiables":["..."],'
        '"counterpart_asks":["..."],"deal_risks":["..."],'
        '"readiness_summary":"..."}}. '
        f"Country: {context.country}. Role: {context.country_role}. "
        f"Objective: {context.country_objective}. Must find: {must_find}."
        f" Stop condition: {context.stop_condition}.{missing_text}"
    )


def _extract_packet_payload(raw_result: object) -> Mapping[str, object] | None:
    if isinstance(raw_result, str):
        try:
            decoded = json.loads(raw_result)
        except json.JSONDecodeError:
            return None
        return _extract_packet_payload(decoded)
    if isinstance(raw_result, Mapping):
        for key in ("packet", "result", "data"):
            nested = raw_result.get(key)
            extracted = _extract_packet_payload(nested)
            if extracted:
                return extracted
        if "country" in raw_result or "important_points" in raw_result:
            return raw_result
    return None


def _parse_sources(raw: object) -> list[CountryPacketSource]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    parsed: list[CountryPacketSource] = []
    for idx, row in enumerate(raw, start=1):
        if not isinstance(row, Mapping):
            continue
        source_id = str(row.get("id", f"source_{idx}")).strip() or f"source_{idx}"
        title = str(row.get("title", "Untitled source")).strip() or "Untitled source"
        url = str(row.get("url", "")).strip()
        if not url:
            continue
        credibility = str(row.get("credibility", "unknown")).strip().lower()
        if credibility not in {"high", "medium", "low", "unknown"}:
            credibility = "unknown"
        normalized_credibility = cast(
            Literal["high", "medium", "low", "unknown"], credibility
        )
        source_date = str(row.get("date", "")).strip()
        parsed.append(
            CountryPacketSource(
                id=source_id,
                title=title,
                url=url,
                credibility=normalized_credibility,
                date=source_date,
            )
        )
    return parsed


def _parse_main_ideas(raw: object) -> list[str]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    ideas: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            continue
        idea = value.strip()
        if idea and idea not in ideas:
            ideas.append(idea)
    return ideas[:6]


def _parse_points(raw: object) -> list[CountryPacketPoint]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    points: list[CountryPacketPoint] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        dimension_raw = str(row.get("dimension", "")).strip()
        dimension = _normalize_dimension(dimension_raw)
        if dimension is None:
            continue
        point = str(row.get("point", "")).strip()
        if not point:
            continue
        support_values: list[str] = []
        support_raw = row.get("support", [])
        if isinstance(support_raw, Sequence) and not isinstance(
            support_raw, str | bytes | bytearray
        ):
            for value in support_raw:
                if isinstance(value, str) and value.strip():
                    support_values.append(value.strip())
        points.append(
            CountryPacketPoint(
                dimension=dimension,
                point=point,
                support=list(dict.fromkeys(support_values)),
            )
        )
    return points


def _parse_string_list(raw: object, *, max_items: int = 8) -> list[str]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = item.strip()
        if clean and clean not in values:
            values.append(clean)
    return values[:max_items]


def _fallback_negotiation_brief(
    context: CountryCurationContext,
) -> CountryNegotiationBrief:
    commodity_label = context.commodity.replace("_", " ")
    return CountryNegotiationBrief(
        priorities=[
            f"Secure {commodity_label} continuity for next quarter.",
            "Keep domestic stability within acceptable risk limits.",
        ],
        concession_options=[
            "Offer phased contract volume with optional extensions.",
        ],
        non_negotiables=[
            "No terms that trigger severe domestic shortage risk.",
        ],
        counterpart_asks=[
            "Request reliable shipment schedule commitments.",
        ],
        deal_risks=[
            "Fallback path used; validate assumptions with stronger sources.",
        ],
        readiness_summary=(
            "Fallback negotiation brief only; requires source-backed validation "
            "before final bargaining."
        ),
    )


def _parse_negotiation_brief(
    raw: object,
    *,
    context: CountryCurationContext,
) -> CountryNegotiationBrief:
    if not isinstance(raw, Mapping):
        return CountryNegotiationBrief()
    return CountryNegotiationBrief(
        priorities=_parse_string_list(raw.get("priorities", [])),
        concession_options=_parse_string_list(raw.get("concession_options", [])),
        non_negotiables=_parse_string_list(raw.get("non_negotiables", [])),
        counterpart_asks=_parse_string_list(raw.get("counterpart_asks", [])),
        deal_risks=_parse_string_list(raw.get("deal_risks", [])),
        readiness_summary=str(raw.get("readiness_summary", "")).strip(),
    )


def _fallback_packet(context: CountryCurationContext) -> CountryPacket:
    source_id = "fallback_1"
    fallback_source = CountryPacketSource(
        id=source_id,
        title="Fallback curation seed",
        url="https://example.com/resolution-prep-fallback",
        credibility="low",
        date=date.today().isoformat(),
    )
    points = [
        CountryPacketPoint(
            dimension=dimension,
            point=(
                f"{context.country}: preliminary {dimension.replace('_', ' ')} "
                f"assessment for {context.commodity}."
            ),
            support=[source_id],
        )
        for dimension in context.dimensions
    ]
    return CountryPacket(
        country=context.country,
        country_role=context.country_role,
        resource_type=cast(Literal["food", "energy"], context.resource_type),
        commodity=context.commodity,
        main_ideas=[
            f"{context.country} packet generated via fallback curation path.",
            f"Objective focus: {context.country_objective}.",
        ],
        important_points=points,
        sources=[fallback_source],
        negotiation_brief=_fallback_negotiation_brief(context),
        source_mode="fallback_seed",
    )


def _packet_from_payload(
    payload: Mapping[str, object],
    *,
    context: CountryCurationContext,
) -> CountryPacket:
    sources = _parse_sources(payload.get("sources", []))
    points = _parse_points(payload.get("important_points", []))
    main_ideas = _parse_main_ideas(payload.get("main_ideas", []))

    if not sources or not points:
        return _fallback_packet(context)

    negotiation_brief = _parse_negotiation_brief(
        payload.get("negotiation_brief", {}), context=context
    )
    if not negotiation_brief.readiness_summary:
        negotiation_brief.readiness_summary = (
            f"Prepared for {context.country} with objective: "
            f"{context.country_objective}."
        )

    return CountryPacket(
        country=context.country,
        country_role=context.country_role,
        resource_type=cast(
            Literal["food", "energy"], context.resource_type
        ),  # fixed by manager context
        commodity=_normalize_commodity(
            str(payload.get("commodity", context.commodity)) or context.commodity
        )
        or context.commodity,
        main_ideas=main_ideas
        or [
            f"{context.country} packet curated for {context.commodity}.",
            f"Objective focus: {context.country_objective}.",
        ],
        important_points=points,
        sources=sources,
        negotiation_brief=negotiation_brief,
        source_mode="live",
    )


async def curate_country_packet(
    context: CountryCurationContext,
    *,
    missing_requirements: Sequence[str] | None = None,
) -> CountryPacket:
    """Collect and curate one country packet using TinyFish, with fallback."""
    try:
        payload = await TinyFishClient().run(
            url=_build_query(context),
            goal=_build_goal(context, missing_requirements=missing_requirements),
        )
        status = str(payload.get("status", "")).upper()
        if status != "COMPLETED":
            raise RuntimeError(f"TinyFish run did not complete successfully: {status}")
        parsed_payload = _extract_packet_payload(payload.get("result"))
        if parsed_payload is None:
            raise RuntimeError("TinyFish run returned no usable country packet")
        return _packet_from_payload(parsed_payload, context=context)
    except Exception:
        return _fallback_packet(context)
