"""
Remodax - SQLite Database Connection & Migration
Provides local SQLite storage for sessions, history, and document metadata.
SECURITY MANDATE: Never stores passwords, tokens, or API keys in SQLite.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("remodax.storage.db")


class SQLiteDatabase:
    """Manages SQLite connection and schema migrations."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self) -> None:
        """Creates database schema if tables do not exist."""
        logger.info("Inicializando esquema SQLite en %s...", self._db_path)
        with self.get_connection() as conn:
            # 1. Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    audio_source TEXT NOT NULL
                );
            """)

            # 2. Q&A History Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qa_records (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    question_text TEXT NOT NULL,
                    answer_text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ai_provider TEXT NOT NULL,
                    ai_model TEXT NOT NULL,
                    response_latency_ms REAL NOT NULL,
                    context_used INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
            """)

            # 3. Documents Metadata Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 4. User Preferences Key-Value Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            conn.commit()
            logger.info("Esquema SQLite verificado y listo.")
