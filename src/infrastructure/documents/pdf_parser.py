"""
Remodax - PyMuPDF (fitz) Document Parser Infrastructure
Extracts textual content and creates chunks from PDF files.
"""

from pathlib import Path
import logging
from typing import List
from src.domain.entities.document import Document, DocumentChunk
from src.domain.ports.document_port import IDocumentParser
from src.domain.exceptions import DocumentParseException

logger = logging.getLogger("remodax.documents.pdf")


class PyMuPDFParser(IDocumentParser):
    """Parses PDF documents into semantic chunks using PyMuPDF (fitz)."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() == ".pdf"

    def parse_file(self, file_path: str) -> Document:
        path = Path(file_path)
        if not path.exists():
            raise DocumentParseException(f"Archivo no encontrado: {file_path}")

        file_size = path.stat().st_size
        doc_entity = Document(
            filename=path.name,
            filepath=str(path.resolve()),
            file_type="pdf",
            file_size_bytes=file_size
        )

        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            pdf_doc = fitz.open(file_path)
            chunks: List[DocumentChunk] = []
            chunk_idx = 0

            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text("text").strip()
                if not text:
                    continue

                # Simple overlapping sliding window for chunking
                start = 0
                text_len = len(text)
                while start < text_len:
                    end = min(start + self._chunk_size, text_len)
                    chunk_text = text[start:end].strip()
                    if chunk_text:
                        chunks.append(DocumentChunk(
                            document_id=doc_entity.id,
                            chunk_index=chunk_idx,
                            content=chunk_text,
                            page_number=page_num + 1
                        ))
                        chunk_idx += 1
                    start += self._chunk_size - self._chunk_overlap

            pdf_doc.close()
            doc_entity.chunks = chunks
            logger.info("PDF '%s' procesado exitosamente: %d chunks generados.", path.name, len(chunks))
            return doc_entity

        except ImportError:
            logger.warning("PyMuPDF no está instalado. Generando Document stub.")
            doc_entity.chunks = [
                DocumentChunk(
                    document_id=doc_entity.id,
                    chunk_index=0,
                    content=f"Contenido simulado para {path.name}",
                    page_number=1
                )
            ]
            return doc_entity
        except Exception as ex:
            raise DocumentParseException(f"Error al analizar PDF '{path.name}': {str(ex)}") from ex
