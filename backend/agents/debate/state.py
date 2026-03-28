"""Structured state for debate agent graph execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models.debate_session import (
    ChunkRecord,
    ClaimLedgerEntry,
    DebateFinalResult,
    EvidenceCard,
    JudgeRoundOutput,
    RoundSummary,
    SourceRecord,
    TeamScore,
    TeamTurnOutput,
)
from backend.services.debate.retrieval import TeamRetriever


@dataclass(slots=True)
class DebateGraphState:
    session_id: str
    topic: str
    goal: str
    max_rounds: int
    input_country: str
    substitute_country: str
    team_a_stance: str
    team_b_stance: str
    current_round: int = 0
    status: str = "running"

    source_records: list[SourceRecord] = field(default_factory=list)
    chunk_records: list[ChunkRecord] = field(default_factory=list)
    team_rag_handles: dict[str, str] = field(default_factory=dict)
    neutral_evidence_pool: list[ChunkRecord] = field(default_factory=list)

    used_evidence_by_team: dict[str, list[str]] = field(
        default_factory=lambda: {"team_a": [], "team_b": []}
    )
    team_turns: list[TeamTurnOutput] = field(default_factory=list)
    claim_ledger: list[ClaimLedgerEntry] = field(default_factory=list)
    judge_rounds: list[JudgeRoundOutput] = field(default_factory=list)
    round_summaries: list[RoundSummary] = field(default_factory=list)
    aggregated_pros: list[str] = field(default_factory=list)
    aggregated_cons: list[str] = field(default_factory=list)
    score_summary: dict[str, TeamScore] = field(default_factory=dict)
    score_history: dict[str, list[TeamScore]] = field(
        default_factory=lambda: {"team_a": [], "team_b": []}
    )

    consensus_rationale: str | None = None
    viability_score: float | None = None
    recommended_action: str | None = None
    final_result: DebateFinalResult | None = None

    judge_guidance_by_team: dict[str, str] = field(
        default_factory=lambda: {
            "team_a": (
                "Prioritize resilience while keeping short-term costs manageable."
            ),
            "team_b": (
                "Present export profitability with domestic-risk safeguards and "
                "delivery reliability."
            ),
        }
    )
    last_opponent_argument_by_team: dict[str, str] = field(
        default_factory=lambda: {"team_a": "", "team_b": ""}
    )

    evidence_cards: list[EvidenceCard] = field(default_factory=list)

    # Runtime handles (kept in-memory, not persisted).
    team_retrievers: dict[str, TeamRetriever] = field(default_factory=dict, repr=False)
