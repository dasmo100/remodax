"""
Remodax - API Keys View
Interface for selecting Groq or Gemini, entering API keys, securely storing
credentials in Windows Credential Manager, and testing provider connection.
Enforces cybersecurity: zero cleartext keys in disk, logs, or SQLite.
Modernized with cyber vault aesthetics and premium styling.
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from src.config.constants import (
    PROVIDER_GROQ,
    PROVIDER_GEMINI,
    GROQ_SUPPORTED_MODELS,
    GEMINI_SUPPORTED_MODELS,
)
from src.application.dtos.api_key_dto import ApiKeyStatusDTO
from src.ui.components.masked_input import MaskedKeyInput
from src.ui.components.status_badge import StatusBadge
from src.ui.view_models.api_keys_view_model import ApiKeysViewModel


class ApiKeysView(QWidget):
    """View for configuring AI provider credentials securely."""

    def __init__(self, view_model: ApiKeysViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._statuses: dict[str, ApiKeyStatusDTO] = {}
        self._current_selected_provider = PROVIDER_GROQ

        self._init_ui()
        self._connect_signals()
        self._vm.load_keys_status()

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

        title = QLabel("🔑 Claves de Inteligencia Artificial", container)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        desc = QLabel(
            "GESTIÓN SEGURA DE CREDENCIALES EN CRIPTOGRAFÍA LOCAL (WINDOWS VAULT)",
            container
        )
        desc.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # 2. Provider Selector Card
        selector_card = QFrame(container)
        selector_card.setProperty("class", "CardFrame")
        sel_layout = QHBoxLayout(selector_card)
        sel_layout.setContentsMargins(18, 14, 18, 14)
        sel_layout.setSpacing(12)

        lbl_prov = QLabel("PROVEEDOR ACTIVO:", selector_card)
        lbl_prov.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 11px; letter-spacing: 0.8px;")
        sel_layout.addWidget(lbl_prov)

        self._btn_select_groq = QPushButton("⚡ GroqCloud (Ultra-rápido)", selector_card)
        self._btn_select_groq.setProperty("class", "PrimaryButton")
        self._btn_select_groq.setCheckable(True)
        self._btn_select_groq.setChecked(True)
        self._btn_select_groq.setFixedHeight(38)
        self._btn_select_groq.setMinimumWidth(210)
        self._btn_select_groq.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_select_groq.clicked.connect(lambda: self._on_provider_selected(PROVIDER_GROQ))
        sel_layout.addWidget(self._btn_select_groq)

        self._btn_select_gemini = QPushButton("✨ Google Gemini", selector_card)
        self._btn_select_gemini.setProperty("class", "SecondaryButton")
        self._btn_select_gemini.setCheckable(True)
        self._btn_select_gemini.setFixedHeight(38)
        self._btn_select_gemini.setMinimumWidth(180)
        self._btn_select_gemini.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_select_gemini.clicked.connect(lambda: self._on_provider_selected(PROVIDER_GEMINI))
        sel_layout.addWidget(self._btn_select_gemini)

        sel_layout.addStretch()
        layout.addWidget(selector_card)

        # 3. Active Configuration Card (Vault Aesthetic)
        self._active_card = QFrame(container)
        self._active_card.setProperty("class", "CardFrame")
        act_layout = QVBoxLayout(self._active_card)
        act_layout.setContentsMargins(22, 20, 22, 20)
        act_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self._lbl_active_name = QLabel("⚡ GroqCloud", self._active_card)
        self._lbl_active_name.setStyleSheet("font-size: 17px; font-weight: 800; color: #00d2ff; letter-spacing: 0.3px;")
        top_row.addWidget(self._lbl_active_name)

        self._lbl_active_models = QLabel(f"({', '.join(GROQ_SUPPORTED_MODELS[:2])})", self._active_card)
        self._lbl_active_models.setStyleSheet("""
            color: #94a3b8;
            font-size: 11px;
            font-weight: 600;
            background-color: #070c17;
            border: 1px solid #16223b;
            border-radius: 6px;
            padding: 3px 8px;
        """)
        top_row.addWidget(self._lbl_active_models)

        top_row.addStretch()

        self._badge_active_key_status = StatusBadge("No Configurada", "warning", self._active_card)
        top_row.addWidget(self._badge_active_key_status)
        act_layout.addLayout(top_row)

        # Active key display vault capsule
        vault_box = QFrame(self._active_card)
        vault_box.setStyleSheet("""
            QFrame {
                background-color: #070b14;
                border: 1px solid #16223b;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        vb_layout = QHBoxLayout(vault_box)
        vb_layout.setContentsMargins(8, 6, 8, 6)

        self._lbl_current_key_display = QLabel("Sin clave guardada", vault_box)
        self._lbl_current_key_display.setStyleSheet("color: #cbd5e1; font-size: 12px; font-family: Consolas, monospace; background: transparent;")
        vb_layout.addWidget(self._lbl_current_key_display)
        act_layout.addWidget(vault_box)

        # Input field
        self._masked_input = MaskedKeyInput(
            placeholder="Pega tu API Key aquí...",
            parent=self._active_card
        )
        act_layout.addWidget(self._masked_input)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self._lbl_test_feedback = QLabel("", self._active_card)
        self._lbl_test_feedback.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 500;")
        btn_layout.addWidget(self._lbl_test_feedback)

        btn_layout.addStretch()

        self._btn_delete = QPushButton("🗑️ Eliminar", self._active_card)
        self._btn_delete.setProperty("class", "DangerButton")
        self._btn_delete.setFixedHeight(38)
        self._btn_delete.setMinimumWidth(110)
        self._btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(self._btn_delete)

        self._btn_test = QPushButton("🔍 Probar Conexión", self._active_card)
        self._btn_test.setProperty("class", "SecondaryButton")
        self._btn_test.setFixedHeight(38)
        self._btn_test.setMinimumWidth(155)
        self._btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_test.clicked.connect(self._on_test_clicked)
        btn_layout.addWidget(self._btn_test)

        self._btn_save = QPushButton("💾 Guardar Clave", self._active_card)
        self._btn_save.setProperty("class", "PrimaryButton")
        self._btn_save.setFixedHeight(38)
        self._btn_save.setMinimumWidth(145)
        self._btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self._btn_save)

        act_layout.addLayout(btn_layout)
        layout.addWidget(self._active_card)

        # Subtle security notice
        sec_banner = QFrame(container)
        sec_banner.setStyleSheet("""
            QFrame {
                background-color: #070c17;
                border: 1px solid #141f36;
                border-radius: 8px;
                padding: 10px 16px;
            }
        """)
        sb_layout = QHBoxLayout(sec_banner)
        sb_layout.setContentsMargins(6, 6, 6, 6)
        lbl_sec = QLabel(
            "🛡️ Tus claves se almacenan cifradas en Windows Credential Manager. Remodax nunca guarda claves en texto plano.",
            sec_banner
        )
        lbl_sec.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500; background: transparent;")
        lbl_sec.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(lbl_sec)
        layout.addWidget(sec_banner)

        layout.addStretch()

        scroll_area.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self._vm.keysStatusLoaded.connect(self._render_status)
        self._vm.keySaved.connect(self._on_key_saved)
        self._vm.keyTested.connect(self._on_key_tested)
        self._vm.errorOccurred.connect(self._show_error)

    def _on_provider_selected(self, provider: str) -> None:
        self._current_selected_provider = provider
        if provider == PROVIDER_GROQ:
            self._btn_select_groq.setChecked(True)
            self._btn_select_groq.setProperty("class", "PrimaryButton")
            self._btn_select_gemini.setChecked(False)
            self._btn_select_gemini.setProperty("class", "SecondaryButton")
            self._lbl_active_name.setText("⚡ GroqCloud")
            self._lbl_active_models.setText(f"({', '.join(GROQ_SUPPORTED_MODELS[:2])})")
        else:
            self._btn_select_gemini.setChecked(True)
            self._btn_select_gemini.setProperty("class", "PrimaryButton")
            self._btn_select_groq.setChecked(False)
            self._btn_select_groq.setProperty("class", "SecondaryButton")
            self._lbl_active_name.setText("✨ Google Gemini")
            self._lbl_active_models.setText(f"({', '.join(GEMINI_SUPPORTED_MODELS)})")

        self._btn_select_groq.style().unpolish(self._btn_select_groq)
        self._btn_select_groq.style().polish(self._btn_select_groq)
        self._btn_select_gemini.style().unpolish(self._btn_select_gemini)
        self._btn_select_gemini.style().polish(self._btn_select_gemini)

        self._lbl_test_feedback.setText("")
        self._update_active_provider_view()

    def _render_status(self, statuses: List[ApiKeyStatusDTO]) -> None:
        for s in statuses:
            self._statuses[s.provider] = s
        self._update_active_provider_view()

    def _update_active_provider_view(self) -> None:
        status = self._statuses.get(self._current_selected_provider)
        if status and status.is_configured:
            self._badge_active_key_status.set_status("Configurada", "success")
            self._lbl_current_key_display.setText(f"Clave activa en Windows Vault: {status.masked_key}")
            self._btn_delete.setEnabled(True)
        else:
            self._badge_active_key_status.set_status("No Configurada", "warning")
            self._lbl_current_key_display.setText("Estado actual: No configurada en Windows Credential Manager")
            self._btn_delete.setEnabled(False)

        self._masked_input.clear()

    def _on_save_clicked(self) -> None:
        raw_key = self._masked_input.text()
        if not raw_key:
            QMessageBox.warning(
                self,
                "API Key Requerida",
                "Por favor ingresa una API Key antes de guardar."
            )
            return

        self._vm.save_key(self._current_selected_provider, raw_key)

    def _on_test_clicked(self) -> None:
        raw_key = self._masked_input.text()
        status = self._statuses.get(self._current_selected_provider)
        has_saved = status and status.is_configured

        if not raw_key and not has_saved:
            QMessageBox.information(
                self,
                "Aviso",
                f"Ingresa tu clave de {self._current_selected_provider} para probar la conexión."
            )
            return

        self._badge_active_key_status.set_status("Probando conexión...", "warning")
        self._lbl_test_feedback.setText("Realizando prueba de conexión...")
        self._lbl_test_feedback.setStyleSheet("font-size: 11px; color: #f59e0b;")
        self._vm.test_key(self._current_selected_provider, raw_key)

    def _on_delete_clicked(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Deseas eliminar la clave de {self._current_selected_provider} de Windows Credential Manager?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._vm.delete_key(self._current_selected_provider)

    def _on_key_saved(self, provider: str, success: bool) -> None:
        if success:
            QMessageBox.information(
                self,
                "Éxito",
                f"La API Key de {provider} ha sido cifrada y guardada en Windows Credential Manager."
            )
            self._lbl_test_feedback.setText("Clave guardada exitosamente.")
            self._lbl_test_feedback.setStyleSheet("font-size: 11px; color: #34d399;")

    def _on_key_tested(self, result) -> None:
        if result.success:
            self._badge_active_key_status.set_status("Conexión Exitosa", "success")
            self._lbl_test_feedback.setText("✓ Conexión exitosa con el proveedor.")
            self._lbl_test_feedback.setStyleSheet("font-size: 11px; color: #34d399;")
            QMessageBox.information(self, "Prueba Exitosa", result.message)
        else:
            self._badge_active_key_status.set_status("Error de Conexión", "danger")
            self._lbl_test_feedback.setText(f"✕ {result.message}")
            self._lbl_test_feedback.setStyleSheet("font-size: 11px; color: #ef4444;")
            QMessageBox.warning(self, "Error de Conexión", result.message)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Error de Seguridad", message)
