"""
Remodax - Interview View
Modern, futuristic interface for real-time interview transcription and AI answers.
Designed for ease of use: intuitive controls, generous spacing, and low cognitive load.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QCheckBox, QFrame, QSplitter,
    QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from src.config.constants import (
    PROVIDER_GROQ,
    PROVIDER_GEMINI,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    GROQ_SUPPORTED_MODELS,
    GEMINI_SUPPORTED_MODELS,
)
from src.ui.components.status_badge import StatusBadge
from src.ui.components.audio_meter import AudioLevelMeter
from src.ui.view_models.interview_view_model import InterviewViewModel
from src.domain.services.question_detector import QuestionDetector


class InterviewView(QWidget):
    """Clean, high-tech view for live interview assistance."""

    def __init__(self, view_model: InterviewViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._is_active = False

        self._init_ui()
        self._connect_signals()
        self._apply_initial_preferences()

    def _apply_initial_preferences(self) -> None:
        """Applies stored user preferences (provider, model, RAG) on initial view load."""
        settings = self._vm.get_user_settings()
        if not settings:
            return
        if settings.active_provider:
            self._combo_provider.setCurrentText(settings.active_provider)
            self._on_provider_changed(settings.active_provider)
            if settings.active_model:
                idx = self._combo_model.findText(settings.active_model)
                if idx >= 0:
                    self._combo_model.setCurrentIndex(idx)
        self._chk_rag_consent.setChecked(settings.allow_external_rag)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Top Header Bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title = QLabel("🎙️ Entrevista", self)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        title_row.addWidget(title)

        self._status_badge = StatusBadge("Listo", "success", self)
        self._conn_badge = self._status_badge
        self._audio_badge = self._status_badge
        title_row.addWidget(self._status_badge)
        title_row.addStretch()
        title_box.addLayout(title_row)

        subtitle = QLabel("ASISTENCIA COGNITIVA EN TIEMPO REAL & RAG LOCAL", self)
        subtitle.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        title_box.addWidget(subtitle)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Big Hero Recording toggle button
        self._btn_session_toggle = QPushButton("🎙️ Iniciar Grabación", self)
        self._btn_session_toggle.setProperty("class", "PrimaryButton")
        self._btn_session_toggle.setFixedHeight(42)
        self._btn_session_toggle.setMinimumWidth(185)
        self._btn_session_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_session_toggle.clicked.connect(self._toggle_session)
        header_layout.addWidget(self._btn_session_toggle)

        main_layout.addLayout(header_layout)

        # 2. Control Toolbar Card
        toolbar_card = QFrame(self)
        toolbar_card.setProperty("class", "ToolbarCard")
        tb_layout = QHBoxLayout(toolbar_card)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(12)

        # Audio VU meter
        self._audio_meter = AudioLevelMeter(toolbar_card)
        tb_layout.addWidget(self._audio_meter)

        # Separator
        sep1 = QFrame(toolbar_card)
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background-color: #1a2742; max-width: 1px; border: none; margin: 4px 2px;")
        tb_layout.addWidget(sep1)

        # AI Provider Selection
        lbl_prov = QLabel("IA:", toolbar_card)
        lbl_prov.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        tb_layout.addWidget(lbl_prov)

        self._combo_provider = QComboBox(toolbar_card)
        self._combo_provider.addItems([PROVIDER_GROQ, PROVIDER_GEMINI])
        self._combo_provider.setMinimumWidth(140)
        self._combo_provider.setFixedHeight(34)
        self._combo_provider.currentTextChanged.connect(self._on_provider_changed)
        tb_layout.addWidget(self._combo_provider)

        # Model Selection
        lbl_mod = QLabel("Modelo:", toolbar_card)
        lbl_mod.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        tb_layout.addWidget(lbl_mod)

        self._combo_model = QComboBox(toolbar_card)
        self._combo_model.addItems(GROQ_SUPPORTED_MODELS)
        self._combo_model.setMinimumWidth(225)
        self._combo_model.setFixedHeight(34)
        tb_layout.addWidget(self._combo_model)

        tb_layout.addStretch()

        # RAG toggle
        self._chk_rag_consent = QCheckBox("Usar Documentos (RAG)", toolbar_card)
        self._chk_rag_consent.setToolTip("Consulta tus documentos PDF y Word para enriquecer las respuestas de la IA sin inventar datos.")
        self._chk_rag_consent.setStyleSheet("color: #00d2ff; font-weight: 600; font-size: 12px;")
        tb_layout.addWidget(self._chk_rag_consent)

        main_layout.addWidget(toolbar_card)

        # 3. Workspaces Splitter: Question (Top) & Answer (Bottom)
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setHandleWidth(8)

        # --- Question Card ---
        card_question = QFrame(self)
        card_question.setProperty("class", "CardFrame")
        layout_q = QVBoxLayout(card_question)
        layout_q.setContentsMargins(18, 14, 18, 14)
        layout_q.setSpacing(10)

        q_header = QHBoxLayout()
        q_header.setSpacing(8)

        lbl_q_dot = QLabel("●", card_question)
        lbl_q_dot.setStyleSheet("color: #00d2ff; font-size: 11px; background: transparent;")
        q_header.addWidget(lbl_q_dot)

        lbl_q_title = QLabel("Tu Pregunta", card_question)
        lbl_q_title.setStyleSheet("font-weight: 700; color: #00d2ff; font-size: 14px; letter-spacing: 0.3px;")
        q_header.addWidget(lbl_q_title)

        lbl_q_sub = QLabel("•  Entrada de voz o texto", card_question)
        lbl_q_sub.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        q_header.addWidget(lbl_q_sub)

        q_header.addStretch()

        self._btn_clear_q = QPushButton("Limpiar", card_question)
        self._btn_clear_q.setProperty("class", "SecondaryButton")
        self._btn_clear_q.setFixedHeight(32)
        self._btn_clear_q.setMinimumWidth(85)
        self._btn_clear_q.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear_q.clicked.connect(self._clear_question)
        q_header.addWidget(self._btn_clear_q)

        self._btn_generate = QPushButton("⚡ Generar Respuesta", card_question)
        self._btn_generate.setProperty("class", "PrimaryButton")
        self._btn_generate.setFixedHeight(32)
        self._btn_generate.setMinimumWidth(180)
        self._btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_generate.clicked.connect(self._on_generate_clicked)
        q_header.addWidget(self._btn_generate)

        layout_q.addLayout(q_header)

        self._text_question = QTextEdit(card_question)
        self._text_question.setPlaceholderText(
            "Habla para transcribir automáticamente con el micrófono o escribe tu pregunta aquí..."
        )
        self._text_question.setMinimumHeight(75)
        self._text_question.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                line-height: 1.45;
                background-color: #060912;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 10px;
                color: #f1f5f9;
            }
        """)
        layout_q.addWidget(self._text_question)

        splitter.addWidget(card_question)

        # --- Answer Card ---
        card_answer = QFrame(self)
        card_answer.setProperty("class", "CardFrame")
        layout_a = QVBoxLayout(card_answer)
        layout_a.setContentsMargins(18, 14, 18, 14)
        layout_a.setSpacing(10)

        a_header = QHBoxLayout()
        a_header.setSpacing(8)

        lbl_a_dot = QLabel("●", card_answer)
        lbl_a_dot.setStyleSheet("color: #34d399; font-size: 11px; background: transparent;")
        a_header.addWidget(lbl_a_dot)

        lbl_a_title = QLabel("Respuesta de la IA", card_answer)
        lbl_a_title.setStyleSheet("font-weight: 700; color: #34d399; font-size: 14px; letter-spacing: 0.3px;")
        a_header.addWidget(lbl_a_title)

        lbl_a_sub = QLabel("•  Asistencia en tiempo real", card_answer)
        lbl_a_sub.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        a_header.addWidget(lbl_a_sub)

        a_header.addStretch()

        self._btn_copy_a = QPushButton("📋 Copiar", card_answer)
        self._btn_copy_a.setProperty("class", "SecondaryButton")
        self._btn_copy_a.setFixedHeight(32)
        self._btn_copy_a.setMinimumWidth(95)
        self._btn_copy_a.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_copy_a.clicked.connect(self._copy_answer)
        a_header.addWidget(self._btn_copy_a)

        self._btn_clear_a = QPushButton("Limpiar", card_answer)
        self._btn_clear_a.setProperty("class", "SecondaryButton")
        self._btn_clear_a.setFixedHeight(32)
        self._btn_clear_a.setMinimumWidth(85)
        self._btn_clear_a.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear_a.clicked.connect(self._clear_answer)
        a_header.addWidget(self._btn_clear_a)

        layout_a.addLayout(a_header)

        self._text_answer = QTextEdit(card_answer)
        self._text_answer.setReadOnly(True)
        self._text_answer.setPlaceholderText(
            "La respuesta de la IA aparecerá aquí en tiempo real con alta precisión..."
        )
        self._text_answer.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                line-height: 1.55;
                background-color: #060912;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 12px;
                color: #f8fafc;
            }
        """)
        layout_a.addWidget(self._text_answer)

        splitter.addWidget(card_answer)

        splitter.setSizes([160, 360])
        main_layout.addWidget(splitter, 1)

        # 4. Minimal Futuristic Footer
        footer_layout = QHBoxLayout()
        self._lbl_system_status = QLabel("Listo para grabar o consultar.", self)
        self._lbl_system_status.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        footer_layout.addWidget(self._lbl_system_status)

        footer_layout.addStretch()

        privacy_tag = QLabel("🔒 Privado • Procesado 100% en memoria", self)
        privacy_tag.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        footer_layout.addWidget(privacy_tag)

        main_layout.addLayout(footer_layout)

    def _connect_signals(self) -> None:
        self._vm.sessionStatusChanged.connect(self._on_session_status_changed)
        self._vm.transcriptionReceived.connect(self._on_transcription_received)
        self._vm.answerChunkReceived.connect(self._on_answer_chunk_received)
        self._vm.answerCompleted.connect(self._on_answer_completed)
        self._vm.errorOccurred.connect(self._on_error)

    def _toggle_session(self) -> None:
        if not self._is_active:
            self._vm.start_interview("Sesión Activa")
        else:
            self._vm.stop_interview()

    def _on_session_status_changed(self, is_active: bool, message: str) -> None:
        self._is_active = is_active
        self._audio_meter.set_active(is_active)
        if is_active:
            self._btn_session_toggle.setText("⏹️ Detener Grabación")
            self._btn_session_toggle.setProperty("class", "DangerButton")
            self._status_badge.set_status("Grabando", "danger")
            self._lbl_system_status.setText("Escuchando audio... Esperando pregunta...")
        else:
            self._btn_session_toggle.setText("🎙️ Iniciar Grabación")
            self._btn_session_toggle.setProperty("class", "PrimaryButton")
            self._status_badge.set_status("Listo", "success")
            self._lbl_system_status.setText("Grabación detenida.")

        self._btn_session_toggle.style().unpolish(self._btn_session_toggle)
        self._btn_session_toggle.style().polish(self._btn_session_toggle)

    def _on_provider_changed(self, provider: str) -> None:
        self._combo_model.clear()
        if provider == PROVIDER_GROQ:
            self._combo_model.addItems(GROQ_SUPPORTED_MODELS)
        else:
            self._combo_model.addItems(GEMINI_SUPPORTED_MODELS)

    def _on_generate_clicked(self) -> None:
        question = self._text_question.toPlainText().strip()
        if not question:
            QMessageBox.information(
                self,
                "Pregunta Requerida",
                "Escribe o di una pregunta antes de generar la respuesta."
            )
            return

        self._text_answer.clear()
        self._status_badge.set_status("Generando...", "warning")
        self._lbl_system_status.setText("Generando respuesta de IA...")

        self._vm.ask_ai_question(
            question=question,
            provider=self._combo_provider.currentText(),
            model=self._combo_model.currentText(),
            allow_external_rag=self._chk_rag_consent.isChecked(),
            force=True
        )

    def _on_transcription_received(self, text: str) -> None:
        clean_text = text.strip()
        if not clean_text:
            return

        # Always update the question box so the user immediately sees what was transcribed
        self._text_question.setPlainText(clean_text)

        # 1. Semantic Filter: Validate if transcription is a substantive question or interview topic
        is_question, reason = QuestionDetector.is_valid_question(clean_text)
        if not is_question:
            # Inform user of ambient/greeting detection without wiping any active response
            self._lbl_system_status.setText(f"Intervención: '{clean_text}' ({reason})")
            return

        # 2. Register accepted question in deduplication cache
        QuestionDetector.record_accepted_question(clean_text)

        # 3. Legitimate question detected -> generate answer immediately via Groq
        provider = PROVIDER_GROQ
        current_ui_model = self._combo_model.currentText()
        if self._combo_provider.currentText() == PROVIDER_GROQ and current_ui_model in GROQ_SUPPORTED_MODELS:
            model = current_ui_model
        else:
            model = DEFAULT_GROQ_MODEL

        short_q = (clean_text[:42] + "...") if len(clean_text) > 42 else clean_text
        self._lbl_system_status.setText(f"⚡ Pregunta: '{short_q}' • Generando con {model}...")
        self._text_answer.clear()
        self._status_badge.set_status("Generando...", "warning")

        self._vm.ask_ai_question(
            question=clean_text,
            provider=provider,
            model=model,
            allow_external_rag=self._chk_rag_consent.isChecked()
        )

    def _on_answer_chunk_received(self, chunk: str) -> None:
        self._text_answer.insertPlainText(chunk)
        cursor = self._text_answer.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._text_answer.setTextCursor(cursor)

    def _on_answer_completed(self, full_text: str) -> None:
        self._status_badge.set_status("Listo", "success")
        self._lbl_system_status.setText("Respuesta completada.")

    def _on_error(self, message: str) -> None:
        self._status_badge.set_status("Aviso", "warning")
        self._text_answer.append(f"\n[Aviso]: {message}")
        self._lbl_system_status.setText(message)

    def _clear_question(self) -> None:
        self._text_question.clear()

    def _clear_answer(self) -> None:
        self._text_answer.clear()

    def _copy_answer(self) -> None:
        text = self._text_answer.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            orig_text = self._btn_copy_a.text()
            self._btn_copy_a.setText("✓ Copiado")
            QTimer.singleShot(1500, lambda: self._btn_copy_a.setText(orig_text))
