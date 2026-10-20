"""
Tests for DitherVeilWidget component.
"""

from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.ui.components.dither_veil_widget import DitherVeilWidget, WEB_ENGINE_AVAILABLE


def test_dither_veil_widget_initialization(qapp):
    """Test that DitherVeilWidget initializes cleanly with default logo."""
    widget = DitherVeilWidget(
        pattern="floyd",
        ink_color="#0f172a",
        paper_color="#ffffff",
        rim_color="#ffffff",
        rim=0.0,
        reveal_radius=120,
        wander=False
    )
    assert widget is not None
    assert widget.objectName() == "DitherVeilContainer"
    assert widget._image_path.exists()
    assert widget._image_path.name == "logoDany.png"


def test_dither_veil_widget_fallback_mode(qapp, monkeypatch):
    """Test that fallback mode renders static pixmap when WebEngine is unavailable."""
    import src.ui.components.dither_veil_widget as dvm
    monkeypatch.setattr(dvm, "WEB_ENGINE_AVAILABLE", False)

    widget = dvm.DitherVeilWidget()
    assert hasattr(widget, "_fallback_label")
    assert widget._fallback_label is not None
    widget.cleanup()


def test_dither_veil_widget_cleanup(qapp):
    """Test that cleanup disposes web view cleanly."""
    widget = DitherVeilWidget()
    widget.cleanup()
    assert widget._view is None


def test_sidebar_includes_dither_veil(qapp):
    """Test that NavigationSidebar integrates DitherVeilWidget and supports cleanup."""
    from src.ui.components.sidebar import NavigationSidebar
    sidebar = NavigationSidebar()
    assert hasattr(sidebar, "_logo_veil")
    assert sidebar._logo_veil is not None
    assert sidebar._logo_veil.objectName() == "DitherVeilContainer"
    sidebar.cleanup()
