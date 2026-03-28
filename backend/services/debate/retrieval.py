"""Lightweight in-memory retrieval utilities for debate sessions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.models.debate_session import ChunkRecord

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> set[str]:
    return {token for token in _WORD_RE.findall(text.lower()) if len(token) > 2}


@dataclass(slots=True)
class TeamRetriever:
    team_id: str
    chunks: list[ChunkRecord]
    used_chunk_ids: set[str] = field(default_factory=set)

    def retrieve(self, *, query: str, top_k: int = 3) -> list[ChunkRecord]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            query_tokens = _tokenize(" ".join(chunk.text for chunk in self.chunks[:4]))

        ranked: list[tuple[float, ChunkRecord]] = []
        for chunk in self.chunks:
            chunk_tokens = _tokenize(chunk.text)
            if not chunk_tokens:
                continue
            overlap = len(query_tokens.intersection(chunk_tokens))
            novelty = 0.25 if chunk.chunk_id not in self.used_chunk_ids else 0.0
            score = float(overlap) + novelty
            if score <= 0:
                continue
            ranked.append((score, chunk))

        ranked.sort(key=lambda row: (row[0], row[1].chunk_index), reverse=True)
        selected = [chunk for _, chunk in ranked[:top_k]]
        self.used_chunk_ids.update(chunk.chunk_id for chunk in selected)
        return selected


def build_team_retrievers(
    *,
    chunks: list[ChunkRecord],
    team_ids: tuple[str, str],
) -> dict[str, TeamRetriever]:
    """Build one retriever handle per team over the session corpus."""
    return {
        team_ids[0]: TeamRetriever(team_id=team_ids[0], chunks=list(chunks)),
        team_ids[1]: TeamRetriever(team_id=team_ids[1], chunks=list(chunks)),
    }


def build_neutral_pool(chunks: list[ChunkRecord]) -> list[ChunkRecord]:
    """Return judge-facing neutral evidence pool from the shared corpus."""
    return list(chunks)
