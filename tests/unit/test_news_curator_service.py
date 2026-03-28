"""Unit tests for news curator service behaviors."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services import news_curator_service as service


def _payload(rows: list[dict[str, str]]) -> dict:
    return {"status": "COMPLETED", "result": {"articles": rows}}


class NewsCuratorServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        service._NEWS_CACHE._entry = None
        service._NEWS_PERSISTED_CACHE.clear()

    async def test_live_success_and_internal_priority(self) -> None:
        async def fake_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            is_internal = "explicitly mentions singapore" in goal.lower()
            if is_internal:
                return _payload(
                    [
                        {
                            "title": "Singapore port congestion risk rises",
                            "hook": "Severe disruption reported. Delays are expected.",
                            "url": "https://example.com/internal-1",
                        },
                        {
                            "title": "Food import inspections tightened",
                            "hook": "Singapore regulators announced stricter controls.",
                            "url": "https://example.com/internal-2",
                        },
                        {
                            "title": "LNG delivery schedule adjusted",
                            "hook": "Supply chain planning teams updated allocations.",
                            "url": "https://example.com/internal-3",
                        },
                    ]
                )
            return _payload(
                [
                    {
                        "title": "Singapore port congestion risk rises",
                        "hook": "Duplicate title should stay internal only.",
                        "url": "https://example.com/external-dup",
                    },
                    {
                        "title": "Global wheat output revised lower",
                        "hook": "External food market stress intensifies.",
                        "url": "https://example.com/external-1",
                    },
                    {
                        "title": "Fuel export policy uncertainty grows",
                        "hook": "External energy outlook remains volatile.",
                        "url": "https://example.com/external-2",
                    },
                ]
            )

        with patch(
            "backend.services.news_curator_service.TinyFishClient.run", new=fake_run
        ):
            data = await service.get_singapore_news_curation()

        self.assertEqual(len(data.internal), 3)
        self.assertEqual(len(data.external), 2)
        self.assertNotIn(
            "Singapore port congestion risk rises",
            [article.title for article in data.external],
        )

    async def test_expands_to_31_days_when_14_days_insufficient(self) -> None:
        async def fake_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            is_internal = "explicitly mentions singapore" in goal.lower()
            is_14_day = "last 14 days" in goal.lower()

            if is_14_day and is_internal:
                return _payload(
                    [
                        {
                            "title": "Internal one 14-day item",
                            "hook": "Short hook.",
                            "url": "https://a-int",
                        }
                    ]
                )
            if is_14_day and not is_internal:
                return _payload(
                    [
                        {
                            "title": "External one 14-day item",
                            "hook": "Short hook.",
                            "url": "https://a-ext",
                        }
                    ]
                )
            if is_internal:
                return _payload(
                    [
                        {
                            "title": "Internal one 31-day item",
                            "hook": "Hook one.",
                            "url": "https://b-int",
                        },
                        {
                            "title": "Internal two 31-day item",
                            "hook": "Hook two.",
                            "url": "https://c-int",
                        },
                    ]
                )
            return _payload(
                [
                    {
                        "title": "External one 31-day item",
                        "hook": "Hook one.",
                        "url": "https://b-ext",
                    },
                    {
                        "title": "External two 31-day item",
                        "hook": "Hook two.",
                        "url": "https://c-ext",
                    },
                ]
            )

        with patch(
            "backend.services.news_curator_service.TinyFishClient.run", new=fake_run
        ):
            data = await service.get_singapore_news_curation()

        self.assertGreaterEqual(len(data.internal), 3)
        self.assertGreaterEqual(len(data.external), 3)

    async def test_fallback_when_live_fails_and_no_cache(self) -> None:
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
            "backend.services.news_curator_service.TinyFishClient.run", new=fail_run
        ):
            data = await service.get_singapore_news_curation()

        self.assertEqual(len(data.internal), 3)
        self.assertEqual(len(data.external), 3)

    async def test_cache_reuse_when_live_fails(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, browser_profile, api_integration)
            return _payload(
                [
                    {
                        "title": f"Seed from {goal[:10]}",
                        "hook": "Initial successful response.",
                        "url": "https://seed",
                    },
                    {
                        "title": "Seed 2",
                        "hook": "Initial successful response.",
                        "url": "https://seed2",
                    },
                    {
                        "title": "Seed 3",
                        "hook": "Initial successful response.",
                        "url": "https://seed3",
                    },
                ]
            )

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
            "backend.services.news_curator_service.TinyFishClient.run", new=success_run
        ):
            first = await service.get_singapore_news_curation()

        with patch(
            "backend.services.news_curator_service.TinyFishClient.run", new=fail_run
        ):
            second = await service.get_singapore_news_curation()

        self.assertEqual(
            [article.title for article in first.internal],
            [article.title for article in second.internal],
        )

    async def test_persisted_cache_survives_memory_clear(self) -> None:
        async def success_run(
            _self,
            *,
            url: str,
            goal: str,
            browser_profile: str = "lite",
            api_integration: str = "tinyfish-supply-chain-resilience",
        ) -> dict:
            _ = (url, goal, browser_profile, api_integration)
            return _payload(
                [
                    {
                        "title": "Persisted internal title",
                        "hook": "Initial successful response.",
                        "url": "https://seed",
                    },
                    {
                        "title": "Persisted internal title 2",
                        "hook": "Initial successful response.",
                        "url": "https://seed2",
                    },
                    {
                        "title": "Persisted internal title 3",
                        "hook": "Initial successful response.",
                        "url": "https://seed3",
                    },
                ]
            )

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
            "backend.services.news_curator_service.TinyFishClient.run", new=success_run
        ):
            await service.get_singapore_news_curation()

        service._NEWS_CACHE._entry = None

        with patch(
            "backend.services.news_curator_service.TinyFishClient.run", new=fail_run
        ):
            cached = await service.get_singapore_news_curation()

        self.assertEqual(cached.internal[0].title, "Persisted internal title")


if __name__ == "__main__":
    unittest.main()
