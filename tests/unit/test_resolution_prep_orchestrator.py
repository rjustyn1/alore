"""Unit tests for resolution-prep orchestration."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from backend.models.country_packet import (
    CountryPacket,
    CountryPacketPoint,
    CountryPacketSource,
)
from backend.models.resolution_workflow import ResolutionPrepStartRequest
from backend.services import disruption_monitor_service
from backend.services.resolution_prep_manager import CountryCurationContext
from backend.services.resolution_prep_orchestrator import (
    get_resolution_prep_status,
    start_resolution_prep,
)


class ResolutionPrepOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmpdir.name, "resolution.db")
        os.environ["DISRUPTION_DB_PATH"] = self._db_path

    def tearDown(self) -> None:
        os.environ.pop("DISRUPTION_DB_PATH", None)
        self._tmpdir.cleanup()

    async def test_start_and_reuse_workflow(self) -> None:
        async def fake_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-1",
                    "url": "https://example.com/d1",
                    "title": "Iran oil shipment delay causes supply constraint",
                    "content": "Delay in crude oil cargoes increases supply pressure.",
                    "collected_at": "2026-03-27T00:00:00Z",
                }
            ]

        with patch(
            "backend.services.disruption_monitor_service._collect_documents",
            new=fake_collect,
        ):
            run_result = await disruption_monitor_service.run_monitor_once(
                trigger="manual"
            )
        self.assertEqual(run_result.status, "completed")
        event_id = run_result.emitted_events[0].event_id
        commodity = run_result.emitted_events[0].commodity

        request = ResolutionPrepStartRequest(
            event_id=event_id,
            resource_type="energy",
            commodity=commodity,
            max_substitutes=2,
        )

        origin_context = CountryCurationContext(
            country="Singapore",
            country_role="origin",
            country_objective="maximize supply resilience for Singapore",
            resource_type="energy",
            commodity=commodity,
            disruption_context={
                "event_id": event_id,
                "from_country": "Iran",
                "severity": "CONSTRAINED",
                "headline": "Iran oil shipment delay causes supply constraint",
            },
            dimensions=[
                "supply_capacity",
                "trade_relevance",
                "cost",
                "logistics",
                "risk",
                "sustainability",
            ],
            must_find=["capacity"],
            stop_condition="all dimensions have sufficient source-backed points",
        )
        origin_packet = CountryPacket(
            country="Singapore",
            country_role="origin",
            resource_type="energy",
            commodity=commodity,
            main_ideas=["Singapore should diversify near-term imports."],
            important_points=[
                CountryPacketPoint(
                    dimension="supply_capacity",
                    point="Alternative capacity exists among regional exporters.",
                    support=["source_1"],
                ),
                CountryPacketPoint(
                    dimension="trade_relevance",
                    point="Existing contracts can be expanded quickly.",
                    support=["source_1"],
                ),
                CountryPacketPoint(
                    dimension="cost",
                    point="Spot price premium is manageable short-term.",
                    support=["source_1"],
                ),
                CountryPacketPoint(
                    dimension="logistics",
                    point="Route time remains feasible from substitutes.",
                    support=["source_1"],
                ),
                CountryPacketPoint(
                    dimension="risk",
                    point="Diversification lowers concentration risk.",
                    support=["source_1"],
                ),
                CountryPacketPoint(
                    dimension="sustainability",
                    point="Carbon impact is neutral versus baseline.",
                    support=["source_1"],
                ),
            ],
            sources=[
                CountryPacketSource(
                    id="source_1",
                    title="Test source",
                    url="https://example.com/source",
                    credibility="high",
                    date="2026-03-28",
                )
            ],
            source_mode="live",
        )

        with (
            patch(
                "backend.services.resolution_prep_orchestrator._select_substitute_snapshot",
                return_value=("energy", commodity, []),
            ),
            patch(
                "backend.services.resolution_prep_orchestrator.build_country_contexts",
                return_value=[origin_context],
            ),
            patch(
                "backend.services.resolution_prep_orchestrator.curate_country_packet",
                new=AsyncMock(return_value=origin_packet),
            ),
        ):
            first = await start_resolution_prep(request)
            second = await start_resolution_prep(request)

        self.assertFalse(first.reused_workflow)
        origin_packet = first.origin_packet
        self.assertIsNotNone(origin_packet)
        if origin_packet is None:
            self.fail("origin packet should not be None")
        self.assertEqual(origin_packet.country, "Singapore")
        self.assertTrue(second.reused_workflow)
        self.assertEqual(first.workflow_id, second.workflow_id)

        status = get_resolution_prep_status(first.workflow_id)
        self.assertEqual(status.workflow_id, first.workflow_id)
        self.assertIn("Singapore", status.country_statuses)
        self.assertIn("Singapore", status.packets)


if __name__ == "__main__":
    unittest.main()
