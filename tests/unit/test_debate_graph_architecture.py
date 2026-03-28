"""Unit tests for debate agent graph architecture."""

from __future__ import annotations

import unittest

from backend.agents.debate.graph import run_debate_from_country_packets


class DebateGraphArchitectureTests(unittest.IsolatedAsyncioTestCase):
    async def test_parent_graph_runs_and_updates_structured_state(self) -> None:
        state = await run_debate_from_country_packets(
            session_id="debate_test_graph_1",
            topic="Best substitute strategy",
            goal="Minimize disruption risk while keeping costs acceptable",
            input_country="Singapore",
            substitute_country="Malaysia",
            input_country_info={
                "main_ideas": ["Diversification improves resilience."],
                "important_points": [
                    {
                        "dimension": "risk",
                        "point": "Concentration risk is high.",
                        "support": ["s1"],
                    }
                ],
                "sources": [
                    {
                        "id": "s1",
                        "title": "Singapore brief",
                        "url": "https://example.com/sg",
                        "content": "Singapore should diversify import sources.",
                    }
                ],
            },
            substitute_country_info={
                "main_ideas": ["Malaysia can increase export allocation."],
                "important_points": [
                    {
                        "dimension": "supply_capacity",
                        "point": "Export headroom exists.",
                        "support": ["m1"],
                    }
                ],
                "sources": [
                    {
                        "id": "m1",
                        "title": "Malaysia brief",
                        "url": "https://example.com/my",
                        "content": "Malaysia has stable shipping routes.",
                    }
                ],
            },
            max_rounds=2,
            team_a_stance="resilience-first",
            team_b_stance="cost-first with safeguards",
        )

        self.assertEqual(state.status, "completed")
        self.assertIsNotNone(state.final_result)
        self.assertEqual(set(state.team_rag_handles.keys()), {"team_a", "team_b"})
        self.assertGreaterEqual(len(state.neutral_evidence_pool), 1)
        self.assertGreaterEqual(len(state.judge_rounds), 1)
        self.assertEqual(len(state.round_summaries), len(state.judge_rounds))
        self.assertGreaterEqual(len(state.claim_ledger), 1)


if __name__ == "__main__":
    unittest.main()
