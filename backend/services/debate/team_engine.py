"""Team-turn generation engine for debate rounds."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from backend.models.debate_session import (
    EvidenceCard,
    TeamCitation,
    TeamTurnOutput,
)
from backend.services.debate.retrieval import TeamRetriever


def _first_sentence(text: str) -> str:
    clean = " ".join(text.split()).strip()
    if not clean:
        return ""
    for delimiter in (". ", "? ", "! "):
        if delimiter in clean:
            return clean.split(delimiter, 1)[0].strip() + "."
    return clean[:180] + ("..." if len(clean) > 180 else "")


def _build_claims(
    *,
    stance: str,
    evidence_cards: Sequence[EvidenceCard],
    goal: str,
) -> list[str]:
    claims: list[str] = []
    for card in evidence_cards[:2]:
        claims.append(card.summary)
    if not claims:
        claims.append(
            f"{stance} remains the safer path to satisfy goal: {goal.lower()}."
        )
    claims.append("Implementation should include phased execution safeguards.")
    return list(dict.fromkeys(claims))[:3]


def generate_team_turn(
    *,
    team_id: str,
    team_name: str,
    stance: str,
    topic: str,
    goal: str,
    round_number: int,
    retriever: TeamRetriever,
    judge_guidance: str,
    opponent_argument: str,
) -> tuple[TeamTurnOutput, list[EvidenceCard]]:
    """Generate one team turn using a deterministic retrieve-then-draft flow."""
    query = " ".join(
        value
        for value in [topic, goal, stance, judge_guidance, opponent_argument]
        if value.strip()
    )
    chunks = retriever.retrieve(query=query, top_k=3)

    evidence_cards: list[EvidenceCard] = []
    for chunk in chunks:
        summary = _first_sentence(chunk.text)
        evidence_cards.append(
            EvidenceCard(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                team_id=team_id,
                source_id=chunk.source_id,
                chunk_id=chunk.chunk_id,
                summary=summary,
                snippet=chunk.text[:260],
                relevance_reason=(
                    f"Supports {team_name} framing for goal alignment and "
                    "implementation realism."
                ),
                used_in_round=round_number,
            )
        )

    claims = _build_claims(stance=stance, evidence_cards=evidence_cards, goal=goal)
    evidence_note = "; ".join(card.summary for card in evidence_cards[:2])
    if not evidence_note:
        evidence_note = "available session evidence is limited"

    argument = (
        f"{team_name} argues that {stance.lower()}. "
        f"In round {round_number}, this position best serves the goal by "
        f"linking practical execution with evidence: {evidence_note}"
    )
    if opponent_argument.strip():
        argument += (
            " The team responds to the opposing side by addressing their latest "
            "cost-risk concerns and proposing a controlled rollout."
        )

    citations = [
        TeamCitation(source_id=card.source_id, chunk_id=card.chunk_id)
        for card in evidence_cards
    ]
    team_turn = TeamTurnOutput(
        team_id=team_id,
        round=round_number,
        strategy_note=(
            f"Prioritize {stance.lower()} while meeting goal constraints. "
            f"Judge guidance: {judge_guidance or 'N/A'}"
        ),
        argument=argument,
        claims=claims,
        evidence_ids=[card.evidence_id for card in evidence_cards],
        citations=citations,
        self_critique=(
            "Potential weakness: assumptions may still need stronger quantified "
            "cost and timeline validation."
        ),
    )
    return team_turn, evidence_cards
