"""
Remodax - Audio Level Meter Component
Visual VU meter displaying audio capture activity in real time.
Modernized with cyber-studio indicator aesthetics.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QFrame
from PySide6.QtCore import Qt, QTimer
import random


class AudioLevelMeter(QWidget):
    """Visual VU meter showing audio capture level and activity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        self._current_level = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 10, 4)
        layout.setSpacing(8)

        # Container styling for sleek capsule appearance
        self.setStyleSheet("""
            AudioLevelMeter {
                background-color: #070c17;
                border: 1px solid #1a2742;
                border-radius: 8px;
            }
        """)

        # Icon indicator
        self._lbl_icon = QLabel("🔈", self)
        self._lbl_icon.setStyleSheet("font-size: 13px; color: #64748b; background: transparent;")
        layout.addWidget(self._lbl_icon)

        # Progress VU bar
        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setMinimumWidth(110)
        self._bar.setProperty("class", "AudioMeterBar")
        layout.addWidget(self._bar)

        # Status text pill
        self._lbl_status = QLabel("● Silencio", self)
        self._lbl_status.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; min-width: 65px; background: transparent;")
        layout.addWidget(self._lbl_status)

        # Subtle animation timer for active state
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._on_tick)

    def set_active(self, active: bool) -> None:
        """Enables or disables meter animation."""
        self._is_active = active
        if active:
            self._lbl_icon.setText("🎙️")
            self._lbl_icon.setStyleSheet("font-size: 13px; color: #00d2ff; background: transparent;")
            self._lbl_status.setText("● Activo")
            self._lbl_status.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 700; min-width: 65px; background: transparent;")
            self._timer.start()
        else:
            self._timer.stop()
            self._bar.setValue(0)
            self._lbl_icon.setText("🔈")
            self._lbl_icon.setStyleSheet("font-size: 13px; color: #64748b; background: transparent;")
            self._lbl_status.setText("● Silencio")
            self._lbl_status.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; min-width: 65px; background: transparent;")

    def set_level(self, level_0_to_100: int) -> None:
        """Sets explicit volume level (0-100)."""
        self._current_level = max(0, min(100, level_0_to_100))
        self._bar.setValue(self._current_level)

    def _on_tick(self) -> None:
        if self._is_active:
            # Ambient pulse between 25% and 80% when capturing
            simulated = random.randint(25, 78)
            self._bar.setValue(simulated)
