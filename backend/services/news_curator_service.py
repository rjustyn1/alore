"""News curator orchestration."""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Mapping, Sequence
from datetime import datetime

from backend.cache.file_cache import JsonFileCache
from backend.cache.memory_cache import MemoryCache
from backend.models.news_curator import NewsArticle, NewsCuratorResponse
from backend.services.tinyfish_client import TinyFishClient

logger = logging.getLogger(__name__)

_NEWS_BASE_URL = "https://news.google.com/search?q=singapore+supply+chain"
_NEWS_CACHE: MemoryCache[NewsCuratorResponse] = MemoryCache()
_NEWS_PERSISTED_CACHE: JsonFileCache[NewsCuratorResponse] = JsonFileCache(
    path=os.getenv("NEWS_CACHE_FILE", "backend/cache/runtime/news_curator.json"),
    serializer=lambda value: value.model_dump(mode="json"),
    deserializer=lambda payload: NewsCuratorResponse.model_validate(payload),
)

_FALLBACK_INTERNAL: list[dict[str, str]] = [
    {
        "title": "Singapore strengthens LNG handling capacity",
        "hook": "Terminal upgrades improve energy import resilience in Singapore.",
        "url": "https://example.com/internal-1",
    },
    {
        "title": "New import screening for fresh produce in Singapore",
        "hook": "Food authorities introduced tighter checks on inbound shipments.",
        "url": "https://example.com/internal-2",
    },
    {
        "title": "Port operations optimization to reduce cargo delays",
        "hook": "Singapore logistics planners announced throughput improvements.",
        "url": "https://example.com/internal-3",
    },
]

_FALLBACK_EXTERNAL: list[dict[str, str]] = [
    {
        "title": "Red Sea shipping disruptions raise regional freight risk",
        "hook": "Continued vessel rerouting may increase Asia-bound transit times.",
        "url": "https://example.com/external-1",
    },
    {
        "title": "Global wheat output concerns pressure import markets",
        "hook": "Weather volatility threatens food commodity availability.",
        "url": "https://example.com/external-2",
    },
    {
        "title": "Major exporter reviews fuel shipment policies",
        "hook": "Policy uncertainty could tighten near-term energy supply.",
        "url": "https://example.com/external-3",
    },
]

_SEVERITY_TERMS = (
    "critical",
    "severe",
    "disruption",
    "shortage",
    "ban",
    "sanction",
    "attack",
    "halt",
    "crisis",
)


def _first_two_sentences(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(parts) <= 2:
        return cleaned
    return " ".join(parts[:2]).strip()


def _safe_parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_article_row(row: Mapping[str, object]) -> dict[str, object] | None:
    title = ""
    for key in ("title", "headline", "name"):
        raw_title = row.get(key)
        if isinstance(raw_title, str) and raw_title.strip():
            title = raw_title.strip()
            break
    if not title:
        return None

    url = ""
    for key in ("url", "link"):
        raw_url = row.get(key)
        if isinstance(raw_url, str) and raw_url.strip():
            url = raw_url.strip()
            break
    if not url:
        url = "https://example.com/news-placeholder"

    hook_source = ""
    for key in ("hook", "summary", "snippet", "description", "content"):
        raw_hook = row.get(key)
        if isinstance(raw_hook, str) and raw_hook.strip():
            hook_source = raw_hook.strip()
            break
    raw_published = row.get("published_at")
    published_at = (
        _safe_parse_datetime(raw_published) if isinstance(raw_published, str) else None
    )

    return {
        "title": title,
        "url": url,
        "hook": _first_two_sentences(hook_source or title),
        "published_at": published_at,
    }


def _extract_articles(raw_result: object) -> list[dict[str, object]]:
    if isinstance(raw_result, str):
        try:
            decoded = json.loads(raw_result)
        except json.JSONDecodeError:
            return []
        return _extract_articles(decoded)

    if isinstance(raw_result, Mapping):
        for key in ("articles", "results", "items", "data", "internal", "external"):
            value = raw_result.get(key)
            extracted = _extract_articles(value)
            if extracted:
                return extracted
        candidate = _extract_article_row(raw_result)
        return [candidate] if candidate else []

    if isinstance(raw_result, Sequence) and not isinstance(
        raw_result, str | bytes | bytearray
    ):
        output: list[dict[str, object]] = []
        for row in raw_result:
            if isinstance(row, Mapping):
                parsed = _extract_article_row(row)
                if parsed:
                    output.append(parsed)
        return output

    return []


def _build_goal(bucket: str, lookback_days: int) -> str:
    if bucket == "internal":
        focus = (
            "Find recent news that explicitly mentions Singapore and direct impact on "
            "supply chain, food imports, energy imports, or logistics."
        )
    else:
        focus = (
            "Find recent non-Singapore-headlined news with strong immediate "
            "operational impact on Singapore supply chain, food, or energy imports."
        )
    return (
        f"{focus} Limit to the last {lookback_days} days when possible. "
        'Return only JSON as {"articles":[{"title":"...","hook":"...","url":"...",'
        '"published_at":"ISO8601 optional"}]}.'
    )


def _rank_candidates(
    candidates: list[dict[str, object]], bucket: str
) -> list[NewsArticle]:
    def sort_key(row: dict[str, object]) -> tuple[int, int]:
        title = str(row.get("title", "")).lower()
        hook = str(row.get("hook", "")).lower()
        text = f"{title} {hook}"
        severity_score = sum(term in text for term in _SEVERITY_TERMS)
        singapore_score = int("singapore" in text and bucket == "internal")
        published_at = row.get("published_at")
        if isinstance(published_at, datetime):
            recency_score = int(published_at.timestamp())
        else:
            recency_score = 0
        return (severity_score + singapore_score, recency_score)

    ranked_rows = sorted(candidates, key=sort_key, reverse=True)
    output: list[NewsArticle] = []
    for index, row in enumerate(ranked_rows[:3], start=1):
        output.append(
            NewsArticle(
                rank=index,
                title=str(row["title"]),
                hook=str(row["hook"]),
                url=str(row["url"]),
            )
        )
    return output


def _dedupe_by_title(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in candidates:
        title_key = str(row.get("title", "")).strip().lower()
        if not title_key or title_key in seen:
            continue
        seen.add(title_key)
        deduped.append(row)
    return deduped


async def _fetch_bucket_articles(
    bucket: str, lookback_days: int
) -> list[dict[str, object]]:
    payload = await TinyFishClient().run(
        url=_NEWS_BASE_URL, goal=_build_goal(bucket, lookback_days)
    )
    status = str(payload.get("status", "")).upper()
    if status != "COMPLETED":
        raise RuntimeError(f"TinyFish run did not complete successfully: {status}")
    return _extract_articles(payload.get("result"))


def _fallback_response() -> NewsCuratorResponse:
    internal = [
        NewsArticle(rank=index, title=item["title"], hook=item["hook"], url=item["url"])
        for index, item in enumerate(_FALLBACK_INTERNAL[:3], start=1)
    ]
    external = [
        NewsArticle(rank=index, title=item["title"], hook=item["hook"], url=item["url"])
        for index, item in enumerate(_FALLBACK_EXTERNAL[:3], start=1)
    ]
    return NewsCuratorResponse(internal=internal, external=external)


async def get_singapore_news_curation() -> NewsCuratorResponse:
    """Return curated Singapore-relevant supply-chain news."""
    cache_entry = _NEWS_CACHE.get()
    if cache_entry is None:
        persisted_entry = _NEWS_PERSISTED_CACHE.get()
        if persisted_entry is not None:
            cache_entry = _NEWS_CACHE.set(persisted_entry.value)

    if cache_entry:
        return cache_entry.value.model_copy(deep=True)

    try:
        internal = _dedupe_by_title(await _fetch_bucket_articles("internal", 14))
        external = _dedupe_by_title(await _fetch_bucket_articles("external", 14))

        if len(internal) < 3:
            internal = _dedupe_by_title(
                internal + await _fetch_bucket_articles("internal", 31)
            )
        if len(external) < 3:
            external = _dedupe_by_title(
                external + await _fetch_bucket_articles("external", 31)
            )

        internal_titles = {str(row["title"]).strip().lower() for row in internal}
        external = [
            row
            for row in external
            if str(row["title"]).strip().lower() not in internal_titles
        ]

        response = NewsCuratorResponse(
            internal=_rank_candidates(internal, "internal"),
            external=_rank_candidates(external, "external"),
        )
        _NEWS_CACHE.set(response)
        _NEWS_PERSISTED_CACHE.set(response)
        return response.model_copy(deep=True)
    except Exception as exc:
        logger.warning("News curation live retrieval failed; using fallback (%s)", exc)
        if cache_entry:
            return cache_entry.value.model_copy(deep=True)
        return _fallback_response()
