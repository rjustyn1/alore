"""Unit tests for supply-chain service behaviors."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.models.supply_chain import SupplyChainDataSource
from backend.services import supply_chain_service as service


def _live_payload(connections: dict[str, list[str]]) -> dict:
    return {"status": "COMPLETED", "result": {"connections": connections}}


class SupplyChainServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        service._CONNECTIONS_CACHE._entry = None
        service._CONNECTIONS_PERSISTED_CACHE.clear()

    async def test_live_success_merges_resources_and_dedupes(self) -> None:
        async def fake_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            if "energy" in goal.lower():
                return _live_payload(
                    {
                        "Indonesia": ["crude_oil", "natural_gas", "crude_oil"],
                        "Malaysia": ["natural_gas"],
                    }
                )
            return _live_payload(
                {
                    "Indonesia": ["rice", "spices", "rice"],
                    "Brazil": ["soybeans"],
                }
            )

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=fake_run,
        ):
            data = await service.get_singapore_connections(refresh=True)

        self.assertEqual(data.source, SupplyChainDataSource.LIVE)
        self.assertEqual(
            data.connections["Indonesia"].energy,
            ["crude_oil", "natural_gas"],
        )
        self.assertEqual(data.connections["Indonesia"].food, ["rice", "spices"])
        self.assertEqual(data.connections["Brazil"].energy, [])
        self.assertEqual(data.connections["Brazil"].food, ["soybeans"])

    async def test_refresh_true_uses_cache_stale_when_live_fails(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            if "energy" in goal.lower():
                return _live_payload({"Indonesia": ["crude_oil"]})
            return _live_payload({"Indonesia": ["rice"]})

        async def fail_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, goal, browser_profile, api_integration)
            raise RuntimeError("network failure")

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=success_run,
        ):
            first = await service.get_singapore_connections(refresh=True)

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=fail_run,
        ):
            second = await service.get_singapore_connections(refresh=True)

        self.assertEqual(first.source, SupplyChainDataSource.LIVE)
        self.assertEqual(second.source, SupplyChainDataSource.CACHE_STALE)
        self.assertEqual(
            second.connections["Indonesia"].energy,
            first.connections["Indonesia"].energy,
        )
        self.assertEqual(
            second.connections["Indonesia"].food,
            first.connections["Indonesia"].food,
        )

    async def test_fallback_seed_when_no_cache_and_live_fails(self) -> None:
        async def fail_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, goal, browser_profile, api_integration)
            raise RuntimeError("network failure")

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=fail_run,
        ):
            data = await service.get_singapore_connections(refresh=True)

        self.assertEqual(data.source, SupplyChainDataSource.FALLBACK_SEED)
        self.assertIn("Indonesia", data.connections)
        self.assertTrue(data.connections["Indonesia"].energy)
        self.assertTrue(data.connections["Indonesia"].food)

    async def test_refresh_false_uses_cache_without_live_attempt(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            if "energy" in goal.lower():
                return _live_payload({"Indonesia": ["crude_oil"]})
            return _live_payload({"Indonesia": ["rice"]})

        async def fail_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, goal, browser_profile, api_integration)
            raise RuntimeError("should not be called")

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=success_run,
        ):
            await service.get_singapore_connections(refresh=True)

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=fail_run,
        ):
            cached = await service.get_singapore_connections(refresh=False)

        self.assertEqual(cached.source, SupplyChainDataSource.LIVE)

    async def test_resource_scrape_uses_shared_combined_pipeline(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            if "energy" in goal.lower():
                return _live_payload({"Indonesia": ["crude_oil"]})
            return _live_payload({"Indonesia": ["rice"]})

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=success_run,
        ):
            food = await service.scrape_supply_chain_resource("food")
            energy = await service.scrape_supply_chain_resource("energy")

        self.assertEqual(food.source, SupplyChainDataSource.LIVE)
        self.assertEqual(energy.source, SupplyChainDataSource.LIVE)
        self.assertEqual(food.connections["Indonesia"], ["rice"])
        self.assertEqual(energy.connections["Indonesia"], ["crude_oil"])

    async def test_persisted_cache_survives_memory_clear(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            if "energy" in goal.lower():
                return _live_payload({"Indonesia": ["crude_oil"]})
            return _live_payload({"Indonesia": ["rice"]})

        async def fail_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, goal, browser_profile, api_integration)
            raise RuntimeError("network failure")

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=success_run,
        ):
            await service.get_singapore_connections(refresh=True)

        service._CONNECTIONS_CACHE._entry = None

        with patch(
            "backend.services.supply_chain_service.TinyFishClient.run",
            new=fail_run,
        ):
            cached = await service.get_singapore_connections(refresh=False)

        self.assertEqual(cached.source, SupplyChainDataSource.LIVE)
        self.assertEqual(cached.connections["Indonesia"].energy, ["crude_oil"])


if __name__ == "__main__":
    unittest.main()
