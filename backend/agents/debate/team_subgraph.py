"""Team subgraph nodes for one debate turn."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from backend.models.debate_session import (
    EvidenceCard,
    TeamCitation,
    TeamTurnOutput,
)
from backend.services.debate.llm_client import call_llm_json, llm_available
from backend.services.debate.retrieval import TeamRetriever


def refresh_strategy(
    *,
    stance: str,
    goal: str,
    judge_guidance: str,
) -> str:
    """Produce current strategy note for this turn."""
    return (
        f"Optimize for: {stance}. Goal constraint: {goal}. "
        f"Judge guidance: {judge_guidance or 'N/A'}."
    )


def retrieve_evidence(
    *,
    team_id: str,
    team_name: str,
    round_number: int,
    retriever: TeamRetriever,
    query: str,
) -> list[EvidenceCard]:
    """Retrieve top evidence cards for this turn."""
    chunks = retriever.retrieve(query=query, top_k=3)
    cards: list[EvidenceCard] = []
    for chunk in chunks:
        snippet = chunk.text[:260]
        summary = snippet
        for delimiter in (". ", "? ", "! "):
            if delimiter in snippet:
                summary = snippet.split(delimiter, 1)[0].strip() + "."
                break
        cards.append(
            EvidenceCard(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                team_id=team_id,
                source_id=chunk.source_id,
                chunk_id=chunk.chunk_id,
                summary=summary,
                snippet=snippet,
                relevance_reason=(
                    f"Supports {team_name} position under current goal constraints."
                ),
                used_in_round=round_number,
            )
        )
    return cards


def draft_argument(
    *,
    team_name: str,
    stance: str,
    goal: str,
    round_number: int,
    evidence_cards: Sequence[EvidenceCard],
    opponent_argument: str,
) -> tuple[str, list[str]]:
    """Draft argument and candidate claims from retrieved evidence."""
    claims: list[str] = [card.summary for card in evidence_cards[:2] if card.summary]
    if not claims:
        claims.append(f"{stance} remains a viable strategy for goal: {goal.lower()}.")
    claims.append(
        "Implementation should use phased safeguards and measurable triggers."
    )
    claims = list(dict.fromkeys(claims))[:3]

    evidence_note = "; ".join(claims[:2]) or "available evidence is limited"
    argument = (
        f"{team_name} argues for {stance.lower()} in round {round_number}. "
        f"This best satisfies the goal based on evidence: {evidence_note}"
    )
    if opponent_argument.strip():
        argument += (
            " The team addresses the opponent's strongest point and provides a "
            "controlled mitigation path."
        )
    return argument, claims


def self_critique(
    *,
    claims: Sequence[str],
) -> str:
    """Create bounded self-critique statement."""
    if not claims:
        return "Potential weakness: evidence base is thin and needs verification."
    return (
        "Potential weakness: current claims still need stronger quantified cost and "
        "timeline support."
    )


def _agentic_team_response(
    *,
    team_name: str,
    team_id: str,
    stance: str,
    goal: str,
    round_number: int,
    strategy_note: str,
    evidence_cards: Sequence[EvidenceCard],
    opponent_argument: str,
) -> tuple[str, list[str], str, str] | None:
    if not llm_available():
        return None

    evidence_lines: list[str] = []
    for card in evidence_cards:
        evidence_lines.append(
            f"- {card.evidence_id} | {card.source_id} | {card.summary} | {card.snippet}"
        )
    evidence_text = "\n".join(evidence_lines) or "- none"

    payload = call_llm_json(
        system_prompt=(
            "You are a debate team agent. Produce concise, grounded, "
            "decision-useful JSON only."
        ),
        user_prompt=(
            "Return JSON keys: strategy_note, argument, claims, self_critique.\n"
            "claims must be a short array (1-4 entries).\n"
            f"Team name: {team_name}\n"
            f"Team id: {team_id}\n"
            f"Stance: {stance}\n"
            f"Goal: {goal}\n"
            f"Round: {round_number}\n"
            f"Current strategy note: {strategy_note}\n"
            f"Opponent argument: {opponent_argument}\n"
            "Evidence cards:\n"
            f"{evidence_text}"
        ),
        temperature=0.3,
        max_tokens=700,
    )
    if not payload:
        return None

    llm_strategy_note = str(payload.get("strategy_note", "")).strip() or strategy_note
    llm_argument = str(payload.get("argument", "")).strip()
    raw_claims = payload.get("claims", [])
    llm_claims: list[str] = []
    if isinstance(raw_claims, Sequence) and not isinstance(
        raw_claims, str | bytes | bytearray
    ):
        for row in raw_claims:
            if not isinstance(row, str):
                continue
            clean = row.strip()
            if clean and clean not in llm_claims:
                llm_claims.append(clean)
    llm_claims = llm_claims[:4]
    llm_critique = str(payload.get("self_critique", "")).strip()

    if not llm_argument:
        return None
    if not llm_claims:
        llm_claims = ["Evidence-backed position remains viable for this round."]
    if not llm_critique:
        llm_critique = (
            "Potential weakness: key assumptions still require stronger quantification."
        )
    return llm_strategy_note, llm_claims, llm_argument, llm_critique


def finalize_argument(
    *,
    team_id: str,
    round_number: int,
    strategy_note: str,
    argument: str,
    claims: Sequence[str],
    evidence_cards: Sequence[EvidenceCard],
    critique: str,
) -> TeamTurnOutput:
    """Build canonical TeamTurnOutput payload."""
    citations = [
        TeamCitation(source_id=card.source_id, chunk_id=card.chunk_id)
        for card in evidence_cards
    ]
    return TeamTurnOutput(
        team_id=team_id,
        round=round_number,
        strategy_note=strategy_note,
        argument=argument,
        claims=list(claims),
        evidence_ids=[card.evidence_id for card in evidence_cards],
        citations=citations,
        self_critique=critique,
    )


def run_team_turn_subgraph(
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
    """Run full team subgraph: refresh -> retrieve -> draft -> critique -> finalize."""
    strategy_note = refresh_strategy(
        stance=stance,
        goal=goal,
        judge_guidance=judge_guidance,
    )
    query = " ".join(
        token
        for token in (topic, goal, stance, judge_guidance, opponent_argument)
        if token.strip()
    )
    evidence_cards = retrieve_evidence(
        team_id=team_id,
        team_name=team_name,
        round_number=round_number,
        retriever=retriever,
        query=query,
    )
    argument, claims = draft_argument(
        team_name=team_name,
        stance=stance,
        goal=goal,
        round_number=round_number,
        evidence_cards=evidence_cards,
        opponent_argument=opponent_argument,
    )
    critique = self_critique(claims=claims)

    agentic = _agentic_team_response(
        team_name=team_name,
        team_id=team_id,
        stance=stance,
        goal=goal,
        round_number=round_number,
        strategy_note=strategy_note,
        evidence_cards=evidence_cards,
        opponent_argument=opponent_argument,
    )
    if agentic is not None:
        strategy_note, claims, argument, critique = agentic

    output = finalize_argument(
        team_id=team_id,
        round_number=round_number,
        strategy_note=strategy_note,
        argument=argument,
        claims=claims,
        evidence_cards=evidence_cards,
        critique=critique,
    )
    return output, evidence_cards
