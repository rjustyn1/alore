"""News curator domain models."""

from __future__ import annotations

from pydantic import BaseModel


class NewsArticle(BaseModel):
    rank: int
    title: str
    hook: str
    url: str


class NewsCuratorResponse(BaseModel):
    internal: list[NewsArticle]
    external: list[NewsArticle]
