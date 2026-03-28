"""Unit tests for resolution-prep manager readiness checks."""

from __future__ import annotations

import unittest

from backend.agents.resolution_prep.manager import evaluate_packet_readiness
from backend.models.country_packet import (
    CountryNegotiationBrief,
    CountryPacket,
    CountryPacketDimension,
    CountryPacketPoint,
    CountryPacketSource,
)


class ResolutionPrepManagerTests(unittest.TestCase):
    def _build_complete_packet(self) -> CountryPacket:
        dimensions: list[CountryPacketDimension] = [
            "supply_capacity",
            "trade_relevance",
            "cost",
            "logistics",
            "risk",
            "sustainability",
        ]
        return CountryPacket(
            country="Singapore",
            country_role="origin",
            resource_type="energy",
            commodity="crude_oil",
            main_ideas=["Diversify quickly."],
            important_points=[
                CountryPacketPoint(
                    dimension=dimension,
                    point=f"Point for {dimension}",
                    support=["s1"],
                )
                for dimension in dimensions
            ],
            sources=[
                CountryPacketSource(
                    id="s1",
                    title="Credible source",
                    url="https://example.com/source",
                    credibility="high",
                    date="2026-03-28",
                )
            ],
            negotiation_brief=CountryNegotiationBrief(
                priorities=[
                    "Ensure continuous supply",
                    "Keep import costs stable",
                ],
                concession_options=["Flexible contract duration"],
                non_negotiables=["No major stockout risk"],
                counterpart_asks=[
                    "Guaranteed monthly shipment floor",
                    "Emergency rerouting clause",
                ],
                deal_risks=["Global spot price volatility"],
                readiness_summary="Enough signals for first-round negotiation.",
            ),
            source_mode="live",
        )

    def test_readiness_is_sufficient_for_complete_packet(self) -> None:
        packet = self._build_complete_packet()
        report = evaluate_packet_readiness(packet)
        self.assertTrue(report.is_sufficient)
        self.assertEqual(report.missing_requirements, [])

    def test_readiness_detects_missing_negotiation_signals(self) -> None:
        packet = self._build_complete_packet()
        packet.negotiation_brief = CountryNegotiationBrief()
        packet.sources = [
            CountryPacketSource(
                id="s1",
                title="Weak source",
                url="https://example.com/weak",
                credibility="low",
                date="2026-03-28",
            )
        ]

        report = evaluate_packet_readiness(packet)
        self.assertFalse(report.is_sufficient)
        self.assertIn("negotiation_brief.priorities", report.missing_requirements)
        self.assertIn("negotiation_brief.counterpart_asks", report.missing_requirements)
        self.assertIn("sources.credible", report.missing_requirements)


if __name__ == "__main__":
    unittest.main()
