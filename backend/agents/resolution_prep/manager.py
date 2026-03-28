"""Manager logic for resolution-prep country context and readiness checks."""

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


@dataclass(slots=True)
class PacketReadinessReport:
    is_sufficient: bool
    missing_dimensions: list[CountryPacketDimension]
    missing_requirements: list[str]


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
            (
                "minimum acceptable deal terms with suppliers "
                "(timing, volume, reliability)"
            ),
            "non-negotiable continuity constraints and risk thresholds",
        ]
    if role == "disrupted_supplier":
        return base + [
            "domestic supply pressures and social risk factors",
            "policy or operational limits on increasing exports",
            "profit opportunities that do not breach domestic safety thresholds",
        ]
    return base + [
        "domestic affordability and supply-security implications",
        "marginal export upside versus domestic risk trade-off",
        "terms this country would request from Singapore to commit supply",
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
            stop_condition=(
                "all dimensions covered with source-backed points and "
                "deal-negotiation signals are complete"
            ),
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
            stop_condition=(
                "all dimensions covered with source-backed points and "
                "deal-negotiation signals are complete"
            ),
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
                stop_condition=(
                    "all dimensions covered with source-backed points and "
                    "deal-negotiation signals are complete"
                ),
            )
        )
        seen.add(key)
    return contexts


def evaluate_packet_readiness(packet: CountryPacket) -> PacketReadinessReport:
    """Assess whether a packet is sufficient for deal negotiation preparation."""
    covered: set[str] = set()
    for point in packet.important_points:
        if point.support:
            covered.add(point.dimension)

    missing_dimensions: list[CountryPacketDimension] = [
        dimension for dimension in _CONTROLLED_DIMENSIONS if dimension not in covered
    ]

    missing_requirements: list[str] = []
    for dimension in missing_dimensions:
        missing_requirements.append(f"dimension.{dimension}")

    brief = packet.negotiation_brief
    if len(brief.priorities) < 2:
        missing_requirements.append("negotiation_brief.priorities")
    if len(brief.concession_options) < 1:
        missing_requirements.append("negotiation_brief.concession_options")
    if len(brief.non_negotiables) < 1:
        missing_requirements.append("negotiation_brief.non_negotiables")
    if len(brief.counterpart_asks) < 1:
        missing_requirements.append("negotiation_brief.counterpart_asks")
    if len(brief.deal_risks) < 1:
        missing_requirements.append("negotiation_brief.deal_risks")

    # Role-specific readiness emphasis.
    if packet.country_role == "origin" and len(brief.counterpart_asks) < 2:
        missing_requirements.append("negotiation_brief.counterpart_asks_depth")
    if packet.country_role != "origin" and len(brief.concession_options) < 2:
        missing_requirements.append("negotiation_brief.concession_options_depth")

    has_credible_source = any(
        source.credibility in {"high", "medium"} for source in packet.sources
    )
    if not has_credible_source:
        missing_requirements.append("sources.credible")

    deduped_missing = list(dict.fromkeys(missing_requirements))
    return PacketReadinessReport(
        is_sufficient=not deduped_missing,
        missing_dimensions=missing_dimensions,
        missing_requirements=deduped_missing,
    )


def evaluate_packet_sufficiency(packet: CountryPacket) -> tuple[bool, list[str]]:
    """Backward-compatible wrapper for older sufficiency call sites."""
    report = evaluate_packet_readiness(packet)
    return report.is_sufficient, report.missing_requirements
