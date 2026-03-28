"""Manager logic for resolution-prep country context and quality checks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backend.db.models import DisruptionEventRecord
from backend.models.country_packet import (
    CountryPacket,
    CountryPacketDimension,
    CountryRole,
)

_CONTROLLED_DIMENSIONS: tuple[CountryPacketDimension, ...] = (
    "supply_capacity",
    "trade_relevance",
    "cost",
    "logistics",
    "risk",
    "sustainability",
)


@dataclass(slots=True)
class CountryCurationContext:
    country: str
    country_role: CountryRole
    country_objective: str
    resource_type: str
    commodity: str
    disruption_context: dict[str, str]
    dimensions: list[CountryPacketDimension]
    must_find: list[str]
    stop_condition: str


def controlled_dimensions() -> tuple[CountryPacketDimension, ...]:
    """Return canonical dimensions for every country packet."""
    return _CONTROLLED_DIMENSIONS


def _objective_for_role(role: CountryRole) -> str:
    if role == "origin":
        return "maximize supply resilience for Singapore"
    if role == "disrupted_supplier":
        return "protect domestic stability while managing export commitments"
    return "increase export profit without elevating domestic citizen risk"


def _must_find_for_role(role: CountryRole) -> list[str]:
    base = [
        "current export or import capacity and near-term constraints",
        "trade relevance to Singapore and regional market dependence",
        "logistics feasibility and route constraints for this commodity",
    ]
    if role == "origin":
        return base + [
            "resilience levers (stockpile, diversification, policy options)",
            "critical import bottlenecks and acceptable risk thresholds",
        ]
    if role == "disrupted_supplier":
        return base + [
            "domestic supply pressures and social risk factors",
            "policy or operational limits on increasing exports",
        ]
    return base + [
        "domestic affordability and supply-security implications",
        "marginal upside versus domestic risk trade-off",
    ]


def build_country_contexts(
    *,
    event: DisruptionEventRecord,
    event_id: str,
    resource_type: str,
    commodity: str,
    substitute_countries: Sequence[str],
) -> list[CountryCurationContext]:
    """Build manager-scoped retrieval contexts for each country worker."""
    disruption_context = {
        "event_id": event_id,
        "from_country": event.from_country,
        "severity": event.severity,
        "headline": event.headline,
    }

    contexts: list[CountryCurationContext] = [
        CountryCurationContext(
            country="Singapore",
            country_role="origin",
            country_objective=_objective_for_role("origin"),
            resource_type=resource_type,
            commodity=commodity,
            disruption_context=disruption_context,
            dimensions=list(_CONTROLLED_DIMENSIONS),
            must_find=_must_find_for_role("origin"),
            stop_condition="all dimensions have sufficient source-backed points",
        ),
        CountryCurationContext(
            country=event.from_country,
            country_role="disrupted_supplier",
            country_objective=_objective_for_role("disrupted_supplier"),
            resource_type=resource_type,
            commodity=commodity,
            disruption_context=disruption_context,
            dimensions=list(_CONTROLLED_DIMENSIONS),
            must_find=_must_find_for_role("disrupted_supplier"),
            stop_condition="all dimensions have sufficient source-backed points",
        ),
    ]

    seen = {ctx.country.casefold() for ctx in contexts}
    for country in substitute_countries:
        clean = country.strip()
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        contexts.append(
            CountryCurationContext(
                country=clean,
                country_role="substitute_candidate",
                country_objective=_objective_for_role("substitute_candidate"),
                resource_type=resource_type,
                commodity=commodity,
                disruption_context=disruption_context,
                dimensions=list(_CONTROLLED_DIMENSIONS),
                must_find=_must_find_for_role("substitute_candidate"),
                stop_condition="all dimensions have sufficient source-backed points",
            )
        )
        seen.add(key)
    return contexts


def evaluate_packet_sufficiency(packet: CountryPacket) -> tuple[bool, list[str]]:
    """Return sufficiency and missing dimensions for iterative retrieval."""
    covered: set[str] = set()
    for point in packet.important_points:
        if point.support:
            covered.add(point.dimension)
    missing = [
        dimension for dimension in _CONTROLLED_DIMENSIONS if dimension not in covered
    ]
    return (len(missing) == 0, missing)
