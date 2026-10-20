"""
Remodax - Status Badge Component
Visual badge indicator for hardware status, AI state, and privacy indicators.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """High-tech pill badge indicating operational states."""

    def __init__(self, text: str = "Inactivo", status_type: str = "warning", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(26)
        self.set_status(text, status_type)

    def set_status(self, text: str, status_type: str) -> None:
        """
        Updates text and status style ('success', 'warning', 'danger').
        """
        clean_text = text.strip()
        display_text = clean_text if clean_text.startswith("●") else f"●  {clean_text}"
        self.setText(display_text)
        css_class = f"Badge{status_type.capitalize()}"
        self.setProperty("class", css_class)
        self.style().unpolish(self)
        self.style().polish(self)
