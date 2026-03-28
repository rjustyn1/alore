"""Judge path nodes for debate graph rounds."""

from __future__ import annotations

from backend.agents.debate.state import DebateGraphState
from backend.models.debate_session import TeamTurnOutput
from backend.services.debate.judge_engine import evaluate_round


def judge_round_node(
    *,
    state: DebateGraphState,
    team_a_turn: TeamTurnOutput,
    team_b_turn: TeamTurnOutput,
) -> None:
    """Evaluate one round and apply state updates."""
    judge_round, round_claims, round_summary = evaluate_round(
        round_number=state.current_round,
        goal=state.goal,
        team_a_turn=team_a_turn,
        team_b_turn=team_b_turn,
        max_rounds=state.max_rounds,
        aggregated_scores=state.score_history,
    )

    state.judge_rounds.append(judge_round)
    state.claim_ledger.extend(round_claims)
    state.round_summaries.append(round_summary)
    state.score_history["team_a"].append(judge_round.team_a_score)
    state.score_history["team_b"].append(judge_round.team_b_score)

    state.judge_guidance_by_team["team_a"] = judge_round.next_round_guidance.team_a
    state.judge_guidance_by_team["team_b"] = judge_round.next_round_guidance.team_b

    for value in round_summary.pros:
        if value not in state.aggregated_pros:
            state.aggregated_pros.append(value)
    for value in round_summary.cons:
        if value not in state.aggregated_cons:
            state.aggregated_cons.append(value)
