"""Database connection placeholders."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: str = "backend.db") -> sqlite3.Connection:
    """Return a SQLite connection for local development."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
