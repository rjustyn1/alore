"""Unit tests for substitute finder utility."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from backend.db.models import DisruptionEventRecord
from backend.db.repositories import DisruptionRepository
from backend.models.supply_chain import (
    CountryResourceBuckets,
    SupplyChainConnectionsResponse,
    SupplyChainDataSource,
)
from backend.utils.substitute_finder import find_substitutes_for_event


class SubstituteFinderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmpdir.name, "substitutes.db")
        os.environ["DISRUPTION_DB_PATH"] = self._db_path
        self._repo = DisruptionRepository(self._db_path)
        self._repo.insert_event(
            DisruptionEventRecord(
                event_id="evt_001",
                from_country="Iran",
                severity="CRITICAL",
                resource_type="energy",
                commodity="crude_oil",
                headline="Iran oil exports disrupted",
                source_urls=["https://example.com/disruption"],
            )
        )

    def tearDown(self) -> None:
        os.environ.pop("DISRUPTION_DB_PATH", None)
        self._tmpdir.cleanup()

    async def test_missing_event_raises(self) -> None:
        with self.assertRaises(ValueError):
            await find_substitutes_for_event("evt_missing")

    async def test_live_results_are_ranked_and_exclude_disrupted_country(self) -> None:
        live_payload = {
            "status": "COMPLETED",
            "result": {
                "candidates": [
                    {
                        "country": "Iran",
                        "commodities": ["crude_oil"],
                        "export_signal": "high",
                        "reason": "Large oil exporter.",
                    },
                    {
                        "country": "Saudi Arabia",
                        "commodities": ["crude_oil"],
                        "export_signal": "high",
                        "reason": "Strong export base.",
                    },
                    {
                        "country": "Russia",
                        "commodities": ["crude_oil"],
                        "export_signal": "medium",
                        "reason": "Large producer.",
                    },
                ]
            },
        }
        connections = SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections={
                "Saudi Arabia": CountryResourceBuckets(energy=["crude_oil"], food=[]),
                "Russia": CountryResourceBuckets(energy=["crude_oil"], food=[]),
            },
        )

        with (
            patch(
                "backend.utils.substitute_finder.TinyFishClient.run",
                new=AsyncMock(return_value=live_payload),
            ),
            patch(
                "backend.utils.substitute_finder.get_singapore_connections",
                new=AsyncMock(return_value=connections),
            ),
        ):
            result = await find_substitutes_for_event("evt_001")

        self.assertEqual(result.event_id, "evt_001")
        self.assertEqual(len(result.substitutes), 1)
        by_commodity = result.substitutes[0]
        self.assertEqual(by_commodity.source, "live")
        countries = [item.country for item in by_commodity.countries]
        self.assertNotIn("Iran", countries)
        self.assertEqual(countries[0], "Saudi Arabia")

    async def test_fallback_uses_connections_when_live_scrape_fails(self) -> None:
        connections = SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections={
                "Saudi Arabia": CountryResourceBuckets(energy=["crude_oil"], food=[]),
                "Iraq": CountryResourceBuckets(energy=["crude_oil"], food=[]),
                "Australia": CountryResourceBuckets(energy=["coal"], food=[]),
            },
        )

        with (
            patch(
                "backend.utils.substitute_finder.TinyFishClient.run",
                new=AsyncMock(side_effect=RuntimeError("boom")),
            ),
            patch(
                "backend.utils.substitute_finder.get_singapore_connections",
                new=AsyncMock(return_value=connections),
            ),
        ):
            result = await find_substitutes_for_event("evt_001")

        self.assertEqual(len(result.substitutes), 1)
        by_commodity = result.substitutes[0]
        self.assertEqual(by_commodity.source, "fallback_connections")
        countries = {item.country for item in by_commodity.countries}
        self.assertEqual(countries, {"Saudi Arabia", "Iraq"})

    async def test_excludes_alias_of_disrupted_country(self) -> None:
        live_payload = {
            "status": "COMPLETED",
            "result": {
                "candidates": [
                    {
                        "country": "Iran, Islamic Republic of",
                        "commodities": ["crude_oil"],
                        "export_signal": "high",
                        "reason": "Alias form for Iran.",
                    },
                    {
                        "country": "Iraq",
                        "commodities": ["crude_oil"],
                        "export_signal": "medium",
                        "reason": "Alternative supplier.",
                    },
                ]
            },
        }
        connections = SupplyChainConnectionsResponse(
            source=SupplyChainDataSource.LIVE,
            connections={
                "Iraq": CountryResourceBuckets(energy=["crude_oil"], food=[]),
            },
        )

        with (
            patch(
                "backend.utils.substitute_finder.TinyFishClient.run",
                new=AsyncMock(return_value=live_payload),
            ),
            patch(
                "backend.utils.substitute_finder.get_singapore_connections",
                new=AsyncMock(return_value=connections),
            ),
        ):
            result = await find_substitutes_for_event("evt_001")

        countries = [item.country for item in result.substitutes[0].countries]
        self.assertNotIn("Iran, Islamic Republic of", countries)
        self.assertEqual(countries, ["Iraq"])


if __name__ == "__main__":
    unittest.main()
