"""Unit tests for supply-chain API route functions."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.api import supply_chain as api
from backend.models.supply_chain import (
    CountryResourceBuckets,
    ResourceCategory,
    SupplyChainConnectionsResponse,
    SupplyChainDataSource,
    SupplyChainScrapeData,
    SupplyChainScrapeRequest,
)


class SupplyChainApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_connections_route_returns_envelope(self) -> None:
        async def fake_get(refresh: bool = False) -> SupplyChainConnectionsResponse:
            _ = refresh
            return SupplyChainConnectionsResponse(
                source=SupplyChainDataSource.LIVE,
                connections={
                    "Indonesia": CountryResourceBuckets(
                        energy=["crude_oil"],
                        food=["rice"],
                    )
                },
            )

        with patch(
            "backend.api.supply_chain.get_singapore_connections",
            new=fake_get,
        ):
            res = await api.singapore_connections(refresh=False)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["source"], "live")
        self.assertIn("connections", res["data"])

    async def test_post_scrape_route_returns_envelope(self) -> None:
        async def fake_scrape(resource: str) -> SupplyChainScrapeData:
            return SupplyChainScrapeData(
                resource=resource,
                source=SupplyChainDataSource.CACHE_STALE,
                connections={"Indonesia": ["rice"]},
            )

        with patch(
            "backend.api.supply_chain.scrape_supply_chain_resource",
            new=fake_scrape,
        ):
            res = await api.scrape_supply_chain(
                SupplyChainScrapeRequest(resource=ResourceCategory.FOOD)
            )

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["resource"], "food")
        self.assertEqual(res["data"]["source"], "cache_stale")

    def test_scrape_request_invalid_resource_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SupplyChainScrapeRequest.model_validate({"resource": "invalid"})


if __name__ == "__main__":
    unittest.main()
