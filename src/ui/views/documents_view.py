"""
Remodax - Documents View
Interface for uploading, listing, and deleting PDF and Word files for local RAG.
Operates completely offline and locally, preserving user privacy.
Modernized with cyber aesthetics, full-width data grid, and high-tech typography.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from src.application.dtos.document_dto import DocumentSummaryDTO
from src.ui.view_models.documents_view_model import DocumentsViewModel


class DocumentsView(QWidget):
    """View for managing documents for local RAG without preview panel."""

    def __init__(self, view_model: DocumentsViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._documents: List[DocumentSummaryDTO] = []
        self._filtered_documents: List[DocumentSummaryDTO] = []

        self._init_ui()
        self._connect_signals()
        self._vm.load_documents()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header
        header = QHBoxLayout()
        header.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("📁 Documentos de Apoyo", self)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        desc = QLabel(
            "GESTIÓN Y ANÁLISIS DE ARCHIVOS (PDF Y WORD) PARA RAG LOCAL SIN INTERNET",
            self
        )
        desc.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header.addLayout(title_box)

        header.addStretch()

        self._btn_refresh = QPushButton("🔄 Actualizar", self)
        self._btn_refresh.setProperty("class", "SecondaryButton")
        self._btn_refresh.setFixedHeight(38)
        self._btn_refresh.setMinimumWidth(120)
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.clicked.connect(self._vm.load_documents)
        header.addWidget(self._btn_refresh)

        self._btn_import = QPushButton("➕ Subir Documento", self)
        self._btn_import.setProperty("class", "PrimaryButton")
        self._btn_import.setFixedHeight(38)
        self._btn_import.setMinimumWidth(165)
        self._btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_import.clicked.connect(self._on_import_clicked)
        header.addWidget(self._btn_import)

        layout.addLayout(header)

        # 2. Main Card Container (Full-width document management)
        card = QFrame(self)
        card.setProperty("class", "CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        # Filter search bar
        self._search_input = QLineEdit(card)
        self._search_input.setFixedHeight(38)
        self._search_input.setPlaceholderText("🔍 Buscar documento por nombre o tipo...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        card_layout.addWidget(self._search_input)

        # Table of documents
        self._table = QTableWidget(card)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Archivo", "Tipo", "Tamaño", "Fecha de Incorporación", "Fragmentos (Chunks)"
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        card_layout.addWidget(self._table)

        # Table bottom action bar
        table_btn_layout = QHBoxLayout()
        table_btn_layout.setSpacing(10)

        self._lbl_count = QLabel("0 documentos listados", card)
        self._lbl_count.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        table_btn_layout.addWidget(self._lbl_count)

        table_btn_layout.addStretch()

        self._btn_delete = QPushButton("🗑️ Eliminar", card)
        self._btn_delete.setProperty("class", "DangerButton")
        self._btn_delete.setFixedHeight(34)
        self._btn_delete.setMinimumWidth(110)
        self._btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        table_btn_layout.addWidget(self._btn_delete)

        card_layout.addLayout(table_btn_layout)
        layout.addWidget(card, 1)

    def _connect_signals(self) -> None:
        self._vm.documentsLoaded.connect(self._render_documents)
        self._vm.importCompleted.connect(self._on_import_completed)
        self._vm.errorOccurred.connect(self._show_error)

    def _on_import_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Documento para RAG Local",
            "",
            "Archivos Compatibles (*.pdf *.docx *.doc);;PDF (*.pdf);;Word (*.docx *.doc)"
        )
        if file_path:
            self._vm.import_document_file(file_path)

    def _on_import_completed(self, result) -> None:
        if result.success:
            QMessageBox.information(
                self,
                "Importación Exitosa",
                f"El documento '{result.filename}' ha sido procesado e indexado exitosamente "
                f"({result.chunk_count} fragmentos semánticos para RAG)."
            )

    def _render_documents(self, documents: List[DocumentSummaryDTO]) -> None:
        self._documents = list(documents)
        self._apply_filter()

    def _on_filter_changed(self, text: str) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._search_input.text().strip().lower()
        if not query:
            self._filtered_documents = list(self._documents)
        else:
            self._filtered_documents = [
                d for d in self._documents
                if query in d.filename.lower() or query in d.file_type.lower()
            ]

        self._table.setRowCount(len(self._filtered_documents))
        for row, doc in enumerate(self._filtered_documents):
            self._table.setItem(row, 0, QTableWidgetItem(doc.filename))
            self._table.setItem(row, 1, QTableWidgetItem(doc.file_type))
            self._table.setItem(row, 2, QTableWidgetItem(doc.file_size_formatted))
            self._table.setItem(row, 3, QTableWidgetItem(doc.created_at_str))
            self._table.setItem(row, 4, QTableWidgetItem(str(doc.chunk_count)))

        self._lbl_count.setText(f"{len(self._filtered_documents)} documento(s) listado(s)")

    def _on_delete_clicked(self) -> None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._filtered_documents):
            QMessageBox.warning(self, "Selección Requerida", "Por favor selecciona un documento de la tabla.")
            return

        doc = self._filtered_documents[row]
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Deseas eliminar permanentemente '{doc.filename}' del índice local RAG?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._vm.delete_document(doc.id)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error de Documento", message)
