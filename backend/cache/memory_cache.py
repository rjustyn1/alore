"""Simple in-memory cache helper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CacheEntry(Generic[T]):
    value: T
    updated_at: datetime


class MemoryCache(Generic[T]):
    """Tiny process-local cache for V0 endpoints."""

    def __init__(self) -> None:
        self._entry: CacheEntry[T] | None = None

    def get(self) -> CacheEntry[T] | None:
        return self._entry

    def set(self, value: T) -> CacheEntry[T]:
        self._entry = CacheEntry(value=value, updated_at=datetime.now(timezone.utc))
        return self._entry
