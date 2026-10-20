"""
Remodax - Masked Input Component
Specialized QLineEdit with password mode and show/hide toggle.
Enforces security: avoids displaying cleartext API keys by default.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from src.config.constants import ICONS_DIR


class MaskedKeyInput(QWidget):
    """Secure input widget for sensitive credentials."""

    textChanged = Signal(str)

    def __init__(self, placeholder: str = "Ingresa tu API Key...", parent: QWidget = None):
        super().__init__(parent)
        self._is_visible = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText(placeholder)
        self._line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._line_edit.setFixedHeight(38)
        self._line_edit.setStyleSheet("font-family: Consolas, 'Cascadia Code', monospace; font-size: 13px;")
        self._line_edit.textChanged.connect(self.textChanged.emit)

        self._toggle_btn = QPushButton(self)
        self._toggle_btn.setToolTip("Mostrar / Ocultar clave")
        self._toggle_btn.setFixedSize(38, 38)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setProperty("class", "SecondaryButton")
        self._toggle_btn.setIconSize(QSize(18, 18))
        self._toggle_btn.clicked.connect(self._toggle_visibility)

        self._icon_eye = ICONS_DIR / "eye.svg"
        self._icon_eye_off = ICONS_DIR / "eye_off.svg"

        self._update_icon()

        layout.addWidget(self._line_edit)
        layout.addWidget(self._toggle_btn)

    def _update_icon(self) -> None:
        if self._is_visible:
            if self._icon_eye_off.exists():
                self._toggle_btn.setIcon(QIcon(str(self._icon_eye_off)))
                self._toggle_btn.setText("")
            else:
                self._toggle_btn.setText("🔒")
            self._toggle_btn.setToolTip("Ocultar clave")
        else:
            if self._icon_eye.exists():
                self._toggle_btn.setIcon(QIcon(str(self._icon_eye)))
                self._toggle_btn.setText("")
            else:
                self._toggle_btn.setText("👁")
            self._toggle_btn.setToolTip("Mostrar clave")

    def _toggle_visibility(self) -> None:
        self._is_visible = not self._is_visible
        if self._is_visible:
            self._line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._update_icon()

    def text(self) -> str:
        return self._line_edit.text().strip()

    def setText(self, text: str) -> None:
        self._line_edit.setText(text)

    def clear(self) -> None:
        self._line_edit.clear()
