"""
Remodax - Sidebar Navigation Component
Sidebar menu with modern buttons, active selection states, and page index signals.
Preserves logoDany interactive DitherVeil animation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpacerItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Signal, Qt
from src.config.constants import APP_NAME
from src.ui.components.dither_veil_widget import DitherVeilWidget


class NavigationSidebar(QWidget):
    """Left navigation panel for switching view stacks."""

    pageChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self._buttons = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(6)

        # 1. Interactive DitherVeil Logo Animation (Preserved logoDany)
        self._logo_veil = DitherVeilWidget(parent=self)
        self._logo_veil.setFixedHeight(210)
        layout.addWidget(self._logo_veil)

        # 2. Header Title & Subtitle with High-Tech Aesthetics
        header_box = QWidget(self)
        h_layout = QVBoxLayout(header_box)
        h_layout.setContentsMargins(4, 0, 4, 8)
        h_layout.setSpacing(2)

        title = QLabel(APP_NAME, header_box)
        title.setObjectName("AppTitleLabel")
        subtitle = QLabel("ASISTENTE IA DE ENTREVISTAS", header_box)
        subtitle.setObjectName("AppSubtitleLabel")
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header_box)

        # Subtle decorative divider line
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #141f36; max-height: 1px; border: none; margin: 0 10px 8px 10px;")
        layout.addWidget(divider)

        # 3. Navigation Buttons
        self._nav_items = [
            ("🎙  Entrevista", 0),
            ("📁  Documentos", 1),
            ("🔑  Configuración API", 2),
            ("⚙  Ajustes", 3),
        ]

        nav_container = QWidget(self)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        for label_text, index in self._nav_items:
            btn = QPushButton(label_text, nav_container)
            btn.setProperty("class", "NavButton")
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=index: self._on_btn_clicked(idx))
            self._buttons.append(btn)
            nav_layout.addWidget(btn)

        layout.addWidget(nav_container)

        # Set first button checked by default
        if self._buttons:
            self._buttons[0].setChecked(True)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # 4. Futuristic Security & Vault Footer
        sec_box = QWidget(self)
        sec_box.setObjectName("SidebarFooter")
        sec_layout = QHBoxLayout(sec_box)
        sec_layout.setContentsMargins(12, 10, 12, 10)
        sec_layout.setSpacing(6)

        sec_dot = QLabel("●", sec_box)
        sec_dot.setStyleSheet("color: #10b981; font-size: 10px; background: transparent;")
        sec_layout.addWidget(sec_dot)

        sec_info = QLabel("Privado y Local", sec_box)
        sec_info.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; background: transparent;")
        sec_layout.addWidget(sec_info)

        sec_layout.addStretch()

        ver_lbl = QLabel("v0.1", sec_box)
        ver_lbl.setStyleSheet("""
            color: #64748b;
            font-size: 10px;
            font-weight: 700;
            background-color: #141e33;
            border-radius: 4px;
            padding: 2px 6px;
        """)
        sec_layout.addWidget(ver_lbl)

        layout.addWidget(sec_box)

    def _on_btn_clicked(self, selected_index: int) -> None:
        self.set_active_index(selected_index)
        self.pageChanged.emit(selected_index)

    def set_active_index(self, selected_index: int) -> None:
        for idx, btn in enumerate(self._buttons):
            is_checked = (idx == selected_index)
            btn.setChecked(is_checked)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def cleanup(self) -> None:
        """Disposes resources to ensure clean application shutdown."""
        if hasattr(self, "_logo_veil") and self._logo_veil:
            self._logo_veil.cleanup()
