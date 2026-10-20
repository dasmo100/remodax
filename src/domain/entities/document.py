"""
Remodax - Document Domain Entities
Models uploaded files (PDF, DOCX) and their vectorized/textual chunks for RAG.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class DocumentChunk:
    """Represents a discrete semantic chunk of a document for RAG indexing."""
    document_id: str
    chunk_index: int
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    relevance_score: float = 0.0
    page_number: Optional[int] = None


@dataclass
class Document:
    """Represents an imported document metadata and content units."""
    filename: str
    filepath: str
    file_type: str  # .pdf or .docx
    file_size_bytes: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    chunks: List[DocumentChunk] = field(default_factory=list)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)
