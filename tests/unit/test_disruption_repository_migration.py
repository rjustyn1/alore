"""Unit tests for disruption event migration to single-commodity rows."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from backend.db.repositories import DisruptionRepository


class DisruptionRepositoryMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._tmpdir.name, "migration.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed_legacy_schema(self) -> None:
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            """
            CREATE TABLE disruption_events (
                event_id TEXT PRIMARY KEY,
                from_country TEXT NOT NULL,
                severity TEXT NOT NULL,
                resource_types TEXT NOT NULL,
                headline TEXT NOT NULL,
                source_urls TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO disruption_events (
                event_id, from_country, severity, resource_types, headline,
                source_urls, created_at, updated_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evt_legacy_1",
                "Iran",
                "CRITICAL",
                json.dumps(
                    {
                        "energy": ["crude_oil", "natural_gas"],
                        "food": ["rice"],
                    },
                    sort_keys=True,
                ),
                "Legacy multi-commodity event",
                json.dumps(["https://example.com/disruption"]),
                "2026-03-28T00:00:00Z",
                "2026-03-28T00:00:00Z",
                "2026-03-28T00:00:00Z",
            ),
        )
        conn.commit()
        conn.close()

    def test_backfills_legacy_multi_commodity_rows(self) -> None:
        self._seed_legacy_schema()

        repo = DisruptionRepository(db_path=self._db_path)
        rows = repo.list_events()

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row.event_id != "evt_legacy_1" for row in rows))
        self.assertEqual(
            {(row.resource_type, row.commodity) for row in rows},
            {
                ("energy", "crude_oil"),
                ("energy", "natural_gas"),
                ("food", "rice"),
            },
        )


if __name__ == "__main__":
    unittest.main()
