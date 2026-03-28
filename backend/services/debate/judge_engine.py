"""Judge scoring, claim ledger updates, and final synthesis."""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence

from backend.models.debate_session import (
    ClaimLedgerEntry,
    DebateFinalResult,
    EvidenceCard,
    FinalRecommendation,
    JudgeRoundGuidance,
    JudgeRoundOutput,
    RoundSummary,
    TeamPosition,
    TeamScore,
    TeamTurnOutput,
    UnsupportedClaim,
)
from backend.services.debate.llm_client import call_llm_json, llm_available

_SCORE_WEIGHTS = {
    "groundedness": 0.35,
    "relevance": 0.25,
    "responsiveness": 0.20,
    "strategic_strength": 0.20,
}

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _tokens(text: str) -> set[str]:
    return {token for token in _WORD_RE.findall(text.lower()) if len(token) > 2}


def _score_turn(
    *,
    turn: TeamTurnOutput,
    goal: str,
    opponent_turn: TeamTurnOutput,
) -> TeamScore:
    evidence_count = len(turn.evidence_ids)
    citation_count = len(turn.citations)
    groundedness = _clamp01(
        0.55 + (0.10 * min(evidence_count, 3)) + (0.05 * min(citation_count, 2))
    )

    goal_tokens = _tokens(goal)
    arg_tokens = _tokens(turn.argument)
    relevance_overlap = len(goal_tokens.intersection(arg_tokens))
    relevance = _clamp01(0.45 + (0.06 * min(relevance_overlap, 6)))

    opponent_tokens = _tokens(
        " ".join(opponent_turn.claims) + " " + opponent_turn.argument
    )
    response_overlap = len(opponent_tokens.intersection(arg_tokens))
    responsiveness = _clamp01(0.40 + (0.08 * min(response_overlap, 5)))

    strategy_bonus = 0.0
    lowered = turn.argument.lower()
    for keyword in ("phase", "risk", "implementation", "cost", "resilience"):
        if keyword in lowered:
            strategy_bonus += 0.04
    strategic_strength = _clamp01(
        0.52 + strategy_bonus + 0.03 * min(len(turn.claims), 3)
    )

    overall = (
        groundedness * _SCORE_WEIGHTS["groundedness"]
        + relevance * _SCORE_WEIGHTS["relevance"]
        + responsiveness * _SCORE_WEIGHTS["responsiveness"]
        + strategic_strength * _SCORE_WEIGHTS["strategic_strength"]
    )

    return TeamScore(
        groundedness=round(groundedness, 3),
        relevance=round(relevance, 3),
        responsiveness=round(responsiveness, 3),
        strategic_strength=round(strategic_strength, 3),
        overall=round(_clamp01(overall), 3),
    )


def _to_string_list(raw: object, *, max_items: int) -> list[str]:
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        return []
    items: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            continue
        clean = value.strip()
        if clean and clean not in items:
            items.append(clean)
    return items[:max_items]


def _agentic_round_overrides(
    *,
    round_number: int,
    goal: str,
    team_a_turn: TeamTurnOutput,
    team_b_turn: TeamTurnOutput,
    team_a_score: TeamScore,
    team_b_score: TeamScore,
) -> dict[str, object] | None:
    if not llm_available():
        return None

    payload = call_llm_json(
        system_prompt=(
            "You are a debate judge agent. Return strict JSON only. "
            "Ground outputs in supplied evidence and claims."
        ),
        user_prompt=(
            "Return JSON keys: round_summary, team_a_strengths, team_b_strengths, "
            "pros, cons, next_round_team_a, next_round_team_b, "
            "unsupported_claims, should_continue, stop_reason.\n"
            "unsupported_claims must be array of objects with team_id and claim_text.\n"
            f"Round: {round_number}\n"
            f"Goal: {goal}\n"
            f"Team A argument: {team_a_turn.argument}\n"
            f"Team A claims: {team_a_turn.claims}\n"
            f"Team A evidence ids: {team_a_turn.evidence_ids}\n"
            f"Team A baseline score: {team_a_score.model_dump()}\n"
            f"Team B argument: {team_b_turn.argument}\n"
            f"Team B claims: {team_b_turn.claims}\n"
            f"Team B evidence ids: {team_b_turn.evidence_ids}\n"
            f"Team B baseline score: {team_b_score.model_dump()}\n"
        ),
        temperature=0.2,
        max_tokens=850,
    )
    if not payload:
        return None
    return payload


def _agentic_final_overrides(
    *,
    topic: str,
    goal: str,
    winner_team_id: str,
    winner_stance: str,
    round_summaries: Sequence[RoundSummary],
    score_summary: Mapping[str, TeamScore],
) -> dict[str, object] | None:
    if not llm_available():
        return None
    summary_lines = [
        f"- round {row.round}, winner={row.winner}, summary={row.summary}"
        for row in round_summaries
    ]
    payload = call_llm_json(
        system_prompt=(
            "You are the final judge synthesis agent. Return strict JSON only."
        ),
        user_prompt=(
            "Return JSON keys: recommended_strategy, why, recommended_action, "
            "consensus_rationale, judge_summary, main_tradeoffs, main_risks, "
            "open_questions.\n"
            f"Topic: {topic}\n"
            f"Goal: {goal}\n"
            f"Winner team id: {winner_team_id}\n"
            f"Winner stance: {winner_stance}\n"
            f"Score summary: {dict(score_summary)}\n"
            "Round summaries:\n" + "\n".join(summary_lines)
        ),
        temperature=0.2,
        max_tokens=900,
    )
    if not payload:
        return None
    return payload


def _strengths(score: TeamScore, *, goal_focus: str) -> list[str]:
    strengths: list[str] = []
    if score.groundedness >= 0.75:
        strengths.append("Grounded claims with citation support")
    if score.relevance >= 0.75:
        strengths.append(f"Strong alignment to goal: {goal_focus}")
    if score.responsiveness >= 0.72:
        strengths.append("Responded to opposing argument directly")
    if not strengths:
        strengths.append("Maintained consistent position under constraints")
    return strengths[:2]


def _build_claim_entries(
    *,
    round_number: int,
    turn: TeamTurnOutput,
    unsupported_claim_texts: set[str],
) -> list[ClaimLedgerEntry]:
    entries: list[ClaimLedgerEntry] = []
    for claim in turn.claims:
        unsupported = claim in unsupported_claim_texts
        if unsupported:
            status = "unsupported"
            note = "Claim lacked clear direct evidence in cited snippets."
        elif len(turn.evidence_ids) <= 1:
            status = "partially_supported"
            note = "Claim has some support but needs stronger quantification."
        else:
            status = "supported"
            note = "Claim is supported by available session evidence."
        entries.append(
            ClaimLedgerEntry(
                claim_id=f"claim_{uuid.uuid4().hex[:8]}",
                round=round_number,
                speaker_team_id=turn.team_id,
                claim_text=claim,
                evidence_ids=list(turn.evidence_ids[:2]),
                judge_status=status,
                judge_note=note,
            )
        )
    return entries


def evaluate_round(
    *,
    round_number: int,
    goal: str,
    team_a_turn: TeamTurnOutput,
    team_b_turn: TeamTurnOutput,
    max_rounds: int,
    aggregated_scores: Mapping[str, Sequence[TeamScore]],
) -> tuple[JudgeRoundOutput, list[ClaimLedgerEntry], RoundSummary]:
    """Evaluate one debate round and decide whether the session should continue."""
    team_a_score = _score_turn(turn=team_a_turn, goal=goal, opponent_turn=team_b_turn)
    team_b_score = _score_turn(turn=team_b_turn, goal=goal, opponent_turn=team_a_turn)

    round_winner = team_a_turn.team_id
    if team_b_score.overall > team_a_score.overall:
        round_winner = team_b_turn.team_id

    unsupported_claims: list[UnsupportedClaim] = []
    unsupported_a: set[str] = set()
    unsupported_b: set[str] = set()
    if len(team_a_turn.evidence_ids) == 0:
        for claim in team_a_turn.claims:
            unsupported_a.add(claim)
            unsupported_claims.append(
                UnsupportedClaim(team_id=team_a_turn.team_id, claim_text=claim)
            )
    if len(team_b_turn.evidence_ids) == 0:
        for claim in team_b_turn.claims:
            unsupported_b.add(claim)
            unsupported_claims.append(
                UnsupportedClaim(team_id=team_b_turn.team_id, claim_text=claim)
            )

    team_a_strengths = _strengths(team_a_score, goal_focus=goal)
    team_b_strengths = _strengths(team_b_score, goal_focus=goal)

    pros = [
        f"{round_winner} presented stronger goal-aligned reasoning this round.",
        "Both teams surfaced practical constraints for implementation.",
    ]
    cons = [
        "Some cost or timeline assumptions remain weakly quantified.",
        "Further evidence could improve confidence on execution risk.",
    ]

    score_delta = abs(team_a_score.overall - team_b_score.overall)
    prior_scores_count = sum(len(values) for values in aggregated_scores.values())
    if round_number >= max_rounds:
        should_continue = False
        stop_reason = "max_rounds_reached"
    elif score_delta >= 0.16 and round_number >= 2:
        should_continue = False
        stop_reason = "clear_lead_established"
    elif prior_scores_count >= 4 and score_delta <= 0.03:
        should_continue = False
        stop_reason = "position_convergence"
    else:
        should_continue = True
        stop_reason = None

    round_summary_text = (
        f"Round {round_number} favored {round_winner} on weighted scoring. "
        "Groundedness and goal relevance remained the primary differentiators."
    )
    guidance = JudgeRoundGuidance(
        team_a="Address quantification gaps and tighten execution steps.",
        team_b="Strengthen evidence support and rebut resilience concerns directly.",
    )

    agentic = _agentic_round_overrides(
        round_number=round_number,
        goal=goal,
        team_a_turn=team_a_turn,
        team_b_turn=team_b_turn,
        team_a_score=team_a_score,
        team_b_score=team_b_score,
    )
    if agentic is not None:
        maybe_summary = str(agentic.get("round_summary", "")).strip()
        if maybe_summary:
            round_summary_text = maybe_summary
        parsed_a_strengths = _to_string_list(
            agentic.get("team_a_strengths", []), max_items=3
        )
        parsed_b_strengths = _to_string_list(
            agentic.get("team_b_strengths", []), max_items=3
        )
        parsed_pros = _to_string_list(agentic.get("pros", []), max_items=4)
        parsed_cons = _to_string_list(agentic.get("cons", []), max_items=4)
        if parsed_a_strengths:
            team_a_strengths = parsed_a_strengths
        if parsed_b_strengths:
            team_b_strengths = parsed_b_strengths
        if parsed_pros:
            pros = parsed_pros
        if parsed_cons:
            cons = parsed_cons
        next_round_a = str(agentic.get("next_round_team_a", "")).strip()
        next_round_b = str(agentic.get("next_round_team_b", "")).strip()
        guidance = JudgeRoundGuidance(
            team_a=next_round_a or guidance.team_a,
            team_b=next_round_b or guidance.team_b,
        )
        raw_continue = agentic.get("should_continue")
        if isinstance(raw_continue, bool):
            should_continue = raw_continue
            stop_reason = (
                None
                if should_continue
                else (str(agentic.get("stop_reason", "")).strip() or "judge_stop")
            )
        raw_unsupported = agentic.get("unsupported_claims", [])
        parsed_unsupported: list[UnsupportedClaim] = []
        if isinstance(raw_unsupported, Sequence) and not isinstance(
            raw_unsupported, str | bytes | bytearray
        ):
            for row in raw_unsupported:
                if not isinstance(row, Mapping):
                    continue
                team = str(row.get("team_id", "")).strip()
                claim = str(row.get("claim_text", "")).strip()
                if team and claim:
                    parsed_unsupported.append(
                        UnsupportedClaim(team_id=team, claim_text=claim)
                    )
        if parsed_unsupported:
            unsupported_claims = parsed_unsupported
            unsupported_a = {
                row.claim_text
                for row in parsed_unsupported
                if row.team_id == team_a_turn.team_id
            }
            unsupported_b = {
                row.claim_text
                for row in parsed_unsupported
                if row.team_id == team_b_turn.team_id
            }
    round_output = JudgeRoundOutput(
        round=round_number,
        team_a_score=team_a_score,
        team_b_score=team_b_score,
        round_winner=round_winner,
        team_a_strengths=team_a_strengths,
        team_b_strengths=team_b_strengths,
        unsupported_claims=unsupported_claims,
        pros=pros,
        cons=cons,
        round_summary=round_summary_text,
        next_round_guidance=guidance,
        should_continue=should_continue,
        stop_reason=stop_reason,
    )

    claim_entries = _build_claim_entries(
        round_number=round_number,
        turn=team_a_turn,
        unsupported_claim_texts=unsupported_a,
    )
    claim_entries.extend(
        _build_claim_entries(
            round_number=round_number,
            turn=team_b_turn,
            unsupported_claim_texts=unsupported_b,
        )
    )

    round_summary = RoundSummary(
        round=round_number,
        winner=round_winner,
        summary=round_summary_text,
        pros=pros,
        cons=cons,
        judge_note="Judge score weights favored groundedness and relevance.",
    )
    return round_output, claim_entries, round_summary


def synthesize_final_result(
    *,
    session_id: str,
    topic: str,
    goal: str,
    team_stances: Mapping[str, str],
    team_turns: Sequence[TeamTurnOutput],
    judge_rounds: Sequence[JudgeRoundOutput],
    round_summaries: Sequence[RoundSummary],
    claim_ledger: Sequence[ClaimLedgerEntry],
    evidence_cards: Sequence[EvidenceCard],
    status: str = "completed",
) -> DebateFinalResult:
    """Create final frontend-ready payload from structured round artifacts."""
    score_buckets: dict[str, list[TeamScore]] = defaultdict(list)
    for row in judge_rounds:
        score_buckets["team_a"].append(row.team_a_score)
        score_buckets["team_b"].append(row.team_b_score)

    score_summary: dict[str, TeamScore] = {}
    for team_id, values in score_buckets.items():
        if not values:
            continue
        count = float(len(values))
        score_summary[team_id] = TeamScore(
            groundedness=round(sum(v.groundedness for v in values) / count, 3),
            relevance=round(sum(v.relevance for v in values) / count, 3),
            responsiveness=round(sum(v.responsiveness for v in values) / count, 3),
            strategic_strength=round(
                sum(v.strategic_strength for v in values) / count, 3
            ),
            overall=round(sum(v.overall for v in values) / count, 3),
        )

    zero_score = TeamScore(
        groundedness=0.0,
        relevance=0.0,
        responsiveness=0.0,
        strategic_strength=0.0,
        overall=0.0,
    )
    winner_team_id = "team_a"
    if (
        score_summary.get("team_b")
        and score_summary["team_b"].overall
        > score_summary.get("team_a", zero_score).overall
    ):
        winner_team_id = "team_b"

    winner_stance = team_stances.get(winner_team_id, "balanced strategy")
    winner_score = score_summary.get(
        winner_team_id,
        TeamScore(
            groundedness=0.6,
            relevance=0.6,
            responsiveness=0.6,
            strategic_strength=0.6,
            overall=0.6,
        ),
    )
    confidence = _clamp01(0.45 + (winner_score.overall * 0.5))

    recommendation = FinalRecommendation(
        recommended_strategy=(
            f"Adopt a {winner_stance.lower()} plan with phased safeguards and "
            "active monitoring."
        ),
        why=(
            "This strategy performed best against weighted criteria for "
            "groundedness, relevance, responsiveness, and strategic utility."
        ),
        confidence=round(confidence, 3),
    )

    final_arguments: dict[str, str] = {}
    for turn in team_turns:
        final_arguments[turn.team_id] = turn.argument

    supporting: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    for card in evidence_cards:
        if card.source_id in seen_sources:
            continue
        supporting.append(
            {
                "source_id": card.source_id,
                "reason": card.relevance_reason,
            }
        )
        seen_sources.add(card.source_id)
        if len(supporting) >= 4:
            break

    pros: list[str] = []
    cons: list[str] = []
    for row in round_summaries:
        for value in row.pros:
            if value not in pros:
                pros.append(value)
        for value in row.cons:
            if value not in cons:
                cons.append(value)

    recommended_action = (
        "Proceed with a phased implementation plan and validate early-stage "
        "operational constraints before scaling."
    )
    consensus_rationale = (
        "Across rounds, the winning strategy better balanced the objective "
        "trade-off while retaining stronger evidence grounding."
    )
    judge_summary = (
        f"{winner_team_id} achieved the highest weighted score with clearer "
        "decision usefulness for the stated goal."
    )
    main_tradeoffs = [
        "Resilience improvements may add short-term operational overhead.",
        "Cost control needs phased rollout discipline.",
    ]
    main_risks = [
        "Transition timelines may be underestimated.",
        "Evidence may not fully capture fast-changing market shocks.",
    ]
    open_questions = [
        "What is the quantified short-term cost delta for implementation?",
        "Which trigger should activate fallback sourcing immediately?",
    ]

    agentic_final = _agentic_final_overrides(
        topic=topic,
        goal=goal,
        winner_team_id=winner_team_id,
        winner_stance=winner_stance,
        round_summaries=round_summaries,
        score_summary=score_summary,
    )
    if agentic_final is not None:
        maybe_strategy = str(agentic_final.get("recommended_strategy", "")).strip()
        maybe_why = str(agentic_final.get("why", "")).strip()
        if maybe_strategy:
            recommendation.recommended_strategy = maybe_strategy
        if maybe_why:
            recommendation.why = maybe_why

        maybe_action = str(agentic_final.get("recommended_action", "")).strip()
        if maybe_action:
            recommended_action = maybe_action

        maybe_consensus = str(agentic_final.get("consensus_rationale", "")).strip()
        if maybe_consensus:
            consensus_rationale = maybe_consensus

        maybe_judge_summary = str(agentic_final.get("judge_summary", "")).strip()
        if maybe_judge_summary:
            judge_summary = maybe_judge_summary

        parsed_tradeoffs = _to_string_list(
            agentic_final.get("main_tradeoffs", []), max_items=4
        )
        parsed_risks = _to_string_list(agentic_final.get("main_risks", []), max_items=4)
        parsed_open = _to_string_list(
            agentic_final.get("open_questions", []), max_items=5
        )
        if parsed_tradeoffs:
            main_tradeoffs = parsed_tradeoffs
        if parsed_risks:
            main_risks = parsed_risks
        if parsed_open:
            open_questions = parsed_open

    return DebateFinalResult(
        session_id=session_id,
        topic=topic,
        goal=goal,
        status="fallback" if status == "fallback" else "completed",
        rounds_completed=len(judge_rounds),
        winner_team_id=winner_team_id,
        final_recommendation=recommendation,
        recommended_action=recommended_action,
        viability_score=round(confidence, 3),
        consensus_rationale=consensus_rationale,
        pros=pros[:6],
        cons=cons[:6],
        score_summary=score_summary,
        judge_summary=judge_summary,
        key_supporting_evidence=supporting,
        main_tradeoffs=main_tradeoffs,
        main_risks=main_risks,
        open_questions=open_questions,
        team_positions={
            "team_a": TeamPosition(
                stance=team_stances.get("team_a", ""),
                final_argument_summary=final_arguments.get("team_a", ""),
            ),
            "team_b": TeamPosition(
                stance=team_stances.get("team_b", ""),
                final_argument_summary=final_arguments.get("team_b", ""),
            ),
        },
        round_summaries=list(round_summaries),
        claim_ledger=list(claim_ledger),
    )


def build_fallback_result(
    *,
    session_id: str,
    topic: str,
    goal: str,
    fallback_country: str,
) -> DebateFinalResult:
    """Create a mock fallback when one country-specific graph fails."""
    return DebateFinalResult(
        session_id=session_id,
        topic=topic,
        goal=goal,
        status="fallback",
        rounds_completed=0,
        winner_team_id="team_a",
        final_recommendation=FinalRecommendation(
            recommended_strategy=(
                "Use a cautious phased substitute plan while collecting additional "
                f"evidence for {fallback_country}."
            ),
            why="Country-specific debate graph failed and fallback mode was activated.",
            confidence=0.45,
        ),
        recommended_action=(
            "Run one additional evidence refresh pass before final procurement "
            "commitment."
        ),
        viability_score=0.45,
        consensus_rationale=(
            "Fallback output is intentionally conservative due to incomplete round "
            "evaluation."
        ),
        pros=["Maintains continuity with a conservative interim decision."],
        cons=["Debate evidence quality is lower in fallback mode."],
        score_summary={},
        judge_summary="Fallback result generated because graph execution failed.",
        key_supporting_evidence=[],
        main_tradeoffs=["Speed versus evidence completeness."],
        main_risks=["Decision confidence is reduced."],
        open_questions=["Which additional sources are required for full confidence?"],
        team_positions={
            "team_a": TeamPosition(
                stance="resilience-first", final_argument_summary=""
            ),
            "team_b": TeamPosition(stance="cost-first", final_argument_summary=""),
        },
        round_summaries=[],
        claim_ledger=[],
    )
