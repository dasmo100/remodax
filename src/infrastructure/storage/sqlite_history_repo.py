"""
Remodax - SQLite History Repository Infrastructure
Implements IHistoryRepository for sessions and Q&A history storage.
"""

from datetime import datetime
from typing import List, Optional
from src.domain.entities.interview import InterviewSession, QuestionAnswer
from src.domain.ports.storage_port import IHistoryRepository
from src.infrastructure.storage.database import SQLiteDatabase


class SQLiteHistoryRepository(IHistoryRepository):
    """Persistence implementation for interview sessions and Q&A pairs."""

    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def save_session(self, session: InterviewSession) -> None:
        with self._db.get_connection() as conn:
            conn.execute("""
                INSERT INTO sessions (id, title, started_at, ended_at, audio_source)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    ended_at=excluded.ended_at,
                    audio_source=excluded.audio_source;
            """, (
                session.id,
                session.title,
                session.started_at.isoformat(),
                session.ended_at.isoformat() if session.ended_at else None,
                session.audio_source
            ))
            conn.commit()

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        with self._db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM sessions WHERE id = ?;", (session_id,))
            row = cur.fetchone()
            if not row:
                return None

            session = InterviewSession(
                id=row["id"],
                title=row["title"],
                started_at=datetime.fromisoformat(row["started_at"]),
                ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                audio_source=row["audio_source"]
            )

            # Fetch associated QAs
            qa_cur = conn.execute("SELECT * FROM qa_records WHERE session_id = ? ORDER BY timestamp ASC;", (session_id,))
            for q_row in qa_cur.fetchall():
                session.add_qa(self._map_qa_row(q_row))

            return session

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[InterviewSession]:
        with self._db.get_connection() as conn:
            cur = conn.execute("""
                SELECT * FROM sessions ORDER BY started_at DESC LIMIT ? OFFSET ?;
            """, (limit, offset))
            sessions = []
            for row in cur.fetchall():
                s = InterviewSession(
                    id=row["id"],
                    title=row["title"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                    audio_source=row["audio_source"]
                )
                sessions.append(s)
            return sessions

    def save_qa(self, qa: QuestionAnswer) -> None:
        with self._db.get_connection() as conn:
            # Prevent FOREIGN KEY constraint failed if session does not exist in DB
            sid = qa.session_id
            if sid:
                cur = conn.execute("SELECT id FROM sessions WHERE id = ?;", (sid,))
                if not cur.fetchone():
                    sid = None

            conn.execute("""
                INSERT INTO qa_records (
                    id, session_id, question_text, answer_text, timestamp,
                    ai_provider, ai_model, response_latency_ms, context_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                qa.id,
                sid,
                qa.question_text,
                qa.answer_text,
                qa.timestamp.isoformat(),
                qa.ai_provider,
                qa.ai_model,
                qa.response_latency_ms,
                1 if qa.context_used else 0
            ))
            conn.commit()

    def search_history(self, query: str) -> List[QuestionAnswer]:
        with self._db.get_connection() as conn:
            pattern = f"%{query}%"
            cur = conn.execute("""
                SELECT * FROM qa_records
                WHERE question_text LIKE ? OR answer_text LIKE ?
                ORDER BY timestamp DESC LIMIT 50;
            """, (pattern, pattern))
            return [self._map_qa_row(row) for row in cur.fetchall()]

    def delete_session(self, session_id: str) -> bool:
        with self._db.get_connection() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE id = ?;", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear_all_history(self) -> bool:
        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM qa_records;")
            conn.execute("DELETE FROM sessions;")
            conn.commit()
            return True

    @staticmethod
    def _map_qa_row(row) -> QuestionAnswer:
        return QuestionAnswer(
            id=row["id"],
            session_id=row["session_id"],
            question_text=row["question_text"],
            answer_text=row["answer_text"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            ai_provider=row["ai_provider"],
            ai_model=row["ai_model"],
            response_latency_ms=float(row["response_latency_ms"]),
            context_used=bool(row["context_used"])
        )
