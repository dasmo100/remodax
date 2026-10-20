"""
Remodax - Settings View (Ajustes)
Interface for hardware configuration, model preferences, and cybersecurity parameters.
Modernized with cyber card layout, generous form spacing, and sleek controls.
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QFrame, QMessageBox, QScrollArea,
    QTextEdit
)
from PySide6.QtCore import Qt
from src.config.constants import (
    PROVIDER_GROQ,
    PROVIDER_GEMINI,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    GROQ_SUPPORTED_MODELS,
    GEMINI_SUPPORTED_MODELS,
    DEFAULT_INTERVIEW_SYSTEM_PROMPT,
)
from src.application.dtos.settings_dto import SettingsDTO
from src.ui.view_models.settings_view_model import SettingsViewModel


class SettingsView(QWidget):
    """View for configuring audio, AI defaults, and security policies."""

    def __init__(self, view_model: SettingsViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._devices_data = []

        self._init_ui()
        self._connect_signals()
        self._vm.load_audio_devices()
        self._vm.load_settings()

    def _init_ui(self) -> None:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. Header
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("⚙️ Ajustes del Sistema", container)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        desc = QLabel(
            "CONFIGURACIÓN DE HARDWARE, PARÁMETROS COGNITIVOS Y PRIVACIDAD",
            container
        )
        desc.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # 2. Audio Hardware Card
        card_audio = QFrame(container)
        card_audio.setProperty("class", "CardFrame")
        layout_audio = QVBoxLayout(card_audio)
        layout_audio.setContentsMargins(22, 18, 22, 18)
        layout_audio.setSpacing(14)

        lbl_aud = QLabel("🎙️ Audio y Micrófono", card_audio)
        lbl_aud.setStyleSheet("color: #00d2ff; font-size: 15px; font-weight: 800; letter-spacing: 0.3px;")
        layout_audio.addWidget(lbl_aud)

        row_aud1 = QHBoxLayout()
        lbl_aud_src = QLabel("Fuente de Entrada:", card_audio)
        lbl_aud_src.setMinimumWidth(190)
        lbl_aud_src.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        row_aud1.addWidget(lbl_aud_src)
        self._combo_audio_source = QComboBox(card_audio)
        self._combo_audio_source.addItems(["Audio de la Reunión (Zoom / Meet / Sistema)", "Micrófono"])
        self._combo_audio_source.setMinimumWidth(320)
        self._combo_audio_source.setFixedHeight(36)
        row_aud1.addWidget(self._combo_audio_source)
        row_aud1.addStretch()
        layout_audio.addLayout(row_aud1)

        row_aud2 = QHBoxLayout()
        lbl_aud_dev = QLabel("Dispositivo de Captura:", card_audio)
        lbl_aud_dev.setMinimumWidth(190)
        lbl_aud_dev.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        row_aud2.addWidget(lbl_aud_dev)
        self._combo_devices = QComboBox(card_audio)
        self._combo_devices.setMinimumWidth(380)
        self._combo_devices.setFixedHeight(36)
        row_aud2.addWidget(self._combo_devices)
        row_aud2.addStretch()
        layout_audio.addLayout(row_aud2)

        row_aud3 = QHBoxLayout()
        lbl_aud_whi = QLabel("Modelo de Whisper:", card_audio)
        lbl_aud_whi.setMinimumWidth(190)
        lbl_aud_whi.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        row_aud3.addWidget(lbl_aud_whi)
        self._combo_whisper = QComboBox(card_audio)
        self._combo_whisper.addItems([
            "whisper-large-v3-turbo (Groq / Nube Ultrarrápido)",
            "base (Local / CPU)",
            "small (Local / Precisión)",
            "tiny (Local / Ligero)"
        ])
        self._combo_whisper.setMinimumWidth(320)
        self._combo_whisper.setFixedHeight(36)
        row_aud3.addWidget(self._combo_whisper)
        row_aud3.addStretch()
        layout_audio.addLayout(row_aud3)

        layout.addWidget(card_audio)

        # 3. AI & Models Default Card
        card_ai = QFrame(container)
        card_ai.setProperty("class", "CardFrame")
        layout_ai = QVBoxLayout(card_ai)
        layout_ai.setContentsMargins(22, 18, 22, 18)
        layout_ai.setSpacing(14)

        lbl_ai = QLabel("🤖 Inteligencia Artificial", card_ai)
        lbl_ai.setStyleSheet("color: #34d399; font-size: 15px; font-weight: 800; letter-spacing: 0.3px;")
        layout_ai.addWidget(lbl_ai)

        row_ai1 = QHBoxLayout()
        lbl_prov = QLabel("Proveedor Predeterminado:", card_ai)
        lbl_prov.setMinimumWidth(190)
        lbl_prov.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        row_ai1.addWidget(lbl_prov)
        self._combo_default_provider = QComboBox(card_ai)
        self._combo_default_provider.addItems([PROVIDER_GROQ, PROVIDER_GEMINI])
        self._combo_default_provider.setMinimumWidth(320)
        self._combo_default_provider.setFixedHeight(36)
        self._combo_default_provider.currentTextChanged.connect(self._on_default_provider_changed)
        row_ai1.addWidget(self._combo_default_provider)
        row_ai1.addStretch()
        layout_ai.addLayout(row_ai1)

        row_ai_model = QHBoxLayout()
        lbl_mod = QLabel("Modelo Predeterminado:", card_ai)
        lbl_mod.setMinimumWidth(190)
        lbl_mod.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        row_ai_model.addWidget(lbl_mod)
        self._combo_default_model = QComboBox(card_ai)
        self._combo_default_model.addItems(GROQ_SUPPORTED_MODELS)
        self._combo_default_model.setMinimumWidth(320)
        self._combo_default_model.setFixedHeight(36)
        row_ai_model.addWidget(self._combo_default_model)
        row_ai_model.addStretch()
        layout_ai.addLayout(row_ai_model)

        row_ai2 = QHBoxLayout()
        self._chk_rag_default = QCheckBox(
            "Activar documentos de apoyo (RAG) por defecto al iniciar",
            card_ai
        )
        self._chk_rag_default.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: 500;")
        row_ai2.addWidget(self._chk_rag_default)
        row_ai2.addStretch()
        layout_ai.addLayout(row_ai2)

        # Prompt customization section
        lbl_prompt_title = QLabel("Instrucciones de Respuesta (Prompt del Asistente):", card_ai)
        lbl_prompt_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 700; margin-top: 6px;")
        layout_ai.addWidget(lbl_prompt_title)

        self._text_system_prompt = QTextEdit(card_ai)
        self._text_system_prompt.setFixedHeight(105)
        self._text_system_prompt.setPlaceholderText("Instrucciones para guiar las respuestas de la IA...")
        self._text_system_prompt.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, 'Cascadia Code', monospace;
                font-size: 12px;
                line-height: 1.45;
                background-color: #060912;
                border: 1px solid #18253e;
                border-radius: 8px;
                padding: 10px;
                color: #f1f5f9;
            }
        """)
        layout_ai.addWidget(self._text_system_prompt)

        row_prompt_btn = QHBoxLayout()
        row_prompt_btn.addStretch()
        self._btn_reset_prompt = QPushButton("🔄 Restablecer a Modo Hablado Breve (Predeterminado)", card_ai)
        self._btn_reset_prompt.setProperty("class", "SecondaryButton")
        self._btn_reset_prompt.setFixedHeight(34)
        self._btn_reset_prompt.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reset_prompt.clicked.connect(self._reset_prompt_to_default)
        row_prompt_btn.addWidget(self._btn_reset_prompt)
        layout_ai.addLayout(row_prompt_btn)

        layout.addWidget(card_ai)

        # 4. Privacy Invariants Card
        card_privacy = QFrame(container)
        card_privacy.setProperty("class", "CardFrame")
        layout_priv = QVBoxLayout(card_privacy)
        layout_priv.setContentsMargins(22, 16, 22, 16)
        layout_priv.setSpacing(10)

        lbl_priv = QLabel("🔒 Privacidad y Seguridad", card_privacy)
        lbl_priv.setStyleSheet("color: #00d2ff; font-size: 15px; font-weight: 800; letter-spacing: 0.3px;")
        layout_priv.addWidget(lbl_priv)

        self._chk_zero_audio = QCheckBox(
            "Procesar audio 100% en memoria RAM (Sin guardar archivos temporales en disco)",
            card_privacy
        )
        self._chk_zero_audio.setChecked(True)
        self._chk_zero_audio.setEnabled(False)
        self._chk_zero_audio.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        layout_priv.addWidget(self._chk_zero_audio)

        layout.addWidget(card_privacy)

        # 5. Save Button Bar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_save = QPushButton("💾 Guardar Ajustes", container)
        self._btn_save.setProperty("class", "PrimaryButton")
        self._btn_save.setFixedHeight(42)
        self._btn_save.setMinimumWidth(190)
        self._btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._btn_save)
        layout.addLayout(btn_layout)

        layout.addStretch()

        scroll_area.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self._vm.settingsLoaded.connect(self._render_settings)
        self._vm.devicesLoaded.connect(self._render_devices)
        self._vm.settingsSaved.connect(self._on_saved_confirmation)
        self._vm.errorOccurred.connect(self._show_error)

    def _render_devices(self, devices: List) -> None:
        self._devices_data = devices
        self._combo_devices.clear()
        self._combo_devices.addItem("Dispositivo Predeterminado de Windows (-1)", -1)
        for dev in devices:
            tag = "[Loopback]" if dev.is_loopback else "[Micrófono]"
            self._combo_devices.addItem(f"{tag} {dev.name}", dev.index)

    def _render_settings(self, settings: SettingsDTO) -> None:
        self._combo_audio_source.setCurrentText(settings.audio_source)
        idx = self._combo_devices.findData(settings.audio_device_index)
        if idx >= 0:
            self._combo_devices.setCurrentIndex(idx)

        # Map whisper model
        whisper_clean = settings.whisper_model.lower()
        for i in range(self._combo_whisper.count()):
            if whisper_clean in self._combo_whisper.itemText(i).lower():
                self._combo_whisper.setCurrentIndex(i)
                break

        self._combo_default_provider.setCurrentText(settings.active_provider)
        self._update_default_models(settings.active_provider)
        if settings.active_model:
            idx_mod = self._combo_default_model.findText(settings.active_model)
            if idx_mod >= 0:
                self._combo_default_model.setCurrentIndex(idx_mod)
        self._chk_rag_default.setChecked(settings.allow_external_rag)

        # Set system prompt in editor
        prompt_val = settings.system_prompt if settings.system_prompt else DEFAULT_INTERVIEW_SYSTEM_PROMPT
        self._text_system_prompt.setPlainText(prompt_val)

    def _reset_prompt_to_default(self) -> None:
        self._text_system_prompt.setPlainText(DEFAULT_INTERVIEW_SYSTEM_PROMPT)

    def _on_default_provider_changed(self, provider: str) -> None:
        self._update_default_models(provider)

    def _update_default_models(self, provider: str) -> None:
        self._combo_default_model.clear()
        if provider == PROVIDER_GROQ:
            self._combo_default_model.addItems(GROQ_SUPPORTED_MODELS)
        else:
            self._combo_default_model.addItems(GEMINI_SUPPORTED_MODELS)

    def _on_save_clicked(self) -> None:
        selected_dev_index = self._combo_devices.currentData()

        # Extract base model name e.g. "base" from "base (Recomendado)"
        whisper_text = self._combo_whisper.currentText().split()[0].lower()
        prompt_text = self._text_system_prompt.toPlainText().strip() or DEFAULT_INTERVIEW_SYSTEM_PROMPT

        dto = SettingsDTO(
            active_provider=self._combo_default_provider.currentText(),
            active_model=self._combo_default_model.currentText(),
            audio_source=self._combo_audio_source.currentText(),
            audio_device_index=selected_dev_index if selected_dev_index is not None else -1,
            whisper_model=whisper_text,
            allow_external_rag=self._chk_rag_default.isChecked(),
            persist_audio=False,
            dark_mode=True,
            system_prompt=prompt_text
        )
        self._vm.save_settings(dto)

    def _on_saved_confirmation(self) -> None:
        QMessageBox.information(self, "Ajustes Guardados", "Las preferencias del sistema se han guardado exitosamente.")

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error de Ajustes", message)
