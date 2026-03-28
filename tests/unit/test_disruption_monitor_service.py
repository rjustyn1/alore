"""Unit tests for disruption monitor service behaviors."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from backend.db.repositories import DisruptionRepository
from backend.services import disruption_monitor_service as service
from backend.utils.substitute_finder import (
    CommoditySubstituteResult,
    SubstituteCountry,
    SubstituteFinderResult,
)


class DisruptionMonitorServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmpdir.name, "disruptions.db")
        os.environ["DISRUPTION_DB_PATH"] = self._db_path

    def tearDown(self) -> None:
        os.environ.pop("DISRUPTION_DB_PATH", None)
        self._tmpdir.cleanup()

    async def test_creates_new_event_and_run_record(self) -> None:
        async def fake_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-1",
                    "url": "https://example.com/d1",
                    "title": "Crude oil disruption in Iran affects shipping lanes",
                    "content": (
                        "Disruption and shortage risks rise for crude oil exports."
                    ),
                    "collected_at": "2026-03-27T00:00:00Z",
                }
            ]

        async def fake_substitutes(
            event_id: str,
            max_candidates: int = 5,
            repository: object = None,
        ) -> SubstituteFinderResult:
            _ = (max_candidates, repository)
            return SubstituteFinderResult(
                event_id=event_id,
                from_country="Iran",
                headline="Crude oil disruption in Iran affects shipping lanes",
                substitutes=[
                    CommoditySubstituteResult(
                        resource="energy",
                        commodity="crude_oil",
                        source="live",
                        countries=[
                            SubstituteCountry(
                                country="Saudi Arabia",
                                score=5,
                                reason="High exporter capacity.",
                                matched_commodities=["crude_oil"],
                            )
                        ],
                    )
                ],
            )

        with (
            patch(
                "backend.services.disruption_monitor_service._collect_documents",
                new=fake_collect,
            ),
            patch(
                "backend.services.disruption_monitor_service.find_substitutes_for_event",
                new=fake_substitutes,
            ),
        ):
            result = await service.run_monitor_once(trigger="manual")

        repo = DisruptionRepository(self._db_path)
        events = repo.list_events()
        runs = repo.list_runs()
        snapshots = repo.list_substitute_snapshots(events[0].event_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.emitted_events), 1)
        self.assertIn("https://example.com/d1", result.emitted_events[0].source_urls)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].from_country, "Iran")
        self.assertEqual(events[0].resource_type, "energy")
        self.assertEqual(events[0].commodity, "crude_oil")
        self.assertIn("https://example.com/d1", events[0].source_urls)
        self.assertEqual(runs[0].status, "completed")
        self.assertEqual(runs[0].emitted_count, 1)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].resource_type, "energy")
        self.assertEqual(snapshots[0].commodity, "crude_oil")
        self.assertEqual(snapshots[0].candidates[0]["country"], "Saudi Arabia")

    async def test_splits_multi_commodity_signal_into_multiple_events(self) -> None:
        async def fake_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-1",
                    "url": "https://example.com/d1",
                    "title": "Iran oil and gas exports disrupted",
                    "content": (
                        "Critical disruption affects oil and gas shipments to Asia."
                    ),
                    "collected_at": "2026-03-27T00:00:00Z",
                }
            ]

        async def fake_substitutes(
            event_id: str,
            max_candidates: int = 5,
            repository: object = None,
        ) -> SubstituteFinderResult:
            _ = (event_id, max_candidates, repository)
            return SubstituteFinderResult(
                event_id=event_id,
                from_country="Iran",
                headline="Iran oil and gas exports disrupted",
                substitutes=[],
            )

        with (
            patch(
                "backend.services.disruption_monitor_service._collect_documents",
                new=fake_collect,
            ),
            patch(
                "backend.services.disruption_monitor_service.find_substitutes_for_event",
                new=fake_substitutes,
            ),
        ):
            result = await service.run_monitor_once(trigger="manual")

        repo = DisruptionRepository(self._db_path)
        events = repo.list_events()
        commodities = {(row.resource_type, row.commodity) for row in events}

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.emitted_events), 2)
        self.assertEqual(len(events), 2)
        self.assertEqual(
            commodities,
            {("energy", "crude_oil"), ("energy", "natural_gas")},
        )

    async def test_updates_existing_event_when_meaningful(self) -> None:
        async def first_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-1",
                    "url": "https://example.com/d1",
                    "title": "Iran oil shipment delay causes supply constraint",
                    "content": "Delay in crude oil cargoes increases supply pressure.",
                    "collected_at": "2026-03-27T00:00:00Z",
                }
            ]

        async def second_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-2",
                    "url": "https://example.com/d2",
                    "title": "Critical attack disrupts Iran crude oil exports",
                    "content": (
                        "Critical disruption expected for crude oil availability."
                    ),
                    "collected_at": "2026-03-27T01:00:00Z",
                }
            ]

        with patch(
            "backend.services.disruption_monitor_service._collect_documents",
            new=first_collect,
        ):
            await service.run_monitor_once(trigger="manual")

        with patch(
            "backend.services.disruption_monitor_service._collect_documents",
            new=second_collect,
        ):
            result = await service.run_monitor_once(trigger="manual")

        repo = DisruptionRepository(self._db_path)
        events = repo.list_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].severity, "CRITICAL")
        self.assertIn("https://example.com/d2", events[0].source_urls)
        self.assertEqual(len(result.emitted_events), 1)
        self.assertIn("https://example.com/d2", result.emitted_events[0].source_urls)

    async def test_unchanged_signal_does_not_emit_new_update(self) -> None:
        async def collect() -> list[dict[str, str]]:
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
            new=collect,
        ):
            await service.run_monitor_once(trigger="manual")
            result = await service.run_monitor_once(trigger="manual")

        repo = DisruptionRepository(self._db_path)
        events = repo.list_events()
        runs = repo.list_runs()

        self.assertEqual(len(events), 1)
        self.assertEqual(runs[0].status, "completed")
        self.assertEqual(runs[0].emitted_count, 0)
        self.assertEqual(result.emitted_events, [])

    async def test_accepts_source_url_field_from_collector_payload(self) -> None:
        async def fake_collect() -> list[dict[str, str]]:
            return [
                {
                    "source_id": "doc-1",
                    "source_url": "https://example.com/source-url-field",
                    "title": "Iran oil shipment delay causes supply constraint",
                    "content": "Delay in crude oil cargoes increases supply pressure.",
                    "collected_at": "2026-03-27T00:00:00Z",
                }
            ]

        with patch(
            "backend.services.disruption_monitor_service._collect_documents",
            new=fake_collect,
        ):
            result = await service.run_monitor_once(trigger="manual")

        repo = DisruptionRepository(self._db_path)
        events = repo.list_events()

        self.assertEqual(len(result.emitted_events), 1)
        self.assertEqual(len(events), 1)
        self.assertIn(
            "https://example.com/source-url-field",
            result.emitted_events[0].source_urls,
        )
        self.assertIn("https://example.com/source-url-field", events[0].source_urls)

    async def test_returns_skipped_overlap_when_run_in_progress(self) -> None:
        await service._RUN_LOCK.acquire()
        try:
            result = await service.run_monitor_once(trigger="manual")
        finally:
            service._RUN_LOCK.release()

        repo = DisruptionRepository(self._db_path)
        runs = repo.list_runs()

        self.assertEqual(result.status, "skipped_overlap")
        self.assertEqual(result.emitted_events, [])
        self.assertEqual(runs[0].status, "skipped_overlap")


if __name__ == "__main__":
    unittest.main()
