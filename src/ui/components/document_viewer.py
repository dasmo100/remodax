"""
Remodax - Document Viewer Component
Displays document metadata, extracted text, and semantic chunks for PDF and Word files.
Modernized with cyber card layout and refined typography.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QTimer


class DocumentViewerWidget(QWidget):
    """Visualizer component for inspecting document content and RAG chunks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Main Card container
        self._card = QFrame(self)
        self._card.setProperty("class", "CardFrame")
        c_layout = QVBoxLayout(self._card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        # Header with document title and actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self._lbl_title = QLabel("📄 Vista Previa", self._card)
        self._lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #00d2ff;")
        header_layout.addWidget(self._lbl_title)

        header_layout.addStretch()

        self._btn_copy = QPushButton("📋 Copiar", self._card)
        self._btn_copy.setProperty("class", "SecondaryButton")
        self._btn_copy.setFixedHeight(32)
        self._btn_copy.setMinimumWidth(90)
        self._btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_copy.clicked.connect(self._copy_text)
        self._btn_copy.setEnabled(False)
        header_layout.addWidget(self._btn_copy)

        c_layout.addLayout(header_layout)

        # Metadata chip container
        meta_frame = QFrame(self._card)
        meta_frame.setStyleSheet("""
            QFrame {
                background-color: #080d19;
                border: 1px solid #16223b;
                border-radius: 6px;
                padding: 4px 10px;
            }
        """)
        meta_layout = QHBoxLayout(meta_frame)
        meta_layout.setContentsMargins(6, 4, 6, 4)

        self._lbl_meta = QLabel("Ningún documento seleccionado", meta_frame)
        self._lbl_meta.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; background: transparent;")
        meta_layout.addWidget(self._lbl_meta)
        c_layout.addWidget(meta_frame)

        # Content Text Area
        self._text_area = QTextEdit(self._card)
        self._text_area.setReadOnly(True)
        self._text_area.setPlaceholderText(
            "Selecciona un archivo de la tabla para ver su contenido indexado..."
        )
        self._text_area.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 12px;
                line-height: 1.55;
                background-color: #060911;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        c_layout.addWidget(self._text_area)

        layout.addWidget(self._card)

    def display_document(
        self,
        filename: str,
        file_type: str,
        file_size: str,
        chunk_count: int,
        content: str
    ) -> None:
        """Renders document details and content."""
        self._lbl_title.setText(f"📄 {filename}")
        self._lbl_meta.setText(f"Formato: {file_type}  •  Tamaño: {file_size}  •  Fragmentos RAG: {chunk_count}")
        self._text_area.setPlainText(content)
        self._btn_copy.setEnabled(bool(content.strip()))

    def clear(self) -> None:
        """Resets visualizer to empty state."""
        self._lbl_title.setText("📄 Vista Previa")
        self._lbl_meta.setText("Ningún documento seleccionado")
        self._text_area.clear()
        self._btn_copy.setEnabled(False)

    def _copy_text(self) -> None:
        text = self._text_area.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            orig_btn_text = self._btn_copy.text()
            self._btn_copy.setText("✓ Copiado")
            QTimer.singleShot(1500, lambda: self._btn_copy.setText(orig_btn_text))
