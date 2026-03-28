"""Unit tests for debate API routes."""

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from backend.api import debate as api
from backend.models.debate_session import (
    ClaimLedgerEntry,
    DebateBatchResult,
    DebateBatchStartRequest,
    DebateFinalResult,
    FinalRecommendation,
    RoundSummary,
    TeamPosition,
)


def _sample_result(session_id: str) -> DebateFinalResult:
    return DebateFinalResult(
        session_id=session_id,
        topic="topic",
        goal="goal",
        status="completed",
        rounds_completed=2,
        winner_team_id="team_a",
        final_recommendation=FinalRecommendation(
            recommended_strategy="Diversification-first",
            why="Best tradeoff",
            confidence=0.81,
        ),
        recommended_action="Start phased rollout",
        viability_score=0.81,
        consensus_rationale="Consensus converged on resilience-first.",
        pros=["Better resilience"],
        cons=["Higher complexity"],
        score_summary={},
        judge_summary="Team A wins",
        key_supporting_evidence=[],
        main_tradeoffs=[],
        main_risks=[],
        open_questions=[],
        team_positions={
            "team_a": TeamPosition(
                stance="resilience-first", final_argument_summary="..."
            ),
            "team_b": TeamPosition(stance="cost-first", final_argument_summary="..."),
        },
        round_summaries=[
            RoundSummary(
                round=1,
                winner="team_a",
                summary="Team A stronger",
                pros=["goal alignment"],
                cons=["cost detail thin"],
                judge_note="",
            )
        ],
        claim_ledger=[
            ClaimLedgerEntry(
                claim_id="c1",
                round=1,
                speaker_team_id="team_a",
                claim_text="claim",
                evidence_ids=["ev1"],
                judge_status="supported",
                judge_note="ok",
            )
        ],
    )


class DebateApiTests(unittest.IsolatedAsyncioTestCase):
    def test_request_model_requires_non_empty_singapore_info(self) -> None:
        with self.assertRaises(ValidationError):
            DebateBatchStartRequest(
                workflow_id="wf_1",
                topic="topic",
                goal="goal",
                singapore_info={},
            )

    async def test_start_route_returns_envelope(self) -> None:
        async def fake_run(body: DebateBatchStartRequest) -> DebateBatchResult:
            self.assertEqual(body.workflow_id, "wf_1")
            return DebateBatchResult(
                workflow_id="wf_1",
                input_country="Singapore",
                substitutes=["Malaysia"],
                results={"Malaysia": _sample_result("debate_1")},
                errors={},
            )

        with patch(
            "backend.api.debate.run_debate_batch_from_workflow",
            new=fake_run,
        ):
            response = await api.start_debate_batch(
                DebateBatchStartRequest(
                    workflow_id="wf_1",
                    topic="topic",
                    goal="goal",
                    singapore_info={"main_ideas": ["x"]},
                )
            )

        self.assertEqual(response["status"], "ok")
        self.assertIn("Malaysia", response["data"]["results"])

    async def test_start_route_maps_not_found(self) -> None:
        async def fake_run(body: DebateBatchStartRequest) -> DebateBatchResult:
            _ = body
            raise ValueError("Resolution workflow not found: wf_missing")

        with patch(
            "backend.api.debate.run_debate_batch_from_workflow",
            new=fake_run,
        ):
            with self.assertRaises(HTTPException) as ctx:
                await api.start_debate_batch(
                    DebateBatchStartRequest(
                        workflow_id="wf_missing",
                        topic="topic",
                        goal="goal",
                        singapore_info={"main_ideas": ["x"]},
                    )
                )

        self.assertEqual(ctx.exception.status_code, 404)
        detail = cast(dict[str, object], ctx.exception.detail)
        self.assertEqual(detail["error_code"], "WORKFLOW_NOT_FOUND")
        self.assertEqual(detail["session_id"], None)

    async def test_get_routes(self) -> None:
        with (
            patch(
                "backend.api.debate.get_debate_session",
                return_value=_sample_result("debate_1"),
            ),
            patch(
                "backend.api.debate.get_debate_rounds",
                return_value=[{"round": 1}],
            ),
            patch(
                "backend.api.debate.get_debate_claims",
                return_value=[{"claim_id": "c1"}],
            ),
        ):
            session = api.get_debate_session_result("debate_1")
            rounds = api.get_debate_session_rounds("debate_1")
            claims = api.get_debate_session_claims("debate_1")

        self.assertEqual(session["status"], "ok")
        self.assertEqual(rounds["data"][0]["round"], 1)
        self.assertEqual(claims["data"][0]["claim_id"], "c1")

    async def test_get_route_returns_structured_not_found_error(self) -> None:
        with patch(
            "backend.api.debate.get_debate_session",
            side_effect=ValueError("Debate session not found: debate_missing"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                api.get_debate_session_result("debate_missing")

        self.assertEqual(ctx.exception.status_code, 404)
        detail = cast(dict[str, object], ctx.exception.detail)
        self.assertEqual(detail["error_code"], "DEBATE_SESSION_NOT_FOUND")
        self.assertEqual(detail["session_id"], "debate_missing")


if __name__ == "__main__":
    unittest.main()
