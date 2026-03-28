"""LangGraph orchestration for one country-pair debate session."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.debate.judge_nodes import judge_round_node as run_judge_round_node
from backend.agents.debate.state import DebateGraphState
from backend.agents.debate.team_subgraph import run_team_turn_subgraph
from backend.services.debate.agentic_ingestion import enhance_sources_for_rag
from backend.services.debate.chunking import chunk_sources
from backend.services.debate.judge_engine import synthesize_final_result
from backend.services.debate.retrieval import build_neutral_pool, build_team_retrievers
from backend.services.debate.source_processor import build_source_records


class GraphEnvelope(TypedDict):
    state: DebateGraphState


class DebateSessionGraph:
    """Deterministic LangGraph with explicit agentic nodes per debate stage."""

    def __init__(
        self,
        *,
        session_id: str,
        topic: str,
        goal: str,
        input_country: str,
        substitute_country: str,
        input_country_info: Mapping[str, object],
        substitute_country_info: Mapping[str, object],
        max_rounds: int,
        team_a_stance: str,
        team_b_stance: str,
    ) -> None:
        self._input_country_info = input_country_info
        self._substitute_country_info = substitute_country_info
        self.state = DebateGraphState(
            session_id=session_id,
            topic=topic,
            goal=goal,
            max_rounds=max_rounds,
            input_country=input_country,
            substitute_country=substitute_country,
            team_a_stance=team_a_stance,
            team_b_stance=team_b_stance,
        )

    def _setup_session_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        singapore_sources = build_source_records(
            country=graph_state.input_country,
            team_role="origin",
            info=self._input_country_info,
        )
        substitute_sources = build_source_records(
            country=graph_state.substitute_country,
            team_role="substitute_candidate",
            info=self._substitute_country_info,
        )
        source_records = enhance_sources_for_rag(singapore_sources + substitute_sources)
        chunk_records = chunk_sources(source_records)

        graph_state.source_records = source_records
        graph_state.chunk_records = chunk_records
        graph_state.neutral_evidence_pool = build_neutral_pool(chunk_records)
        graph_state.team_retrievers = build_team_retrievers(
            chunks=chunk_records,
            team_ids=("team_a", "team_b"),
        )
        graph_state.team_rag_handles = {
            "team_a": f"{graph_state.session_id}:team_a",
            "team_b": f"{graph_state.session_id}:team_b",
        }
        return {"state": graph_state}

    def _plan_debate_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        graph_state.judge_guidance_by_team["team_a"] = (
            "Prioritize resilient continuity and explicit rollout safeguards."
        )
        graph_state.judge_guidance_by_team["team_b"] = (
            "Prioritize profitable export terms with explicit domestic-risk controls."
        )
        return {"state": graph_state}

    def _advance_round_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        graph_state.current_round += 1
        return {"state": graph_state}

    def _team_a_turn_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        turn, evidence = run_team_turn_subgraph(
            team_id="team_a",
            team_name=graph_state.input_country,
            stance=graph_state.team_a_stance,
            topic=graph_state.topic,
            goal=graph_state.goal,
            round_number=graph_state.current_round,
            retriever=graph_state.team_retrievers["team_a"],
            judge_guidance=graph_state.judge_guidance_by_team["team_a"],
            opponent_argument=graph_state.last_opponent_argument_by_team["team_a"],
        )
        graph_state.team_turns.append(turn)
        graph_state.evidence_cards.extend(evidence)
        for card in evidence:
            if card.evidence_id not in graph_state.used_evidence_by_team["team_a"]:
                graph_state.used_evidence_by_team["team_a"].append(card.evidence_id)
        return {"state": graph_state}

    def _team_b_turn_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        team_a_turn = graph_state.team_turns[-1]
        turn, evidence = run_team_turn_subgraph(
            team_id="team_b",
            team_name=graph_state.substitute_country,
            stance=graph_state.team_b_stance,
            topic=graph_state.topic,
            goal=graph_state.goal,
            round_number=graph_state.current_round,
            retriever=graph_state.team_retrievers["team_b"],
            judge_guidance=graph_state.judge_guidance_by_team["team_b"],
            opponent_argument=team_a_turn.argument,
        )
        graph_state.team_turns.append(turn)
        graph_state.evidence_cards.extend(evidence)
        for card in evidence:
            if card.evidence_id not in graph_state.used_evidence_by_team["team_b"]:
                graph_state.used_evidence_by_team["team_b"].append(card.evidence_id)

        graph_state.last_opponent_argument_by_team["team_a"] = turn.argument
        graph_state.last_opponent_argument_by_team["team_b"] = team_a_turn.argument
        return {"state": graph_state}

    def _judge_round_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        team_b_turn = graph_state.team_turns[-1]
        team_a_turn = graph_state.team_turns[-2]
        run_judge_round_node(
            state=graph_state,
            team_a_turn=team_a_turn,
            team_b_turn=team_b_turn,
        )
        return {"state": graph_state}

    def _continue_router(self, state: GraphEnvelope) -> str:
        graph_state = state["state"]
        if not graph_state.judge_rounds:
            return "advance_round"
        latest = graph_state.judge_rounds[-1]
        if graph_state.current_round >= graph_state.max_rounds:
            return "final_verdict"
        if not latest.should_continue:
            return "final_verdict"
        return "advance_round"

    def _final_verdict_node(self, state: GraphEnvelope) -> GraphEnvelope:
        graph_state = state["state"]
        result = synthesize_final_result(
            session_id=graph_state.session_id,
            topic=graph_state.topic,
            goal=graph_state.goal,
            team_stances={
                "team_a": graph_state.team_a_stance,
                "team_b": graph_state.team_b_stance,
            },
            team_turns=graph_state.team_turns,
            judge_rounds=graph_state.judge_rounds,
            round_summaries=graph_state.round_summaries,
            claim_ledger=graph_state.claim_ledger,
            evidence_cards=graph_state.evidence_cards,
            status="completed",
        )
        graph_state.score_summary = dict(result.score_summary)
        graph_state.consensus_rationale = result.consensus_rationale
        graph_state.viability_score = result.viability_score
        graph_state.recommended_action = result.recommended_action
        graph_state.final_result = result
        graph_state.status = result.status
        return {"state": graph_state}

    def run(self) -> DebateGraphState:
        """Run session graph: setup -> plan -> rounds -> final verdict."""
        workflow = StateGraph(GraphEnvelope)
        workflow.add_node("setup_session", self._setup_session_node)
        workflow.add_node("plan_debate", self._plan_debate_node)
        workflow.add_node("advance_round", self._advance_round_node)
        workflow.add_node("team_a_turn", self._team_a_turn_node)
        workflow.add_node("team_b_turn", self._team_b_turn_node)
        workflow.add_node("judge_round", self._judge_round_node)
        workflow.add_node("final_verdict", self._final_verdict_node)

        workflow.add_edge(START, "setup_session")
        workflow.add_edge("setup_session", "plan_debate")
        workflow.add_edge("plan_debate", "advance_round")
        workflow.add_edge("advance_round", "team_a_turn")
        workflow.add_edge("team_a_turn", "team_b_turn")
        workflow.add_edge("team_b_turn", "judge_round")
        workflow.add_conditional_edges(
            "judge_round",
            self._continue_router,
            {
                "advance_round": "advance_round",
                "final_verdict": "final_verdict",
            },
        )
        workflow.add_edge("final_verdict", END)

        app = workflow.compile()
        result = app.invoke({"state": self.state}, config={"recursion_limit": 64})
        return result["state"]


async def run_debate_from_country_packets(
    *,
    session_id: str,
    topic: str,
    goal: str,
    input_country: str,
    substitute_country: str,
    input_country_info: Mapping[str, object],
    substitute_country_info: Mapping[str, object],
    max_rounds: int,
    team_a_stance: str,
    team_b_stance: str,
) -> DebateGraphState:
    """Async wrapper for one country-pair LangGraph run."""
    graph = DebateSessionGraph(
        session_id=session_id,
        topic=topic,
        goal=goal,
        input_country=input_country,
        substitute_country=substitute_country,
        input_country_info=input_country_info,
        substitute_country_info=substitute_country_info,
        max_rounds=max_rounds,
        team_a_stance=team_a_stance,
        team_b_stance=team_b_stance,
    )
    return graph.run()
