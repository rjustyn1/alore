"""Simple JSON file-backed cache helper."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Generic, TypeVar

from backend.cache.memory_cache import CacheEntry

T = TypeVar("T")


class JsonFileCache(Generic[T]):
    """Tiny durable cache for sharing data across process restarts."""

    def __init__(
        self,
        *,
        path: str,
        serializer: Callable[[T], dict[str, object]],
        deserializer: Callable[[dict[str, object]], T],
    ) -> None:
        self._path = Path(path)
        self._serializer = serializer
        self._deserializer = deserializer

    def get(self) -> CacheEntry[T] | None:
        if not self._path.exists():
            return None
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return None
            payload = raw.get("value")
            if not isinstance(payload, dict):
                return None
            updated_raw = raw.get("updated_at", "")
            updated_at = datetime.fromisoformat(str(updated_raw))
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            value = self._deserializer(payload)
            return CacheEntry(value=value, updated_at=updated_at)
        except Exception:
            return None

    def set(self, value: T) -> CacheEntry[T]:
        entry = CacheEntry(value=value, updated_at=datetime.now(timezone.utc))
        payload = {
            "updated_at": entry.updated_at.isoformat(),
            "value": self._serializer(value),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(payload, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        return entry

    def clear(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
        except Exception:
            pass
