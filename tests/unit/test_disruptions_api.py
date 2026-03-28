"""Unit tests for disruptions API route."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.api import disruptions as api
from backend.models.disruption_event import DisruptionEvent, DisruptionMonitorRunResult
from backend.utils.substitute_finder import (
    CommoditySubstituteResult,
    SubstituteCountry,
    SubstituteFinderResult,
)


class DisruptionsApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_route_returns_envelope(self) -> None:
        async def fake_run(trigger: str) -> DisruptionMonitorRunResult:
            _ = trigger
            return DisruptionMonitorRunResult(
                run_id="run_20260327_120000_abcd",
                status="completed",
                trigger="manual",
                emitted_events=[
                    DisruptionEvent(
                        event_id="evt_001",
                        from_country="Iran",
                        severity="DISRUPTED",
                        resource_type="energy",
                        commodity="crude_oil",
                        headline="Iran-linked disruption signal",
                        source_urls=["https://example.com/disruption"],
                    )
                ],
            )

        with patch("backend.api.disruptions.run_monitor_once", new=fake_run):
            res = await api.run_disruption_monitor()

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["status"], "completed")
        self.assertEqual(res["data"]["trigger"], "manual")
        self.assertEqual(res["data"]["emitted_events"][0]["event_id"], "evt_001")
        self.assertEqual(
            res["data"]["emitted_events"][0]["source_urls"],
            ["https://example.com/disruption"],
        )

    async def test_substitute_route_returns_envelope(self) -> None:
        async def fake_find(
            event_id: str,
            max_candidates: int = 5,
            repository: object = None,
        ) -> SubstituteFinderResult:
            _ = repository
            self.assertEqual(event_id, "evt_001")
            self.assertEqual(max_candidates, 5)
            return SubstituteFinderResult(
                event_id="evt_001",
                from_country="Iran",
                headline="Oil exports disrupted",
                substitutes=[
                    CommoditySubstituteResult(
                        resource="energy",
                        commodity="crude_oil",
                        source="live",
                        countries=[
                            SubstituteCountry(
                                country="Saudi Arabia",
                                score=6,
                                reason="Strong exporter and SG link.",
                                matched_commodities=["crude_oil"],
                            )
                        ],
                    )
                ],
            )

        with patch("backend.api.disruptions.find_substitutes_for_event", new=fake_find):
            res = await api.get_substitutes_for_event(
                event_id="evt_001", max_candidates=5
            )

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["event_id"], "evt_001")
        self.assertEqual(res["data"]["substitutes"][0]["resource"], "energy")
        self.assertEqual(
            res["data"]["substitutes"][0]["countries"][0]["country"], "Saudi Arabia"
        )

    async def test_list_events_route_returns_source_urls(self) -> None:
        def fake_list(*, limit: int = 100) -> list[DisruptionEvent]:
            self.assertEqual(limit, 50)
            return [
                DisruptionEvent(
                    event_id="evt_001",
                    from_country="Iran",
                    severity="DISRUPTED",
                    resource_type="energy",
                    commodity="crude_oil",
                    headline="Iran-linked disruption signal",
                    source_urls=["https://example.com/disruption"],
                )
            ]

        with patch("backend.api.disruptions.list_persisted_events", new=fake_list):
            res = await api.list_disruption_events(limit=50)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"][0]["event_id"], "evt_001")
        self.assertEqual(
            res["data"][0]["source_urls"], ["https://example.com/disruption"]
        )

    async def test_get_event_route_returns_404_when_missing(self) -> None:
        def fake_get(event_id: str) -> DisruptionEvent:
            _ = event_id
            raise ValueError("Disruption event not found: evt_missing")

        with patch("backend.api.disruptions.get_persisted_event", new=fake_get):
            with self.assertRaises(HTTPException) as ctx:
                await api.get_disruption_event(event_id="evt_missing")

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_substitute_route_returns_404_for_missing_event(self) -> None:
        async def fake_find(
            event_id: str,
            max_candidates: int = 5,
            repository: object = None,
        ) -> SubstituteFinderResult:
            _ = (event_id, max_candidates, repository)
            raise ValueError("Disruption event not found: evt_missing")

        with patch("backend.api.disruptions.find_substitutes_for_event", new=fake_find):
            with self.assertRaises(HTTPException) as ctx:
                await api.get_substitutes_for_event(
                    event_id="evt_missing", max_candidates=5
                )

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("Disruption event not found", str(ctx.exception.detail))


if __name__ == "__main__":
    unittest.main()
