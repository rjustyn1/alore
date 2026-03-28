"""Disruption monitor orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Literal, cast

from backend.db.models import (
    DisruptionEventRecord,
    DisruptionRunRecord,
    DisruptionSubstituteSnapshotRecord,
)
from backend.db.repositories import DisruptionRepository
from backend.models.disruption_event import DisruptionEvent, DisruptionMonitorRunResult
from backend.services.tinyfish_client import TinyFishClient
from backend.utils.substitute_finder import find_substitutes_for_event

logger = logging.getLogger(__name__)

_RUN_LOCK = asyncio.Lock()
_COLLECTION_URL = "https://news.google.com/search?q=singapore+supply+chain+disruption"

_KNOWN_COUNTRIES = (
    "Australia",
    "Brazil",
    "China",
    "India",
    "Indonesia",
    "Iran",
    "Iraq",
    "Japan",
    "Malaysia",
    "Qatar",
    "Russia",
    "Saudi Arabia",
    "Thailand",
    "Ukraine",
    "United Arab Emirates",
    "United States",
    "Vietnam",
)

_RESOURCE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "energy": (
        "crude",
        "oil",
        "petroleum",
        "gas",
        "lng",
        "coal",
        "diesel",
        "fuel",
        "electricity",
    ),
    "food": (
        "rice",
        "wheat",
        "corn",
        "soy",
        "soybean",
        "soybeans",
        "palm oil",
        "poultry",
        "beef",
        "fish",
        "seafood",
        "sugar",
        "dairy",
        "fruit",
        "fruits",
        "vegetable",
        "vegetables",
        "coffee",
    ),
}

_CANONICAL_COMMODITY: dict[str, str] = {
    "crude": "crude_oil",
    "oil": "crude_oil",
    "petroleum": "crude_oil",
    "gas": "natural_gas",
    "lng": "natural_gas",
    "diesel": "refined_fuel",
    "fuel": "refined_fuel",
    "soy": "soybeans",
    "soybean": "soybeans",
    "soybeans": "soybeans",
    "fruit": "fruits",
    "vegetable": "vegetables",
}

_FALLBACK_DOCUMENTS: list[dict[str, str]] = [
    {
        "source_id": "fallback-1",
        "url": "https://example.com/disruption-1",
        "title": "Shipping chokepoint disruptions pressure crude oil routes from Iran",
        "content": (
            "Maritime delays affecting crude oil shipments from Iran could raise "
            "near-term energy supply risk for Asian importers including Singapore."
        ),
        "collected_at": "2026-03-27T00:00:00Z",
    }
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _new_run_id() -> str:
    return f"{_utc_now().strftime('run_%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"


def _normalize_commodity(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _infer_country(text: str) -> str | None:
    for country in _KNOWN_COUNTRIES:
        if re.search(rf"\b{re.escape(country)}\b", text, flags=re.IGNORECASE):
            return country
    return None


def _infer_severity(
    text: str,
) -> Literal["WARNING", "CONSTRAINED", "DISRUPTED", "CRITICAL"]:
    lowered = text.lower()
    if any(token in lowered for token in ("critical", "halt", "blockade", "attack")):
        return cast(Literal["CRITICAL"], "CRITICAL")
    if any(token in lowered for token in ("disrupt", "shortage", "sanction", "ban")):
        return cast(Literal["DISRUPTED"], "DISRUPTED")
    if any(
        token in lowered for token in ("delay", "constraint", "tighten", "restrict")
    ):
        return cast(Literal["CONSTRAINED"], "CONSTRAINED")
    return cast(Literal["WARNING"], "WARNING")


def _infer_resource_pairs(text: str) -> list[tuple[str, str]]:
    lowered = text.lower()
    pairs: list[tuple[str, str]] = []
    for category, keywords in _RESOURCE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                normalized = _normalize_commodity(keyword)
                if not normalized:
                    continue
                canonical = _CANONICAL_COMMODITY.get(normalized, normalized)
                pair = (category, canonical)
                if pair not in pairs:
                    pairs.append(pair)
    return pairs


def _extract_documents(raw_result: object) -> list[dict[str, str]]:
    if isinstance(raw_result, str):
        try:
            decoded = json.loads(raw_result)
        except json.JSONDecodeError:
            return []
        return _extract_documents(decoded)

    if isinstance(raw_result, Mapping):
        for key in ("documents", "articles", "results", "items", "data"):
            value = raw_result.get(key)
            extracted = _extract_documents(value)
            if extracted:
                return extracted
        candidate = _extract_document_row(raw_result)
        return [candidate] if candidate else []

    if isinstance(raw_result, Sequence) and not isinstance(
        raw_result, str | bytes | bytearray
    ):
        output: list[dict[str, str]] = []
        for row in raw_result:
            if isinstance(row, Mapping):
                candidate = _extract_document_row(row)
                if candidate:
                    output.append(candidate)
        return output
    return []


def _extract_document_row(row: Mapping[str, object]) -> dict[str, str] | None:
    title = str(row.get("title", "")).strip()
    content = str(
        row.get("content", row.get("summary", row.get("snippet", "")))
    ).strip()
    url = _extract_source_url(row)
    if not title and not content:
        return None
    if not url:
        return None
    source_id = str(row.get("source_id", url)).strip() or url
    collected_at = (
        str(row.get("collected_at", _utc_now_iso())).strip() or _utc_now_iso()
    )
    return {
        "source_id": source_id,
        "url": url,
        "title": title or "Untitled disruption signal",
        "content": content or title,
        "collected_at": collected_at,
    }


def _extract_source_url(row: Mapping[str, object]) -> str:
    for key in ("url", "link", "source_url", "source_link", "article_url", "href"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    source_value = row.get("source")
    if isinstance(source_value, str) and source_value.strip():
        return source_value.strip()
    if isinstance(source_value, Mapping):
        source_url = source_value.get("url", source_value.get("link", ""))
        if isinstance(source_url, str) and source_url.strip():
            return source_url.strip()
    return ""


def _classify_documents(
    documents: Sequence[Mapping[str, object]],
) -> list[DisruptionEvent]:
    candidates: list[DisruptionEvent] = []
    for document in documents:
        title = str(document.get("title", "")).strip()
        content = str(document.get("content", "")).strip()
        text = f"{title} {content}"
        from_country = _infer_country(text)
        if not from_country:
            continue

        impacted_pairs = _infer_resource_pairs(text)
        if not impacted_pairs:
            continue

        source_urls = _extract_document_source_urls(document)
        if not source_urls:
            continue

        severity = _infer_severity(text)
        headline = title.strip() or "Supply disruption signal detected"
        for resource_type, commodity in impacted_pairs:
            candidates.append(
                DisruptionEvent(
                    event_id="",
                    from_country=from_country,
                    severity=severity,
                    resource_type=cast(Literal["food", "energy"], resource_type),
                    commodity=commodity,
                    headline=headline,
                    source_urls=source_urls,
                )
            )
    return candidates


def _extract_document_source_urls(document: Mapping[str, object]) -> list[str]:
    urls: list[str] = []
    for key in ("url", "link", "source_url", "source_link", "article_url", "href"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            urls.append(value.strip())
    if not urls:
        fallback = _extract_source_url(document)
        if fallback:
            urls.append(fallback)
    return list(dict.fromkeys(urls))


def _match_existing_event(
    existing_events: Sequence[DisruptionEventRecord],
    candidate: DisruptionEvent,
) -> DisruptionEventRecord | None:
    for record in existing_events:
        if record.from_country != candidate.from_country:
            continue
        if record.resource_type != candidate.resource_type:
            continue
        if _normalize_commodity(record.commodity) != _normalize_commodity(
            candidate.commodity
        ):
            continue
        return record
    return None


def _is_meaningful_update(
    existing: DisruptionEventRecord,
    candidate: DisruptionEvent,
    merged_urls: Sequence[str],
) -> bool:
    if existing.severity != candidate.severity:
        return True
    if existing.headline != candidate.headline:
        return True
    if len(merged_urls) > len(existing.source_urls):
        return True
    return False


def _record_to_event(record: DisruptionEventRecord) -> DisruptionEvent:
    return DisruptionEvent(
        event_id=record.event_id,
        from_country=record.from_country,
        severity=cast(
            Literal["WARNING", "CONSTRAINED", "DISRUPTED", "CRITICAL"],
            record.severity,
        ),
        resource_type=cast(Literal["food", "energy"], record.resource_type),
        commodity=_normalize_commodity(record.commodity),
        headline=record.headline,
        source_urls=list(record.source_urls),
    )


async def _refresh_substitute_snapshots(
    repository: DisruptionRepository,
    event_id: str,
) -> None:
    try:
        substitute_result = await find_substitutes_for_event(
            event_id,
            repository=repository,
        )
    except Exception as exc:
        logger.warning(
            "Substitute generation failed for %s; skipping snapshot refresh (%s)",
            event_id,
            exc,
        )
        return

    for row in substitute_result.substitutes:
        candidates: list[dict[str, object]] = []
        for candidate in row.countries:
            candidates.append(
                {
                    "country": candidate.country,
                    "score": candidate.score,
                    "reason": candidate.reason,
                    "matched_commodities": list(candidate.matched_commodities),
                }
            )
        repository.upsert_substitute_snapshot(
            DisruptionSubstituteSnapshotRecord(
                event_id=event_id,
                resource_type=row.resource,
                commodity=row.commodity,
                source=row.source,
                candidates=candidates,
            )
        )


async def _collect_documents() -> list[dict[str, str]]:
    goal = (
        "Collect reputable recent news about disruptions with possible impact on "
        "Singapore food or energy imports. Return JSON only as "
        '{"documents":[{"source_id":"...","url":"...","title":"...",'
        '"content":"...","collected_at":"ISO8601"}]}.'
    )
    payload = await TinyFishClient().run(url=_COLLECTION_URL, goal=goal)
    status = str(payload.get("status", "")).upper()
    if status != "COMPLETED":
        raise RuntimeError(f"TinyFish run did not complete successfully: {status}")
    return _extract_documents(payload.get("result"))


def _get_repository() -> DisruptionRepository:
    db_path = os.getenv("DISRUPTION_DB_PATH", "backend.db")
    return DisruptionRepository(db_path=db_path)


def list_persisted_events(*, limit: int = 100) -> list[DisruptionEvent]:
    """Return most-recent persisted disruption events."""
    repository = _get_repository()
    events = repository.list_events()
    sorted_events = sorted(
        events,
        key=lambda row: (row.updated_at, row.created_at, row.event_id),
        reverse=True,
    )
    return [_record_to_event(row) for row in sorted_events[:limit]]


def get_persisted_event(event_id: str) -> DisruptionEvent:
    """Return one persisted disruption event."""
    repository = _get_repository()
    record = repository.get_event_by_id(event_id)
    if record is None:
        raise ValueError(f"Disruption event not found: {event_id}")
    return _record_to_event(record)


async def run_monitor_once(
    trigger: Literal["manual", "scheduled"],
) -> DisruptionMonitorRunResult:
    """Run one disruption-monitor cycle with overlap protection."""
    repository = _get_repository()
    run_id = _new_run_id()
    started_at = _utc_now_iso()

    if _RUN_LOCK.locked():
        finished_at = _utc_now_iso()
        repository.insert_run(
            DisruptionRunRecord(
                run_id=run_id,
                status="skipped_overlap",
                trigger=trigger,
                started_at=started_at,
                finished_at=finished_at,
            )
        )
        return DisruptionMonitorRunResult(
            run_id=run_id,
            status="skipped_overlap",
            trigger=trigger,
        )

    async with _RUN_LOCK:
        try:
            documents = await _collect_documents()
        except Exception as exc:
            logger.warning(
                "Live disruption document collection failed; using fallback (%s)", exc
            )
            documents = list(_FALLBACK_DOCUMENTS)

        try:
            candidates = _classify_documents(documents)
            emitted_count = 0
            emitted_events_by_id: dict[str, DisruptionEvent] = {}

            for candidate in candidates:
                same_country_records = repository.get_events_by_country(
                    candidate.from_country
                )
                matched = _match_existing_event(same_country_records, candidate)
                now_iso = _utc_now_iso()

                if matched is None:
                    event_id = f"evt_{uuid.uuid4().hex[:10]}"
                    new_record = DisruptionEventRecord(
                        event_id=event_id,
                        from_country=candidate.from_country,
                        severity=candidate.severity,
                        resource_type=candidate.resource_type,
                        commodity=_normalize_commodity(candidate.commodity),
                        headline=candidate.headline,
                        source_urls=list(dict.fromkeys(candidate.source_urls)),
                        created_at=now_iso,
                        updated_at=now_iso,
                        last_seen_at=now_iso,
                    )
                    inserted = repository.insert_event(new_record)
                    emitted_events_by_id[inserted.event_id] = _record_to_event(inserted)
                    emitted_count += 1
                    continue

                merged_urls = list(
                    dict.fromkeys(matched.source_urls + candidate.source_urls)
                )
                if _is_meaningful_update(
                    matched,
                    candidate,
                    merged_urls=merged_urls,
                ):
                    updated_record = DisruptionEventRecord(
                        event_id=matched.event_id,
                        from_country=matched.from_country,
                        severity=candidate.severity,
                        resource_type=matched.resource_type,
                        commodity=matched.commodity,
                        headline=candidate.headline,
                        source_urls=merged_urls,
                        created_at=matched.created_at,
                        updated_at=now_iso,
                        last_seen_at=now_iso,
                    )
                    updated = repository.update_event(updated_record)
                    emitted_events_by_id[updated.event_id] = _record_to_event(updated)
                    emitted_count += 1
                else:
                    repository.touch_event(matched.event_id)

            for event_id in emitted_events_by_id:
                await _refresh_substitute_snapshots(repository, event_id)

            finished_at = _utc_now_iso()
            repository.insert_run(
                DisruptionRunRecord(
                    run_id=run_id,
                    status="completed",
                    trigger=trigger,
                    started_at=started_at,
                    finished_at=finished_at,
                    emitted_count=emitted_count,
                )
            )
            return DisruptionMonitorRunResult(
                run_id=run_id,
                status="completed",
                trigger=trigger,
                emitted_events=list(emitted_events_by_id.values()),
            )
        except Exception as exc:
            logger.exception("Disruption monitor failed during processing")
            finished_at = _utc_now_iso()
            repository.insert_run(
                DisruptionRunRecord(
                    run_id=run_id,
                    status="failed",
                    trigger=trigger,
                    started_at=started_at,
                    finished_at=finished_at,
                    error_message=str(exc),
                )
            )
            return DisruptionMonitorRunResult(
                run_id=run_id,
                status="failed",
                trigger=trigger,
                emitted_events=[],
            )
