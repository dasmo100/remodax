"""
Remodax - Document Management & RAG Use Cases
Coordinates document parsing (PDF/Word), local private storage, and RAG indexing.
"""

from pathlib import Path
from typing import List
from src.config.constants import (
    SUPPORTED_DOCUMENT_EXTENSIONS,
    MAX_DOCUMENT_SIZE_BYTES,
)
from src.domain.exceptions import (
    UnsupportedDocumentFormatException,
    DocumentParseException,
)
from src.domain.ports.document_port import (
    IDocumentParser,
    IRAGService,
    IDocumentRepository,
)
from src.application.dtos.document_dto import (
    DocumentSummaryDTO,
    DocumentImportResultDTO,
)


class DocumentManagementUseCase:
    """Manages document import lifecycle, parsing, local indexation, and safe removal."""

    def __init__(
        self,
        parsers: List[IDocumentParser],
        rag_service: IRAGService,
        document_repo: IDocumentRepository
    ):
        self._parsers = parsers
        self._rag_service = rag_service
        self._document_repo = document_repo

    def import_document(self, file_path_str: str) -> DocumentImportResultDTO:
        path = Path(file_path_str)
        if not path.exists():
            return DocumentImportResultDTO(
                success=False,
                filename=path.name,
                error_message="El archivo especificado no existe en el disco."
            )

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
            return DocumentImportResultDTO(
                success=False,
                filename=path.name,
                error_message=f"Formato no soportado ({suffix}). Solo se admiten archivos PDF y Word (.docx)."
            )

        file_size = path.stat().st_size
        if file_size > MAX_DOCUMENT_SIZE_BYTES:
            return DocumentImportResultDTO(
                success=False,
                filename=path.name,
                error_message=f"El archivo excede el tamaño máximo permitido de 50 MB."
            )

        # Find matching parser
        parser = next((p for p in self._parsers if p.supports_extension(suffix)), None)
        if not parser:
            return DocumentImportResultDTO(
                success=False,
                filename=path.name,
                error_message="No se encontró un parser registrado para este tipo de archivo."
            )

        try:
            document = parser.parse_file(str(path))
            # Persist document metadata
            self._document_repo.save_document(document)
            # Index semantic chunks into RAG retriever
            self._rag_service.index_document(document)

            return DocumentImportResultDTO(
                success=True,
                document_id=document.id,
                filename=document.filename,
                chunk_count=document.chunk_count
            )
        except Exception as ex:
            return DocumentImportResultDTO(
                success=False,
                filename=path.name,
                error_message=f"Error durante el procesamiento del documento: {str(ex)}"
            )

    def list_documents(self) -> List[DocumentSummaryDTO]:
        docs = self._document_repo.list_documents()
        results = []
        for d in docs:
            size_kb = d.file_size_bytes / 1024
            size_formatted = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{(size_kb / 1024):.1f} MB"
            results.append(DocumentSummaryDTO(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type.upper(),
                file_size_formatted=size_formatted,
                created_at_str=d.created_at.strftime("%Y-%m-%d %H:%M"),
                chunk_count=d.chunk_count
            ))
        return results

    def delete_document(self, document_id: str) -> bool:
        self._rag_service.remove_document(document_id)
        return self._document_repo.delete_document(document_id)

    def get_document_content(self, document_id: str) -> str:
        """Retrieves textual representation and chunks of a document for previewing."""
        doc = self._document_repo.get_document(document_id)
        if not doc:
            return "Documento no encontrado."

        chunks = self._rag_service.get_document_chunks(document_id)
        if chunks:
            parts = []
            for c in chunks:
                page = f" (Pág. {c.page_number})" if c.page_number else ""
                parts.append(f"=== Fragmento #{c.chunk_index + 1}{page} ===\n{c.content.strip()}\n")
            return "\n".join(parts)

        if Path(doc.filepath).exists():
            suffix = Path(doc.filepath).suffix.lower()
            parser = next((p for p in self._parsers if p.supports_extension(suffix)), None)
            if parser:
                try:
                    parsed = parser.parse_file(doc.filepath)
                    parts = []
                    for c in parsed.chunks:
                        page = f" (Pág. {c.page_number})" if c.page_number else ""
                        parts.append(f"=== Fragmento #{c.chunk_index + 1}{page} ===\n{c.content.strip()}\n")
                    return "\n".join(parts)
                except Exception as ex:
                    return f"Error al leer contenido del archivo: {str(ex)}"

        return f"Documento: {doc.filename}\nRuta: {doc.filepath}\n(Los fragmentos se indexarán automáticamente durante la sesión)"
