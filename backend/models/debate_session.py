"""Models for debate session orchestration and API contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DebateSourceInput(BaseModel):
    source_id: str
    title: str
    url: str


class DebateTeamInput(BaseModel):
    team_id: str
    name: str
    stance: str


class DebateBatchStartRequest(BaseModel):
    workflow_id: str
    topic: str
    goal: str
    input_country: str = "Singapore"
    singapore_info: dict[str, object]
    max_rounds: int = Field(default=3, ge=1, le=6)
    max_substitutes: int = Field(default=4, ge=1, le=8)
    max_parallel_graphs: int = Field(default=2, ge=1, le=4)

    @model_validator(mode="after")
    def validate_payload(self) -> "DebateBatchStartRequest":
        info = self.singapore_info
        if not isinstance(info, dict):
            raise ValueError("singapore_info must be a JSON object")

        has_main_ideas = bool(info.get("main_ideas"))
        has_points = bool(info.get("important_points"))
        has_sources = bool(info.get("sources"))
        if not (has_main_ideas or has_points or has_sources):
            raise ValueError(
                "singapore_info must include at least one of: "
                "main_ideas, important_points, or sources"
            )

        if not self.input_country.strip():
            raise ValueError("input_country must not be empty")
        return self


class SourceRecord(BaseModel):
    source_id: str
    title: str
    url: str
    published_at: str | None = None
    source_type: str = "brief"
    raw_text: str
    summary: str
    reliability: Literal["high", "medium", "low", "unknown"] = "unknown"
    tags: list[str] = Field(default_factory=list)


class ChunkRecord(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    chunk_index: int
    metadata: dict[str, object] = Field(default_factory=dict)


class EvidenceCard(BaseModel):
    evidence_id: str
    team_id: str
    source_id: str
    chunk_id: str
    summary: str
    snippet: str
    relevance_reason: str
    used_in_round: int


class TeamCitation(BaseModel):
    source_id: str
    chunk_id: str


class TeamTurnOutput(BaseModel):
    team_id: str
    round: int
    strategy_note: str
    argument: str
    claims: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    citations: list[TeamCitation] = Field(default_factory=list)
    self_critique: str


class ClaimLedgerEntry(BaseModel):
    claim_id: str
    round: int
    speaker_team_id: str
    claim_text: str
    evidence_ids: list[str] = Field(default_factory=list)
    judge_status: Literal["supported", "unsupported", "partially_supported"]
    judge_note: str


class TeamScore(BaseModel):
    groundedness: float
    relevance: float
    responsiveness: float
    strategic_strength: float
    overall: float


class UnsupportedClaim(BaseModel):
    team_id: str
    claim_text: str


class JudgeRoundGuidance(BaseModel):
    team_a: str
    team_b: str


class JudgeRoundOutput(BaseModel):
    round: int
    team_a_score: TeamScore
    team_b_score: TeamScore
    round_winner: str
    team_a_strengths: list[str] = Field(default_factory=list)
    team_b_strengths: list[str] = Field(default_factory=list)
    unsupported_claims: list[UnsupportedClaim] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    round_summary: str
    next_round_guidance: JudgeRoundGuidance
    should_continue: bool
    stop_reason: str | None = None


class RoundSummary(BaseModel):
    round: int
    winner: str
    summary: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    judge_note: str = ""


class FinalRecommendation(BaseModel):
    recommended_strategy: str
    why: str
    confidence: float


class TeamPosition(BaseModel):
    stance: str
    final_argument_summary: str


class DebateFinalResult(BaseModel):
    session_id: str
    topic: str
    goal: str
    status: Literal["completed", "fallback", "failed"]
    rounds_completed: int
    winner_team_id: str
    final_recommendation: FinalRecommendation
    recommended_action: str
    viability_score: float
    consensus_rationale: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    score_summary: dict[str, TeamScore] = Field(default_factory=dict)
    judge_summary: str
    key_supporting_evidence: list[dict[str, str]] = Field(default_factory=list)
    main_tradeoffs: list[str] = Field(default_factory=list)
    main_risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    team_positions: dict[str, TeamPosition] = Field(default_factory=dict)
    round_summaries: list[RoundSummary] = Field(default_factory=list)
    claim_ledger: list[ClaimLedgerEntry] = Field(default_factory=list)


class DebateBatchResult(BaseModel):
    workflow_id: str
    input_country: str
    substitutes: list[str] = Field(default_factory=list)
    results: dict[str, DebateFinalResult] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)


class DebateSessionArtifacts(BaseModel):
    session_id: str
    country: str
    result: DebateFinalResult
    rounds: list[JudgeRoundOutput] = Field(default_factory=list)
    claims: list[ClaimLedgerEntry] = Field(default_factory=list)
