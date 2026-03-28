"""Disruption monitor domain models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DisruptionEvent(BaseModel):
    event_id: str
    from_country: str
    severity: Literal["WARNING", "CONSTRAINED", "DISRUPTED", "CRITICAL"]
    resource_type: Literal["food", "energy"]
    commodity: str
    headline: str
    source_urls: list[str] = Field(default_factory=list)


class DisruptionMonitorRunResult(BaseModel):
    run_id: str
    status: Literal["completed", "failed", "skipped_overlap"]
    trigger: Literal["manual", "scheduled"]
    emitted_events: list[DisruptionEvent] = Field(default_factory=list)
