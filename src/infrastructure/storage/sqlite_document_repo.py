"""
Remodax - SQLite Document Repository Infrastructure
Implements IDocumentRepository for persisting uploaded document metadata.
"""

from datetime import datetime
from typing import List, Optional
from src.domain.entities.document import Document
from src.domain.ports.document_port import IDocumentRepository
from src.infrastructure.storage.database import SQLiteDatabase


class SQLiteDocumentRepository(IDocumentRepository):
    """Stores document metadata in local SQLite."""

    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def save_document(self, document: Document) -> None:
        with self._db.get_connection() as conn:
            conn.execute("""
                INSERT INTO documents (id, filename, filepath, file_type, file_size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    filename=excluded.filename,
                    filepath=excluded.filepath,
                    file_type=excluded.file_type,
                    file_size_bytes=excluded.file_size_bytes;
            """, (
                document.id,
                document.filename,
                document.filepath,
                document.file_type,
                document.file_size_bytes,
                document.created_at.isoformat()
            ))
            conn.commit()

    def get_document(self, document_id: str) -> Optional[Document]:
        with self._db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM documents WHERE id = ?;", (document_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._map_row(row)

    def list_documents(self) -> List[Document]:
        with self._db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM documents ORDER BY created_at DESC;")
            return [self._map_row(r) for r in cur.fetchall()]

    def delete_document(self, document_id: str) -> bool:
        with self._db.get_connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = ?;", (document_id,))
            conn.commit()
            return cur.rowcount > 0

    @staticmethod
    def _map_row(row) -> Document:
        return Document(
            id=row["id"],
            filename=row["filename"],
            filepath=row["filepath"],
            file_type=row["file_type"],
            file_size_bytes=int(row["file_size_bytes"]),
            created_at=datetime.fromisoformat(row["created_at"])
        )
