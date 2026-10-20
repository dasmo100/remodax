"""
Remodax - Documents ViewModel
Bridges Document Management UI with Use Cases.
"""

import threading
from typing import List
from PySide6.QtCore import QObject, Signal
from src.application.use_cases.document_use_cases import DocumentManagementUseCase
from src.application.dtos.document_dto import DocumentSummaryDTO, DocumentImportResultDTO


class DocumentsViewModel(QObject):
    """Manages document list state, import execution, and deletions."""

    documentsLoaded = Signal(list)       # List[DocumentSummaryDTO]
    importCompleted = Signal(object)     # DocumentImportResultDTO
    documentContentReady = Signal(str, str)  # (doc_id, content)
    errorOccurred = Signal(str)

    def __init__(self, document_use_cases: DocumentManagementUseCase):
        super().__init__()
        self._document_use_cases = document_use_cases

    def load_documents(self) -> None:
        try:
            docs = self._document_use_cases.list_documents()
            self.documentsLoaded.emit(docs)
        except Exception as ex:
            self.errorOccurred.emit(f"Error cargando documentos: {str(ex)}")

    def import_document_file(self, file_path: str) -> None:
        def worker():
            try:
                result = self._document_use_cases.import_document(file_path)
                self.importCompleted.emit(result)
                if result.success:
                    self.load_documents()
                else:
                    self.errorOccurred.emit(result.error_message or "Error importando documento.")
            except Exception as ex:
                self.errorOccurred.emit(f"Error importando archivo: {str(ex)}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def delete_document(self, document_id: str) -> None:
        try:
            success = self._document_use_cases.delete_document(document_id)
            if success:
                self.load_documents()
            else:
                self.errorOccurred.emit("No se pudo eliminar el documento seleccionado.")
        except Exception as ex:
            self.errorOccurred.emit(f"Error al eliminar documento: {str(ex)}")

    def load_document_content(self, document_id: str) -> None:
        def worker():
            try:
                content = self._document_use_cases.get_document_content(document_id)
                self.documentContentReady.emit(document_id, content)
            except Exception as ex:
                self.errorOccurred.emit(f"Error al cargar contenido del documento: {str(ex)}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

