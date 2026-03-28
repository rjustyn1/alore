"""Resolution-prep workflow request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.models.country_packet import CountryPacket

WorkflowStage = Literal[
    "queued",
    "curation_started",
    "origin_packet_in_progress",
    "origin_packet_ready",
    "substitute_packets_in_progress",
    "all_packets_ready",
    "awaiting_user_configuration",
    "failed",
    "partially_failed",
]

CountryPacketStatus = Literal["queued", "in_progress", "completed", "failed"]


class ResolutionPrepStartRequest(BaseModel):
    event_id: str
    resource_type: Literal["food", "energy"] | None = None
    commodity: str | None = None
    max_substitutes: int = Field(default=3, ge=1, le=10)


class ResolutionPrepKickoffData(BaseModel):
    workflow_id: str
    stage: WorkflowStage
    event_id: str
    origin_country: str = "Singapore"
    resource_type: Literal["food", "energy"]
    commodity: str
    origin_packet: CountryPacket | None = None
    reused_workflow: bool = False


class ResolutionPrepStatusData(BaseModel):
    workflow_id: str
    stage: WorkflowStage
    event_id: str
    resource_type: Literal["food", "energy"]
    commodity: str
    country_statuses: dict[str, CountryPacketStatus] = Field(default_factory=dict)
    packets: dict[str, CountryPacket] = Field(default_factory=dict)
