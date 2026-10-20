"""
Remodax - python-docx Document Parser Infrastructure
Extracts textual content and creates chunks from Microsoft Word (.docx) files.
"""

from pathlib import Path
import logging
from typing import List
from src.domain.entities.document import Document, DocumentChunk
from src.domain.ports.document_port import IDocumentParser
from src.domain.exceptions import DocumentParseException

logger = logging.getLogger("remodax.documents.docx")


class DocxParser(IDocumentParser):
    """Parses Word (.docx) documents into semantic chunks using python-docx."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in [".docx", ".doc"]

    def parse_file(self, file_path: str) -> Document:
        path = Path(file_path)
        if not path.exists():
            raise DocumentParseException(f"Archivo no encontrado: {file_path}")

        file_size = path.stat().st_size
        doc_entity = Document(
            filename=path.name,
            filepath=str(path.resolve()),
            file_type="docx",
            file_size_bytes=file_size
        )

        try:
            from docx import Document as DocxReader
            docx = DocxReader(file_path)
            full_text = "\n".join([p.text for p in docx.paragraphs if p.text.strip()])

            chunks: List[DocumentChunk] = []
            chunk_idx = 0
            start = 0
            text_len = len(full_text)

            while start < text_len:
                end = min(start + self._chunk_size, text_len)
                chunk_text = full_text[start:end].strip()
                if chunk_text:
                    chunks.append(DocumentChunk(
                        document_id=doc_entity.id,
                        chunk_index=chunk_idx,
                        content=chunk_text
                    ))
                    chunk_idx += 1
                start += self._chunk_size - self._chunk_overlap

            doc_entity.chunks = chunks
            logger.info("Docx '%s' procesado exitosamente: %d chunks generados.", path.name, len(chunks))
            return doc_entity

        except ImportError:
            logger.warning("python-docx no está instalado. Generando Document stub.")
            doc_entity.chunks = [
                DocumentChunk(
                    document_id=doc_entity.id,
                    chunk_index=0,
                    content=f"Contenido simulado para Word {path.name}"
                )
            ]
            return doc_entity
        except Exception as ex:
            raise DocumentParseException(f"Error al analizar DOCX '{path.name}': {str(ex)}") from ex
