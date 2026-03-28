"""Unit tests for resolution-prep API routes."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.api import resolution_prep as api
from backend.models.country_packet import CountryPacket
from backend.models.resolution_workflow import (
    ResolutionPrepKickoffData,
    ResolutionPrepStartRequest,
    ResolutionPrepStatusData,
)


class ResolutionPrepApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_route_returns_envelope(self) -> None:
        async def fake_start(body: object) -> ResolutionPrepKickoffData:
            _ = body
            return ResolutionPrepKickoffData(
                workflow_id="wf_123",
                stage="origin_packet_ready",
                event_id="evt_001",
                origin_country="Singapore",
                resource_type="energy",
                commodity="crude_oil",
                origin_packet=CountryPacket(
                    country="Singapore",
                    country_role="origin",
                    resource_type="energy",
                    commodity="crude_oil",
                    main_ideas=["Diversify imports quickly."],
                    important_points=[],
                    sources=[],
                    source_mode="fallback_seed",
                ),
                reused_workflow=False,
            )

        with patch("backend.api.resolution_prep.start_resolution_prep", new=fake_start):
            res = await api.start_resolution_prep_workflow(
                body=ResolutionPrepStartRequest(
                    event_id="evt_001",
                )
            )
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["workflow_id"], "wf_123")
        self.assertEqual(res["data"]["origin_packet"]["country"], "Singapore")

    async def test_status_route_returns_envelope(self) -> None:
        def fake_status(workflow_id: str) -> ResolutionPrepStatusData:
            self.assertEqual(workflow_id, "wf_123")
            return ResolutionPrepStatusData(
                workflow_id="wf_123",
                stage="substitute_packets_in_progress",
                event_id="evt_001",
                resource_type="energy",
                commodity="crude_oil",
                country_statuses={"Singapore": "completed", "Malaysia": "in_progress"},
                packets={
                    "Singapore": CountryPacket(
                        country="Singapore",
                        country_role="origin",
                        resource_type="energy",
                        commodity="crude_oil",
                        main_ideas=["Diversify imports quickly."],
                        important_points=[],
                        sources=[],
                        source_mode="fallback_seed",
                    )
                },
            )

        with patch(
            "backend.api.resolution_prep.get_resolution_prep_status", new=fake_status
        ):
            res = await api.get_resolution_prep_workflow(workflow_id="wf_123")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["stage"], "substitute_packets_in_progress")
        self.assertIn("Singapore", res["data"]["packets"])

    async def test_status_route_returns_404_when_not_found(self) -> None:
        def fake_status(workflow_id: str) -> ResolutionPrepStatusData:
            _ = workflow_id
            raise ValueError("Resolution workflow not found: wf_missing")

        with patch(
            "backend.api.resolution_prep.get_resolution_prep_status", new=fake_status
        ):
            with self.assertRaises(HTTPException) as ctx:
                await api.get_resolution_prep_workflow(workflow_id="wf_missing")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_start_route_returns_409_when_snapshots_missing(self) -> None:
        async def fake_start(body: object) -> ResolutionPrepKickoffData:
            _ = body
            raise ValueError("Substitute snapshots not found: evt_001")

        with patch("backend.api.resolution_prep.start_resolution_prep", new=fake_start):
            with self.assertRaises(HTTPException) as ctx:
                await api.start_resolution_prep_workflow(
                    body=ResolutionPrepStartRequest(event_id="evt_001")
                )
        self.assertEqual(ctx.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
