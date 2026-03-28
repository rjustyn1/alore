"""In-memory repository for debate session artifacts."""

from __future__ import annotations

from threading import Lock

from backend.models.debate_session import (
    ClaimLedgerEntry,
    DebateSessionArtifacts,
    JudgeRoundOutput,
)


class DebateSessionRepository:
    """Small in-memory store for debate session outputs."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._by_session: dict[str, DebateSessionArtifacts] = {}

    def save(self, artifacts: DebateSessionArtifacts) -> None:
        with self._lock:
            self._by_session[artifacts.session_id] = artifacts

    def get(self, session_id: str) -> DebateSessionArtifacts | None:
        with self._lock:
            return self._by_session.get(session_id)

    def get_rounds(self, session_id: str) -> list[JudgeRoundOutput]:
        row = self.get(session_id)
        if row is None:
            return []
        return list(row.rounds)

    def get_claims(self, session_id: str) -> list[ClaimLedgerEntry]:
        row = self.get(session_id)
        if row is None:
            return []
        return list(row.claims)


_REPOSITORY = DebateSessionRepository()


def get_debate_session_repository() -> DebateSessionRepository:
    return _REPOSITORY
