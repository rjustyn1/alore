"""Scheduled runner placeholders for disruption monitoring."""

from __future__ import annotations

from backend.services.disruption_monitor_service import run_monitor_once


async def run_daily_monitor() -> dict:
    """Execute one scheduled monitor run."""
    result = await run_monitor_once(trigger="scheduled")
    return result.model_dump()
