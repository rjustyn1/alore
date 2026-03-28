"""Simple deterministic chunking for debate session sources."""

from __future__ import annotations

import re
import uuid

from backend.models.debate_session import ChunkRecord, SourceRecord


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def chunk_sources(
    sources: list[SourceRecord],
    *,
    max_chars: int = 420,
) -> list[ChunkRecord]:
    """Chunk source text into stable serializable records."""
    chunks: list[ChunkRecord] = []
    for source in sources:
        sentences = _split_sentences(source.raw_text)
        if not sentences:
            continue

        bucket: list[str] = []
        bucket_len = 0
        chunk_index = 0
        for sentence in sentences:
            next_len = bucket_len + len(sentence) + 1
            if bucket and next_len > max_chars:
                text = " ".join(bucket).strip()
                chunks.append(
                    ChunkRecord(
                        chunk_id=f"chk_{uuid.uuid4().hex[:8]}",
                        source_id=source.source_id,
                        text=text,
                        chunk_index=chunk_index,
                        metadata={
                            "title": source.title,
                            "tags": list(source.tags),
                            "url": source.url,
                        },
                    )
                )
                chunk_index += 1
                bucket = [sentence]
                bucket_len = len(sentence)
                continue
            bucket.append(sentence)
            bucket_len = next_len

        if bucket:
            text = " ".join(bucket).strip()
            chunks.append(
                ChunkRecord(
                    chunk_id=f"chk_{uuid.uuid4().hex[:8]}",
                    source_id=source.source_id,
                    text=text,
                    chunk_index=chunk_index,
                    metadata={
                        "title": source.title,
                        "tags": list(source.tags),
                        "url": source.url,
                    },
                )
            )

    return chunks
