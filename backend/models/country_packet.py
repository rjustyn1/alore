"""Country packet models for resolution preparation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CountryRole = Literal["origin", "disrupted_supplier", "substitute_candidate"]
CountryPacketDimension = Literal[
    "supply_capacity",
    "trade_relevance",
    "cost",
    "logistics",
    "risk",
    "sustainability",
]


class CountryPacketPoint(BaseModel):
    dimension: CountryPacketDimension
    point: str
    support: list[str] = Field(default_factory=list)


class CountryPacketSource(BaseModel):
    id: str
    title: str
    url: str
    credibility: Literal["high", "medium", "low", "unknown"] = "unknown"
    date: str = ""


class CountryNegotiationBrief(BaseModel):
    priorities: list[str] = Field(default_factory=list)
    concession_options: list[str] = Field(default_factory=list)
    non_negotiables: list[str] = Field(default_factory=list)
    counterpart_asks: list[str] = Field(default_factory=list)
    deal_risks: list[str] = Field(default_factory=list)
    readiness_summary: str = ""


class CountryPacket(BaseModel):
    country: str
    country_role: CountryRole
    resource_type: Literal["food", "energy"]
    commodity: str
    main_ideas: list[str] = Field(default_factory=list)
    important_points: list[CountryPacketPoint] = Field(default_factory=list)
    sources: list[CountryPacketSource] = Field(default_factory=list)
    negotiation_brief: CountryNegotiationBrief = Field(
        default_factory=CountryNegotiationBrief
    )
    source_mode: Literal["live", "fallback_seed"] = "fallback_seed"
