"""Unit tests for debate batch orchestrator."""

from __future__ import annotations

import os
import tempfile
import unittest

from backend.db.models import (
    CountryPacketRecord,
    DisruptionSubstituteSnapshotRecord,
    ResolutionWorkflowRecord,
)
from backend.db.repositories import DisruptionRepository, ResolutionPrepRepository
from backend.models.debate_session import DebateBatchStartRequest
from backend.services.debate.session_orchestrator import (
    run_debate_batch_from_workflow,
    run_debate_from_country_packets,
)


class DebateOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmpdir.name, "debate.db")
        os.environ["DISRUPTION_DB_PATH"] = self._db_path

    def tearDown(self) -> None:
        os.environ.pop("DISRUPTION_DB_PATH", None)
        self._tmpdir.cleanup()

    async def test_batch_runs_and_returns_country_keyed_results(self) -> None:
        resolution_repo = ResolutionPrepRepository(self._db_path)
        disruption_repo = DisruptionRepository(self._db_path)

        workflow = resolution_repo.insert_workflow(
            ResolutionWorkflowRecord(
                workflow_id="wf_test_001",
                normalized_key="wk_1",
                event_id="evt_001",
                origin_country="Singapore",
                disrupted_supplier_country="Iran",
                resource_type="energy",
                commodity="crude_oil",
                stage="all_packets_ready",
                country_statuses={
                    "Singapore": "completed",
                    "Malaysia": "completed",
                    "Qatar": "completed",
                },
            )
        )

        resolution_repo.upsert_packet(
            CountryPacketRecord(
                workflow_id=workflow.workflow_id,
                country="Malaysia",
                status="completed",
                packet_json={
                    "country": "Malaysia",
                    "country_role": "substitute_candidate",
                    "resource_type": "energy",
                    "commodity": "crude_oil",
                    "main_ideas": ["Malaysia can increase export lanes."],
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
                            "url": "https://example.com/malaysia",
                            "content": (
                                "Malaysia can scale crude export allocation with "
                                "safeguards."
                            ),
                            "credibility": "high",
                            "date": "2026-03-28",
                        }
                    ],
                },
            )
        )
        resolution_repo.upsert_packet(
            CountryPacketRecord(
                workflow_id=workflow.workflow_id,
                country="Qatar",
                status="completed",
                packet_json={
                    "country": "Qatar",
                    "country_role": "substitute_candidate",
                    "resource_type": "energy",
                    "commodity": "crude_oil",
                    "main_ideas": ["Qatar can provide LNG-linked alternatives."],
                    "important_points": [
                        {
                            "dimension": "logistics",
                            "point": "Existing shipping routes are stable.",
                            "support": ["q1"],
                        }
                    ],
                    "sources": [
                        {
                            "id": "q1",
                            "title": "Qatar brief",
                            "url": "https://example.com/qatar",
                            "content": "Qatar offers reliable shipping schedules.",
                            "credibility": "high",
                            "date": "2026-03-28",
                        }
                    ],
                },
            )
        )

        disruption_repo.upsert_substitute_snapshot(
            DisruptionSubstituteSnapshotRecord(
                event_id="evt_001",
                resource_type="energy",
                commodity="crude_oil",
                source="live",
                candidates=[
                    {"country": "Malaysia", "score": 6},
                    {"country": "Qatar", "score": 7},
                ],
            )
        )

        request = DebateBatchStartRequest(
            workflow_id="wf_test_001",
            topic="Best substitute sourcing strategy",
            goal="Minimize disruption risk while keeping short-term costs acceptable",
            singapore_info={
                "main_ideas": ["Singapore should reduce concentration risk."],
                "important_points": [
                    {
                        "dimension": "risk",
                        "point": "Single-country dependency increases volatility.",
                        "support": ["s1"],
                    }
                ],
                "sources": [
                    {
                        "id": "s1",
                        "title": "Singapore brief",
                        "url": "https://example.com/singapore",
                        "content": (
                            "Singapore needs resilient diversified import sources."
                        ),
                        "credibility": "high",
                        "date": "2026-03-28",
                    }
                ],
                "negotiation_brief": {
                    "priorities": ["Maintain continuity", "Manage transition cost"],
                    "concession_options": ["Phased procurement commitment"],
                    "non_negotiables": ["No severe stockout risk"],
                    "counterpart_asks": ["Guaranteed minimum shipment"],
                    "deal_risks": ["Price volatility"],
                    "readiness_summary": "Ready for structured negotiation.",
                },
            },
            max_rounds=2,
            max_substitutes=2,
            max_parallel_graphs=2,
        )

        result = await run_debate_batch_from_workflow(request)

        self.assertEqual(result.workflow_id, "wf_test_001")
        self.assertEqual(result.substitutes, ["Qatar", "Malaysia"])
        self.assertIn("Qatar", result.results)
        self.assertIn("Malaysia", result.results)
        self.assertGreaterEqual(result.results["Qatar"].rounds_completed, 1)
        self.assertTrue(
            result.results["Qatar"].final_recommendation.recommended_strategy
        )

    async def test_direct_country_packet_function_runs(self) -> None:
        result = await run_debate_from_country_packets(
            topic="Direct run",
            goal="Balance resilience and cost",
            input_country="Singapore",
            substitute_country="Qatar",
            input_country_info={
                "main_ideas": ["Diversify imports for continuity."],
                "sources": [
                    {
                        "id": "s1",
                        "title": "SG note",
                        "url": "https://example.com/sg",
                        "content": "Singapore should reduce concentration risk.",
                    }
                ],
            },
            substitute_country_info={
                "main_ideas": ["Qatar can expand stable export commitments."],
                "sources": [
                    {
                        "id": "q1",
                        "title": "Qatar note",
                        "url": "https://example.com/qa",
                        "content": "Qatar can offer reliable delivery windows.",
                    }
                ],
            },
            max_rounds=2,
        )

        self.assertEqual(result.status, "completed")
        self.assertGreaterEqual(result.rounds_completed, 1)


if __name__ == "__main__":
    unittest.main()
