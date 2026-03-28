"""Unit tests for news curator API route."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.api import news_curator as api
from backend.models.news_curator import NewsArticle, NewsCuratorResponse


class NewsCuratorApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_route_returns_envelope(self) -> None:
        async def fake_get() -> NewsCuratorResponse:
            return NewsCuratorResponse(
                internal=[
                    NewsArticle(
                        rank=1,
                        title="Internal title",
                        hook="Internal hook.",
                        url="https://internal",
                    )
                ],
                external=[],
            )

        with patch(
            "backend.api.news_curator.get_singapore_news_curation", new=fake_get
        ):
            res = await api.singapore_news()

        self.assertEqual(res["status"], "ok")
        self.assertIn("internal", res["data"])
        self.assertIn("external", res["data"])


if __name__ == "__main__":
    unittest.main()
