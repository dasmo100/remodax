"""
Remodax - Document Domain Ports
Abstract interfaces for document parsing (PyMuPDF, docx), RAG retrieval, and persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.document import Document, DocumentChunk


class IDocumentParser(ABC):
    """Port for extracting text and creating chunks from supported files."""

    @abstractmethod
    def parse_file(self, file_path: str) -> Document:
        """Parses PDF or DOCX file into Document entity with semantic chunks."""
        pass

    @abstractmethod
    def supports_extension(self, extension: str) -> bool:
        """Checks if parser handles the given file extension."""
        pass


class IRAGService(ABC):
    """Port for RAG indexing and similarity context retrieval."""

    @abstractmethod
    def index_document(self, document: Document) -> None:
        """Indexes document chunks into local retriever."""
        pass

    @abstractmethod
    def remove_document(self, document_id: str) -> None:
        """Removes indexed chunks associated with a document."""
        pass

    @abstractmethod
    def search_context(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """Finds most relevant document chunks for a question."""
        pass

    @abstractmethod
    def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Retrieves stored chunks for a specific document."""
        pass


class IDocumentRepository(ABC):
    """Port for persisting document metadata locally."""

    @abstractmethod
    def save_document(self, document: Document) -> None:
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Document]:
        pass

    @abstractmethod
    def list_documents(self) -> List[Document]:
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        pass
