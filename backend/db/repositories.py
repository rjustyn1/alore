"""Repositories for disruption monitor persistence."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.db.connection import get_connection
from backend.db.models import (
    CountryPacketRecord,
    DisruptionEventRecord,
    DisruptionRunRecord,
    DisruptionSubstituteSnapshotRecord,
    ResolutionWorkflowRecord,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _flatten_resource_types(
    resource_types: Mapping[str, object],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for resource in ("food", "energy"):
        raw_values = resource_types.get(resource, [])
        if not isinstance(raw_values, list):
            continue
        for raw in raw_values:
            if not isinstance(raw, str):
                continue
            commodity = _normalize_token(raw)
            if commodity:
                pair = (resource, commodity)
                if pair not in pairs:
                    pairs.append(pair)
    return pairs


class DisruptionRepository:
    """Storage access for disruption records and run history."""

    def __init__(self, db_path: str = "backend.db") -> None:
        self._db_path = db_path
        self.init_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = get_connection(self._db_path)
        try:
            yield connection
        finally:
            connection.close()

    def init_schema(self) -> None:
        """Create required tables if they do not exist."""
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS disruption_events (
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
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_disruption_events_country
                ON disruption_events(from_country)
                """
            )
            self._ensure_column(
                connection,
                table_name="disruption_events",
                column_name="source_urls",
                column_sql="TEXT NOT NULL DEFAULT '[]'",
            )
            self._ensure_column(
                connection,
                table_name="disruption_events",
                column_name="resource_type",
                column_sql="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table_name="disruption_events",
                column_name="commodity",
                column_sql="TEXT NOT NULL DEFAULT ''",
            )
            connection.execute(
                """
                UPDATE disruption_events
                SET source_urls = '[]'
                WHERE source_urls IS NULL OR TRIM(source_urls) = ''
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_disruption_events_signature
                ON disruption_events(from_country, resource_type, commodity)
                """
            )
            self._migrate_events_to_single_commodity(connection)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS disruption_runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    emitted_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS disruption_substitute_snapshots (
                    event_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    candidates_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(event_id, resource_type, commodity)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_disruption_substitutes_event
                ON disruption_substitute_snapshots(event_id)
                """
            )
            connection.commit()

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        *,
        table_name: str,
        column_name: str,
        column_sql: str,
    ) -> None:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        existing_columns = {str(row["name"]) for row in rows}
        if column_name in existing_columns:
            return
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
        )

    @staticmethod
    def _migrate_events_to_single_commodity(connection: sqlite3.Connection) -> None:
        """Backfill legacy multi-commodity rows into one row per commodity.

        Legacy rows are replaced with new rows that each carry a new `event_id`.
        """
        rows = connection.execute(
            """
            SELECT event_id, from_country, severity, resource_types, headline,
                   source_urls, created_at, updated_at, last_seen_at,
                   resource_type, commodity
            FROM disruption_events
            WHERE resource_type IS NULL OR TRIM(resource_type) = ''
               OR commodity IS NULL OR TRIM(commodity) = ''
            """
        ).fetchall()

        for row in rows:
            legacy_event_id = str(row["event_id"])
            from_country = str(row["from_country"])
            severity = str(row["severity"])
            headline = str(row["headline"])
            created_at = str(row["created_at"])
            updated_at = str(row["updated_at"])
            last_seen_at = str(row["last_seen_at"])

            source_urls_raw = row["source_urls"]
            try:
                source_urls = json.loads(str(source_urls_raw))
                if not isinstance(source_urls, list):
                    source_urls = []
            except Exception:
                source_urls = []
            source_urls_json = json.dumps(source_urls)

            pairs: list[tuple[str, str]] = []
            normalized_resource = _normalize_token(str(row["resource_type"] or ""))
            normalized_commodity = _normalize_token(str(row["commodity"] or ""))
            if normalized_resource in {"food", "energy"} and normalized_commodity:
                pairs.append((normalized_resource, normalized_commodity))

            if not pairs:
                resource_types_raw = row["resource_types"]
                try:
                    decoded = json.loads(str(resource_types_raw))
                except Exception:
                    decoded = {}
                if isinstance(decoded, Mapping):
                    pairs = _flatten_resource_types(decoded)

            if not pairs:
                connection.execute(
                    "DELETE FROM disruption_events WHERE event_id = ?",
                    (legacy_event_id,),
                )
                continue

            for resource_type, commodity in pairs:
                new_event_id = f"evt_{uuid.uuid4().hex[:10]}"
                single_resource_json = json.dumps(
                    {resource_type: [commodity]},
                    sort_keys=True,
                )
                connection.execute(
                    """
                    INSERT INTO disruption_events (
                        event_id, from_country, severity, resource_types, resource_type,
                        commodity, headline, source_urls, created_at, updated_at,
                        last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_event_id,
                        from_country,
                        severity,
                        single_resource_json,
                        resource_type,
                        commodity,
                        headline,
                        source_urls_json,
                        created_at,
                        updated_at,
                        last_seen_at,
                    ),
                )

            connection.execute(
                "DELETE FROM disruption_events WHERE event_id = ?",
                (legacy_event_id,),
            )

    def list_events(self) -> list[DisruptionEventRecord]:
        """Return all persisted disruption events."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, from_country, severity, resource_type, commodity,
                       resource_types, headline,
                       source_urls, created_at, updated_at, last_seen_at
                FROM disruption_events
                """
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_events_by_country(self, from_country: str) -> list[DisruptionEventRecord]:
        """Return events filtered by origin country."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, from_country, severity, resource_type, commodity,
                       resource_types, headline,
                       source_urls, created_at, updated_at, last_seen_at
                FROM disruption_events
                WHERE from_country = ?
                """,
                (from_country,),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_event_by_id(self, event_id: str) -> DisruptionEventRecord | None:
        """Return one disruption event by id."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT event_id, from_country, severity, resource_type, commodity,
                       resource_types, headline,
                       source_urls, created_at, updated_at, last_seen_at
                FROM disruption_events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_event(row)

    def upsert_substitute_snapshot(
        self, record: DisruptionSubstituteSnapshotRecord
    ) -> DisruptionSubstituteSnapshotRecord:
        """Insert or update substitute snapshot for an event/resource/commodity."""
        updated_at = record.updated_at or _utc_now_iso()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO disruption_substitute_snapshots (
                    event_id, resource_type, commodity, source,
                    candidates_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id, resource_type, commodity) DO UPDATE SET
                    source = excluded.source,
                    candidates_json = excluded.candidates_json,
                    updated_at = excluded.updated_at
                """,
                (
                    record.event_id,
                    record.resource_type,
                    record.commodity,
                    record.source,
                    json.dumps(record.candidates, sort_keys=True),
                    updated_at,
                ),
            )
            connection.commit()
        return DisruptionSubstituteSnapshotRecord(
            event_id=record.event_id,
            resource_type=record.resource_type,
            commodity=record.commodity,
            source=record.source,
            candidates=list(record.candidates),
            updated_at=updated_at,
        )

    def get_substitute_snapshot(
        self,
        *,
        event_id: str,
        resource_type: str,
        commodity: str,
    ) -> DisruptionSubstituteSnapshotRecord | None:
        """Return one substitute snapshot row."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT event_id, resource_type, commodity, source,
                       candidates_json, updated_at
                FROM disruption_substitute_snapshots
                WHERE event_id = ? AND resource_type = ? AND commodity = ?
                """,
                (event_id, resource_type, commodity),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_substitute_snapshot(row)

    def list_substitute_snapshots(
        self, event_id: str
    ) -> list[DisruptionSubstituteSnapshotRecord]:
        """Return substitute snapshots for one event."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, resource_type, commodity, source,
                       candidates_json, updated_at
                FROM disruption_substitute_snapshots
                WHERE event_id = ?
                ORDER BY updated_at DESC
                """,
                (event_id,),
            ).fetchall()
        return [self._row_to_substitute_snapshot(row) for row in rows]

    def insert_event(self, record: DisruptionEventRecord) -> DisruptionEventRecord:
        """Insert a new disruption event."""
        created_at = record.created_at or _utc_now_iso()
        updated_at = record.updated_at or created_at
        last_seen_at = record.last_seen_at or updated_at
        single_resource_payload = {record.resource_type: [record.commodity]}
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO disruption_events (
                    event_id, from_country, severity, resource_types, resource_type,
                    commodity, headline, source_urls, created_at, updated_at,
                    last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.event_id,
                    record.from_country,
                    record.severity,
                    json.dumps(single_resource_payload, sort_keys=True),
                    record.resource_type,
                    record.commodity,
                    record.headline,
                    json.dumps(record.source_urls),
                    created_at,
                    updated_at,
                    last_seen_at,
                ),
            )
            connection.commit()
        return DisruptionEventRecord(
            event_id=record.event_id,
            from_country=record.from_country,
            severity=record.severity,
            resource_type=record.resource_type,
            commodity=record.commodity,
            headline=record.headline,
            source_urls=list(record.source_urls),
            created_at=created_at,
            updated_at=updated_at,
            last_seen_at=last_seen_at,
        )

    def update_event(self, record: DisruptionEventRecord) -> DisruptionEventRecord:
        """Update an existing disruption event."""
        updated_at = record.updated_at or _utc_now_iso()
        last_seen_at = record.last_seen_at or updated_at
        single_resource_payload = {record.resource_type: [record.commodity]}
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE disruption_events
                SET severity = ?,
                    resource_types = ?,
                    resource_type = ?,
                    commodity = ?,
                    headline = ?,
                    source_urls = ?,
                    updated_at = ?,
                    last_seen_at = ?
                WHERE event_id = ?
                """,
                (
                    record.severity,
                    json.dumps(single_resource_payload, sort_keys=True),
                    record.resource_type,
                    record.commodity,
                    record.headline,
                    json.dumps(record.source_urls),
                    updated_at,
                    last_seen_at,
                    record.event_id,
                ),
            )
            connection.commit()
        return DisruptionEventRecord(
            event_id=record.event_id,
            from_country=record.from_country,
            severity=record.severity,
            resource_type=record.resource_type,
            commodity=record.commodity,
            headline=record.headline,
            source_urls=list(record.source_urls),
            created_at=record.created_at,
            updated_at=updated_at,
            last_seen_at=last_seen_at,
        )

    def touch_event(self, event_id: str) -> None:
        """Refresh last-seen timestamp without emission-worthy changes."""
        now = _utc_now_iso()
        with self._connection() as connection:
            connection.execute(
                "UPDATE disruption_events SET last_seen_at = ? WHERE event_id = ?",
                (now, event_id),
            )
            connection.commit()

    def insert_run(self, run: DisruptionRunRecord) -> DisruptionRunRecord:
        """Persist monitor run status."""
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO disruption_runs (
                    run_id, status, trigger, started_at, finished_at,
                    emitted_count, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.status,
                    run.trigger,
                    run.started_at,
                    run.finished_at,
                    run.emitted_count,
                    run.error_message,
                ),
            )
            connection.commit()
        return run

    def list_runs(self) -> list[DisruptionRunRecord]:
        """Return run history records."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT run_id, status, trigger, started_at, finished_at,
                       emitted_count, error_message
                FROM disruption_runs
                ORDER BY started_at DESC
                """
            ).fetchall()
        return [
            DisruptionRunRecord(
                run_id=row["run_id"],
                status=row["status"],
                trigger=row["trigger"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
                emitted_count=int(row["emitted_count"]),
                error_message=row["error_message"] or "",
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_event(row: Mapping[str, object]) -> DisruptionEventRecord:
        def row_value(key: str, default: str) -> str:
            try:
                value = row[key]
            except Exception:
                return default
            return str(value)

        event_id = row_value("event_id", "")
        from_country = row_value("from_country", "")
        severity = row_value("severity", "")
        resource_type = row_value("resource_type", "")
        commodity = row_value("commodity", "")
        resource_types_raw = row_value("resource_types", "{}")
        headline = row_value("headline", "")
        source_urls_raw = row_value("source_urls", "[]")
        created_at = row_value("created_at", "")
        updated_at = row_value("updated_at", "")
        last_seen_at = row_value("last_seen_at", "")

        if not resource_type or not commodity:
            try:
                decoded_resource_types = json.loads(resource_types_raw)
            except Exception:
                decoded_resource_types = {}
            if isinstance(decoded_resource_types, Mapping):
                pairs = _flatten_resource_types(decoded_resource_types)
                if pairs:
                    resource_type, commodity = pairs[0]

        try:
            source_urls = json.loads(source_urls_raw)
            if not isinstance(source_urls, list):
                source_urls = []
        except Exception:
            source_urls = []

        return DisruptionEventRecord(
            event_id=event_id,
            from_country=from_country,
            severity=severity,
            resource_type=resource_type,
            commodity=commodity,
            headline=headline,
            source_urls=source_urls,
            created_at=created_at,
            updated_at=updated_at,
            last_seen_at=last_seen_at,
        )

    @staticmethod
    def _row_to_substitute_snapshot(
        row: Mapping[str, object],
    ) -> DisruptionSubstituteSnapshotRecord:
        def row_value(key: str, default: str) -> str:
            try:
                value = row[key]
            except Exception:
                return default
            return str(value)

        candidates_raw = row_value("candidates_json", "[]")
        return DisruptionSubstituteSnapshotRecord(
            event_id=row_value("event_id", ""),
            resource_type=row_value("resource_type", ""),
            commodity=row_value("commodity", ""),
            source=row_value("source", ""),
            candidates=json.loads(candidates_raw),
            updated_at=row_value("updated_at", ""),
        )


class ResolutionPrepRepository:
    """Storage access for resolution-prep workflows and country packets."""

    def __init__(self, db_path: str = "backend.db") -> None:
        self._db_path = db_path
        self.init_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = get_connection(self._db_path)
        try:
            yield connection
        finally:
            connection.close()

    def init_schema(self) -> None:
        """Create resolution-prep tables if they do not exist."""
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS resolution_workflows (
                    workflow_id TEXT PRIMARY KEY,
                    normalized_key TEXT NOT NULL UNIQUE,
                    event_id TEXT NOT NULL,
                    origin_country TEXT NOT NULL,
                    disrupted_supplier_country TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    commodity TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    country_statuses TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS resolution_country_packets (
                    workflow_id TEXT NOT NULL,
                    country TEXT NOT NULL,
                    status TEXT NOT NULL,
                    packet_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workflow_id, country)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_resolution_workflows_event
                ON resolution_workflows(event_id)
                """
            )
            connection.commit()

    def insert_workflow(
        self, record: ResolutionWorkflowRecord
    ) -> ResolutionWorkflowRecord:
        """Persist a new resolution-prep workflow."""
        created_at = record.created_at or _utc_now_iso()
        updated_at = record.updated_at or created_at
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO resolution_workflows (
                    workflow_id, normalized_key, event_id, origin_country,
                    disrupted_supplier_country, resource_type, commodity, stage,
                    country_statuses, created_at, updated_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.workflow_id,
                    record.normalized_key,
                    record.event_id,
                    record.origin_country,
                    record.disrupted_supplier_country,
                    record.resource_type,
                    record.commodity,
                    record.stage,
                    json.dumps(record.country_statuses, sort_keys=True),
                    created_at,
                    updated_at,
                    record.error_message,
                ),
            )
            connection.commit()
        return ResolutionWorkflowRecord(
            workflow_id=record.workflow_id,
            normalized_key=record.normalized_key,
            event_id=record.event_id,
            origin_country=record.origin_country,
            disrupted_supplier_country=record.disrupted_supplier_country,
            resource_type=record.resource_type,
            commodity=record.commodity,
            stage=record.stage,
            country_statuses=dict(record.country_statuses),
            created_at=created_at,
            updated_at=updated_at,
            error_message=record.error_message,
        )

    def get_workflow_by_id(self, workflow_id: str) -> ResolutionWorkflowRecord | None:
        """Return workflow by workflow id."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT workflow_id, normalized_key, event_id, origin_country,
                       disrupted_supplier_country, resource_type, commodity, stage,
                       country_statuses, created_at, updated_at, error_message
                FROM resolution_workflows
                WHERE workflow_id = ?
                """,
                (workflow_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_workflow(row)

    def get_workflow_by_normalized_key(
        self, normalized_key: str
    ) -> ResolutionWorkflowRecord | None:
        """Return workflow by normalized idempotency key."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT workflow_id, normalized_key, event_id, origin_country,
                       disrupted_supplier_country, resource_type, commodity, stage,
                       country_statuses, created_at, updated_at, error_message
                FROM resolution_workflows
                WHERE normalized_key = ?
                """,
                (normalized_key,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_workflow(row)

    def update_workflow(
        self,
        *,
        workflow_id: str,
        stage: str | None = None,
        country_statuses: Mapping[str, str] | None = None,
        error_message: str | None = None,
    ) -> ResolutionWorkflowRecord | None:
        """Update workflow stage/statuses and return latest record."""
        existing = self.get_workflow_by_id(workflow_id)
        if existing is None:
            return None

        updated_stage = stage if stage is not None else existing.stage
        updated_statuses = (
            dict(country_statuses)
            if country_statuses is not None
            else dict(existing.country_statuses)
        )
        updated_error = (
            error_message if error_message is not None else existing.error_message
        )
        updated_at = _utc_now_iso()

        with self._connection() as connection:
            connection.execute(
                """
                UPDATE resolution_workflows
                SET stage = ?, country_statuses = ?, updated_at = ?, error_message = ?
                WHERE workflow_id = ?
                """,
                (
                    updated_stage,
                    json.dumps(updated_statuses, sort_keys=True),
                    updated_at,
                    updated_error,
                    workflow_id,
                ),
            )
            connection.commit()
        return ResolutionWorkflowRecord(
            workflow_id=existing.workflow_id,
            normalized_key=existing.normalized_key,
            event_id=existing.event_id,
            origin_country=existing.origin_country,
            disrupted_supplier_country=existing.disrupted_supplier_country,
            resource_type=existing.resource_type,
            commodity=existing.commodity,
            stage=updated_stage,
            country_statuses=updated_statuses,
            created_at=existing.created_at,
            updated_at=updated_at,
            error_message=updated_error,
        )

    def upsert_packet(self, record: CountryPacketRecord) -> CountryPacketRecord:
        """Insert or update one country packet row."""
        updated_at = record.updated_at or _utc_now_iso()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO resolution_country_packets (
                    workflow_id, country, status, packet_json, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(workflow_id, country) DO UPDATE SET
                    status = excluded.status,
                    packet_json = excluded.packet_json,
                    updated_at = excluded.updated_at
                """,
                (
                    record.workflow_id,
                    record.country,
                    record.status,
                    json.dumps(record.packet_json, sort_keys=True),
                    updated_at,
                ),
            )
            connection.commit()
        return CountryPacketRecord(
            workflow_id=record.workflow_id,
            country=record.country,
            status=record.status,
            packet_json=dict(record.packet_json),
            updated_at=updated_at,
        )

    def list_packets(self, workflow_id: str) -> list[CountryPacketRecord]:
        """Return persisted packet rows for a workflow."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT workflow_id, country, status, packet_json, updated_at
                FROM resolution_country_packets
                WHERE workflow_id = ?
                """,
                (workflow_id,),
            ).fetchall()
        return [self._row_to_packet(row) for row in rows]

    @staticmethod
    def _row_to_workflow(row: Mapping[str, object]) -> ResolutionWorkflowRecord:
        def row_value(key: str, default: str) -> str:
            try:
                value = row[key]
            except Exception:
                return default
            return str(value)

        statuses_raw = row_value("country_statuses", "{}")
        return ResolutionWorkflowRecord(
            workflow_id=row_value("workflow_id", ""),
            normalized_key=row_value("normalized_key", ""),
            event_id=row_value("event_id", ""),
            origin_country=row_value("origin_country", "Singapore"),
            disrupted_supplier_country=row_value("disrupted_supplier_country", ""),
            resource_type=row_value("resource_type", ""),
            commodity=row_value("commodity", ""),
            stage=row_value("stage", "queued"),
            country_statuses=json.loads(statuses_raw),
            created_at=row_value("created_at", ""),
            updated_at=row_value("updated_at", ""),
            error_message=row_value("error_message", ""),
        )

    @staticmethod
    def _row_to_packet(row: Mapping[str, object]) -> CountryPacketRecord:
        def row_value(key: str, default: str) -> str:
            try:
                value = row[key]
            except Exception:
                return default
            return str(value)

        packet_raw = row_value("packet_json", "{}")
        return CountryPacketRecord(
            workflow_id=row_value("workflow_id", ""),
            country=row_value("country", ""),
            status=row_value("status", "queued"),
            packet_json=json.loads(packet_raw),
            updated_at=row_value("updated_at", ""),
        )
