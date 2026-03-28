"""TinyFish API adapter."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib import error, request

from dotenv import load_dotenv

_DEFAULT_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"
_DEFAULT_TIMEOUT_SECONDS = 1800


class TinyFishClient:
    """Thin TinyFish automation client."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        run_url: str = _DEFAULT_RUN_URL,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        # Supports direct service usage where backend.main isn't imported.
        load_dotenv()
        self._api_key = (api_key or os.getenv("TINYFISH_API_KEY", "")).strip()
        self._run_url = run_url
        self._timeout_seconds = timeout_seconds

    async def run(
        self,
        *,
        url: str,
        goal: str,
        browser_profile: str = "lite",
        api_integration: str = "tinyfish-supply-chain-resilience",
    ) -> dict[str, Any]:
        """Execute one TinyFish automation run."""
        if not self._api_key:
            raise RuntimeError("TINYFISH_API_KEY is not set")
        return await asyncio.to_thread(
            self._run_sync,
            url,
            goal,
            browser_profile,
            api_integration,
        )

    def _run_sync(
        self,
        url: str,
        goal: str,
        browser_profile: str,
        api_integration: str,
    ) -> dict[str, Any]:
        payload = {
            "url": url,
            "goal": goal,
            "browser_profile": browser_profile,
            "api_integration": api_integration,
        }
        req = request.Request(
            self._run_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self._api_key,
            },
        )
        try:
            with request.urlopen(req, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"TinyFish request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"TinyFish request failed: {exc.reason}") from exc
