"""
Remodax - DitherVeil Interactive Logo Component
Architecture: UI Component Layer (Presentation)
Encapsulates the React Bits DitherVeil WebGL effect for desktop PySide6,
rendering the local brand avatar (logoDany.png) with procedural error-diffusion
dithering, cursor-trail reveal, cyan electric rim, click burst ripple,
and autonomous idle wandering.
"""

import os
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QPixmap

os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")

from src.config.constants import (
    LOGO_DANY_PATH,
    DITHER_HTML_PATH,
    DEFAULT_DITHER_PATTERN,
    DEFAULT_DITHER_FIT,
    DEFAULT_DITHER_INK_COLOR,
    DEFAULT_DITHER_PAPER_COLOR,
    DEFAULT_DITHER_RIM_COLOR,
    DEFAULT_DITHER_RIM,
    DEFAULT_DITHER_REVEAL_RADIUS,
    DEFAULT_DITHER_PIXEL_SIZE,
    DEFAULT_DITHER_WANDER,
    DEFAULT_DITHER_LINGER,
    DEFAULT_DITHER_CLICK_BURST,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False


class DitherVeilWidget(QFrame):
    """
    Presentation component that hosts the DitherVeil WebGL animation.
    Adheres to Clean Architecture:
      - Configuration ingested from application constants or constructor overrides.
      - Visual styles decoupled into dark_theme.qss.
      - Graceful degradation to static QPixmap when WebGL is unavailable.
      - Explicit resource disposal on widget destruction.
    """

    def __init__(
        self,
        image_path: Optional[Path] = None,
        pattern: str = DEFAULT_DITHER_PATTERN,
        fit: str = DEFAULT_DITHER_FIT,
        ink_color: str = DEFAULT_DITHER_INK_COLOR,
        paper_color: str = DEFAULT_DITHER_PAPER_COLOR,
        rim_color: str = DEFAULT_DITHER_RIM_COLOR,
        rim: float = DEFAULT_DITHER_RIM,
        reveal_radius: int = DEFAULT_DITHER_REVEAL_RADIUS,
        pixel_size: int = DEFAULT_DITHER_PIXEL_SIZE,
        wander: bool = DEFAULT_DITHER_WANDER,
        linger: float = DEFAULT_DITHER_LINGER,
        click_burst: bool = DEFAULT_DITHER_CLICK_BURST,
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("DitherVeilContainer")
        self.setProperty("class", "DitherVeilFrame")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWidth(0)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._image_path = Path(image_path) if image_path else LOGO_DANY_PATH
        self._html_path = DITHER_HTML_PATH
        self._pattern = pattern
        self._fit = fit
        self._ink_color = ink_color
        self._paper_color = paper_color
        self._rim_color = rim_color
        self._rim = rim
        self._reveal_radius = reveal_radius
        self._pixel_size = pixel_size
        self._wander = wander
        self._linger = linger
        self._click_burst = click_burst

        self._view: Optional[QWebEngineView] = None
        self._fallback_label: Optional[QLabel] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._init_component(layout)

    def _init_component(self, layout: QVBoxLayout) -> None:
        """Initializes WebGL view or native fallback based on environment capabilities."""
        if WEB_ENGINE_AVAILABLE and self._html_path.exists():
            try:
                self._view = QWebEngineView(self)
                self._view.setObjectName("DitherVeilWebView")
                self._view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                self._view.setStyleSheet("background: transparent; border: none;")
                self._view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

                # Set transparent page background to seamlessly integrate with Remodax
                self._view.page().setBackgroundColor(QColor(0, 0, 0, 0))

                # Configure WebEngine security & rendering parameters
                settings = self._view.settings()
                settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)

                # Build URL with animation hyperparameters
                params = [
                    f"src={QUrl.fromLocalFile(str(self._image_path)).toString()}",
                    f"pattern={self._pattern}",
                    f"inkColor={QUrl.toPercentEncoding(self._ink_color).data().decode()}",
                    f"paperColor={QUrl.toPercentEncoding(self._paper_color).data().decode()}",
                    f"rimColor={QUrl.toPercentEncoding(self._rim_color).data().decode()}",
                    f"revealRadius={self._reveal_radius}",
                    f"pixelSize={self._pixel_size}",
                    f"wander={'true' if self._wander else 'false'}",
                    f"linger={self._linger}",
                    f"clickBurst={'true' if self._click_burst else 'false'}",
                    f"fit={self._fit}",
                    "contrast=1.25",
                    "brightness=0.05",
                    "softness=0.6",
                    f"rim={self._rim}"
                ]
                url = QUrl.fromLocalFile(str(self._html_path))
                url.setQuery("&".join(params))

                self._view.setUrl(url)
                layout.addWidget(self._view)
                return
            except Exception:
                # Fallback gracefully if WebEngine engine cannot initialize
                pass

        # Native fallback using scaled QPixmap
        self._fallback_label = QLabel(self)
        self._fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fallback_label.setStyleSheet("background: transparent; border: none;")
        if self._image_path.exists():
            pix = QPixmap(str(self._image_path)).scaled(
                170, 170,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._fallback_label.setPixmap(pix)
        else:
            self._fallback_label.setText("⚡ Dany AI")
            self._fallback_label.setStyleSheet("color: #38bdf8; font-weight: 700;")
        layout.addWidget(self._fallback_label)

    def cleanup(self) -> None:
        """Explicitly disposes web view resources to prevent memory leaks."""
        if self._view is not None:
            self._view.stop()
            self._view.setUrl(QUrl("about:blank"))
            self._view.setParent(None)
            self._view.deleteLater()
            self._view = None

    def closeEvent(self, event) -> None:
        """Ensures cleanup is called on widget close."""
        self.cleanup()
        super().closeEvent(event)
