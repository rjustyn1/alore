"""Persistence models for disruption monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DisruptionEventRecord:
    """Disruption event record persisted in local database."""

    event_id: str
    from_country: str
    severity: str
    resource_type: str
    commodity: str
    headline: str
    source_urls: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_seen_at: str = ""


@dataclass(slots=True)
class DisruptionRunRecord:
    """Disruption monitor run history record."""

    run_id: str
    status: str
    trigger: str
    started_at: str
    finished_at: str
    emitted_count: int = 0
    error_message: str = ""


@dataclass(slots=True)
class ResolutionWorkflowRecord:
    """Resolution-prep workflow record persisted in local database."""

    workflow_id: str
    normalized_key: str
    event_id: str
    origin_country: str
    disrupted_supplier_country: str
    resource_type: str
    commodity: str
    stage: str
    country_statuses: dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    error_message: str = ""


@dataclass(slots=True)
class CountryPacketRecord:
    """Persisted country packet row for one workflow + country."""

    workflow_id: str
    country: str
    status: str
    packet_json: dict[str, object] = field(default_factory=dict)
    updated_at: str = ""


@dataclass(slots=True)
class DisruptionSubstituteSnapshotRecord:
    """Persisted substitute-country snapshot for one event/resource/commodity."""

    event_id: str
    resource_type: str
    commodity: str
    source: str
    candidates: list[dict[str, object]] = field(default_factory=list)
    updated_at: str = ""
