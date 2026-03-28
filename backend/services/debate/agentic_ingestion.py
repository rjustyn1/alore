"""Agentic ingestion utilities for RAG preparation."""

from __future__ import annotations

from collections.abc import Sequence

from backend.models.debate_session import SourceRecord
from backend.services.debate.llm_client import call_llm_json, llm_available


def _string_list(raw: object, *, max_items: int = 6) -> list[str]:
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


def _agentic_summary_for_source(source: SourceRecord) -> tuple[str, list[str]] | None:
    if not llm_available():
        return None

    payload = call_llm_json(
        system_prompt=(
            "You prepare compact RAG-ready source summaries for a debate system. "
            "Return strict JSON only."
        ),
        user_prompt=(
            "Summarize the source for retrieval and argument grounding.\n"
            "Return JSON with keys: summary (string), key_points (string array).\n\n"
            f"Title: {source.title}\n"
            f"URL: {source.url}\n"
            f"Text:\n{source.raw_text}"
        ),
        temperature=0.1,
        max_tokens=450,
    )
    if not payload:
        return None
    summary = str(payload.get("summary", "")).strip()
    key_points = _string_list(payload.get("key_points", []), max_items=6)
    if not summary and not key_points:
        return None
    return summary, key_points


def enhance_sources_for_rag(sources: list[SourceRecord]) -> list[SourceRecord]:
    """Optionally summarize and enrich source text for team retrievers."""
    enriched: list[SourceRecord] = []
    for source in sources:
        agentic = _agentic_summary_for_source(source)
        if agentic is None:
            enriched.append(source)
            continue

        summary, key_points = agentic
        prepended = source.raw_text
        if key_points:
            lines = "\n".join(f"- {point}" for point in key_points)
            prepended = (
                f"RAG key points:\n{lines}\n\nSource content:\n{source.raw_text}"
            )

        enriched.append(
            source.model_copy(
                update={
                    "raw_text": prepended,
                    "summary": summary or source.summary,
                }
            )
        )
    return enriched
