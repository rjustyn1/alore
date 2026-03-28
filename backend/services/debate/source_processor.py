"""Source normalization for session-scoped debate runs."""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping, Sequence

from backend.models.debate_session import SourceRecord


def _to_string_list(raw: object) -> list[str]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    items: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            continue
        clean = value.strip()
        if clean and clean not in items:
            items.append(clean)
    return items


def _extract_info_text(info: Mapping[str, object]) -> str:
    lines: list[str] = []
    for idea in _to_string_list(info.get("main_ideas", [])):
        lines.append(f"Main idea: {idea}")

    points = info.get("important_points", [])
    if isinstance(points, Sequence) and not isinstance(points, str | bytes | bytearray):
        for row in points:
            if not isinstance(row, Mapping):
                continue
            point = str(row.get("point", "")).strip()
            dimension = str(row.get("dimension", "")).strip()
            if point:
                if dimension:
                    lines.append(f"{dimension}: {point}")
                else:
                    lines.append(point)

    negotiation = info.get("negotiation_brief", {})
    if isinstance(negotiation, Mapping):
        for key in (
            "priorities",
            "concession_options",
            "non_negotiables",
            "counterpart_asks",
            "deal_risks",
        ):
            for value in _to_string_list(negotiation.get(key, [])):
                lines.append(f"{key}: {value}")
        summary = str(negotiation.get("readiness_summary", "")).strip()
        if summary:
            lines.append(f"readiness_summary: {summary}")

    return "\n".join(lines).strip()


def _normalize_tags(country: str, role: str) -> list[str]:
    country_tag = re.sub(r"[^a-z0-9]+", "_", country.strip().lower()).strip("_")
    role_tag = re.sub(r"[^a-z0-9]+", "_", role.strip().lower()).strip("_")
    return [tag for tag in (country_tag, role_tag, "debate") if tag]


def build_source_records(
    *,
    country: str,
    team_role: str,
    info: Mapping[str, object],
) -> list[SourceRecord]:
    """Build stable source records from filtered country information."""
    base_text = _extract_info_text(info)
    source_rows = info.get("sources", [])

    records: list[SourceRecord] = []
    if isinstance(source_rows, Sequence) and not isinstance(
        source_rows, str | bytes | bytearray
    ):
        for index, row in enumerate(source_rows, start=1):
            if not isinstance(row, Mapping):
                continue
            title = str(row.get("title", f"{country} brief source {index}")).strip()
            url = str(row.get("url", "")).strip() or f"urn:{country}:{index}"
            content = str(
                row.get("content", row.get("snippet", row.get("summary", "")))
            ).strip()
            raw_text = content or base_text
            if not raw_text:
                continue
            source_id = str(row.get("id", "")).strip() or f"src_{uuid.uuid4().hex[:8]}"
            records.append(
                SourceRecord(
                    source_id=source_id,
                    title=title or f"{country} source {index}",
                    url=url,
                    raw_text=raw_text,
                    summary=(raw_text[:200] + "...")
                    if len(raw_text) > 200
                    else raw_text,
                    reliability="medium",
                    tags=_normalize_tags(country, team_role),
                )
            )

    if records:
        return records

    fallback_text = base_text or (
        f"No detailed source content supplied for {country}. "
        "Use cautious assumptions and acknowledge uncertainty."
    )
    return [
        SourceRecord(
            source_id=f"src_{uuid.uuid4().hex[:8]}",
            title=f"{country} synthesized brief",
            url=f"urn:{country}:synthesized",
            raw_text=fallback_text,
            summary=(fallback_text[:200] + "...")
            if len(fallback_text) > 200
            else fallback_text,
            reliability="low",
            tags=_normalize_tags(country, team_role),
        )
    ]
