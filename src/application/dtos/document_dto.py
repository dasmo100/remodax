"""
Remodax - Document DTOs
Data Transfer Objects for document management and status display.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentSummaryDTO:
    id: str
    filename: str
    file_type: str
    file_size_formatted: str
    created_at_str: str
    chunk_count: int


@dataclass
class DocumentImportResultDTO:
    success: bool
    document_id: Optional[str] = None
    filename: str = ""
    chunk_count: int = 0
    error_message: Optional[str] = None
