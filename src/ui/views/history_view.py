"""
Remodax - History View
Interface for browsing, searching, inspecting, and deleting past interview
Q&A records stored locally in SQLite.
Modernized with cyber cards, high-tech table headers, and smooth button layouts.
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QSplitter, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QTimer
from src.application.dtos.interview_dto import QuestionAnswerDTO
from src.ui.view_models.history_view_model import HistoryViewModel


class HistoryView(QWidget):
    """View for querying and inspecting local Q&A interview records."""

    def __init__(self, view_model: HistoryViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._records: List[QuestionAnswerDTO] = []

        self._init_ui()
        self._connect_signals()
        self._vm.load_recent_history()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header
        header = QHBoxLayout()
        header.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("🕒 Historial de Sesiones", self)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        desc = QLabel(
            "REGISTRO LOCAL Y AUDITORÍA DE PREGUNTAS Y RESPUESTAS GENERADAS",
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
        self._btn_refresh.clicked.connect(self._vm.load_recent_history)
        header.addWidget(self._btn_refresh)

        self._btn_clear = QPushButton("🗑️ Limpiar Todo", self)
        self._btn_clear.setProperty("class", "DangerButton")
        self._btn_clear.setFixedHeight(38)
        self._btn_clear.setMinimumWidth(130)
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear.clicked.connect(self._on_clear_clicked)
        header.addWidget(self._btn_clear)

        layout.addLayout(header)

        # 2. Search Bar
        self._search_input = QLineEdit(self)
        self._search_input.setFixedHeight(38)
        self._search_input.setPlaceholderText("🔍 Buscar por palabra clave en preguntas o respuestas...")
        self._search_input.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self._search_input)

        # 3. Main Splitter: Table (Left) + Detail Viewer (Right)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(8)

        # Table container
        tbl_container = QWidget(self)
        tbl_layout = QVBoxLayout(tbl_container)
        tbl_layout.setContentsMargins(0, 0, 0, 0)
        tbl_layout.setSpacing(10)

        self._table = QTableWidget(tbl_container)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            "Fecha/Hora", "Proveedor e IA", "Pregunta Transcrita", "Latencia"
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_row_selected)
        tbl_layout.addWidget(self._table)

        self._lbl_count = QLabel("0 registros en historial", tbl_container)
        self._lbl_count.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        tbl_layout.addWidget(self._lbl_count)

        splitter.addWidget(tbl_container)

        # Detail Inspection Card
        card_detail = QFrame(self)
        card_detail.setProperty("class", "CardFrame")
        det_layout = QVBoxLayout(card_detail)
        det_layout.setContentsMargins(18, 16, 18, 16)
        det_layout.setSpacing(10)

        det_header = QHBoxLayout()
        det_header.setSpacing(10)

        self._lbl_det_title = QLabel("Detalle de Interacción", card_detail)
        self._lbl_det_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #00d2ff;")
        det_header.addWidget(self._lbl_det_title)

        det_header.addStretch()

        self._btn_copy_answer = QPushButton("📋 Copiar", card_detail)
        self._btn_copy_answer.setProperty("class", "SecondaryButton")
        self._btn_copy_answer.setFixedHeight(32)
        self._btn_copy_answer.setMinimumWidth(90)
        self._btn_copy_answer.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_copy_answer.clicked.connect(self._copy_detail_answer)
        self._btn_copy_answer.setEnabled(False)
        det_header.addWidget(self._btn_copy_answer)

        det_layout.addLayout(det_header)

        # Metadata chip container
        meta_frame = QFrame(card_detail)
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

        self._lbl_det_meta = QLabel("Selecciona un registro para ver el contenido.", meta_frame)
        self._lbl_det_meta.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; background: transparent;")
        meta_layout.addWidget(self._lbl_det_meta)
        det_layout.addWidget(meta_frame)

        lbl_q_tag = QLabel("Pregunta Transcrita:", card_detail)
        lbl_q_tag.setStyleSheet("color: #00d2ff; font-weight: 700; font-size: 11px; margin-top: 4px;")
        det_layout.addWidget(lbl_q_tag)

        self._txt_detail_q = QTextEdit(card_detail)
        self._txt_detail_q.setReadOnly(True)
        self._txt_detail_q.setFixedHeight(80)
        self._txt_detail_q.setPlaceholderText("La pregunta aparecerá aquí...")
        self._txt_detail_q.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                line-height: 1.45;
                background-color: #060912;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        det_layout.addWidget(self._txt_detail_q)

        lbl_a_tag = QLabel("Respuesta Sugerida por IA:", card_detail)
        lbl_a_tag.setStyleSheet("color: #34d399; font-weight: 700; font-size: 11px; margin-top: 4px;")
        det_layout.addWidget(lbl_a_tag)

        self._txt_detail_a = QTextEdit(card_detail)
        self._txt_detail_a.setReadOnly(True)
        self._txt_detail_a.setPlaceholderText("La respuesta generada por la IA aparecerá aquí...")
        self._txt_detail_a.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                line-height: 1.55;
                background-color: #060912;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """)
        det_layout.addWidget(self._txt_detail_a)

        splitter.addWidget(card_detail)

        # Splitter proportion (52% table, 48% detail)
        splitter.setSizes([520, 440])
        layout.addWidget(splitter, 1)

    def _connect_signals(self) -> None:
        self._vm.historyLoaded.connect(self._render_history)
        self._vm.errorOccurred.connect(self._show_error)

    def _on_search_text_changed(self, text: str) -> None:
        self._vm.search(text.strip())

    def _render_history(self, records: List[QuestionAnswerDTO]) -> None:
        self._records = list(records)
        self._table.setRowCount(len(self._records))

        for row, r in enumerate(self._records):
            prov_model = f"{r.ai_provider} ({r.ai_model})"
            latency_str = f"{r.response_latency_ms:.0f} ms"

            self._table.setItem(row, 0, QTableWidgetItem(r.timestamp_str))
            self._table.setItem(row, 1, QTableWidgetItem(prov_model))
            self._table.setItem(row, 2, QTableWidgetItem(r.question_text))
            self._table.setItem(row, 3, QTableWidgetItem(latency_str))

        self._lbl_count.setText(f"{len(self._records)} registro(s) encontrado(s)")

        if not self._records:
            self._clear_detail()

    def _on_row_selected(self) -> None:
        row = self._table.currentRow()
        if 0 <= row < len(self._records):
            rec = self._records[row]
            self._lbl_det_title.setText(f"Interacción del {rec.timestamp_str}")
            self._lbl_det_meta.setText(
                f"Proveedor: {rec.ai_provider}  •  Modelo: {rec.ai_model}  •  Latencia: {rec.response_latency_ms:.0f} ms"
            )
            self._txt_detail_q.setPlainText(rec.question_text)
            self._txt_detail_a.setPlainText(rec.answer_text)
            self._btn_copy_answer.setEnabled(bool(rec.answer_text.strip()))
        else:
            self._clear_detail()

    def _clear_detail(self) -> None:
        self._lbl_det_title.setText("Detalle de Interacción")
        self._lbl_det_meta.setText("Selecciona un registro para ver el contenido.")
        self._txt_detail_q.clear()
        self._txt_detail_a.clear()
        self._btn_copy_answer.setEnabled(False)

    def _copy_detail_answer(self) -> None:
        text = self._txt_detail_a.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            orig_text = self._btn_copy_answer.text()
            self._btn_copy_answer.setText("✓ Copiado")
            QTimer.singleShot(1500, lambda: self._btn_copy_answer.setText(orig_text))

    def _on_clear_clicked(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Confirmar Vaciado de Historial",
            "¿Deseas eliminar permanentemente todo el historial de preguntas y respuestas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._vm.clear_history()
            self._clear_detail()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error de Historial", message)
