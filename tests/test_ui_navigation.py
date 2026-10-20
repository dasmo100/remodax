"""
Remodax - UI Navigation and View Integration Tests
Hermetic tests ensuring all PySide6 GUI views instantiate, wire properly,
and switch navigation without errors.
"""

import pytest
from PySide6.QtWidgets import QApplication
from src.container import AppContainer
from src.ui.main_window import MainWindow
from src.ui.views.interview_view import InterviewView
from src.ui.views.documents_view import DocumentsView
from src.ui.views.api_keys_view import ApiKeysView
from src.ui.views.history_view import HistoryView
from src.ui.views.settings_view import SettingsView


from src.config.settings import AppConfig


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp, tmp_path, monkeypatch):
    from src.infrastructure.audio.wasapi_capture import WasapiAudioCaptureService
    monkeypatch.setattr(WasapiAudioCaptureService, "get_available_devices", lambda self: [])

    config = AppConfig(
        app_data_dir=tmp_path / "appdata",
        database_path=tmp_path / "appdata" / "remodax_test.db",
        documents_dir=tmp_path / "appdata" / "documents",
    )
    container = AppContainer(config=config)
    window = MainWindow(container)
    return window


def test_main_window_initialization(main_window):
    assert main_window is not None
    assert "Remodax" in main_window.windowTitle()
    assert main_window._stack.count() == 4


def test_sidebar_navigation_sections(main_window):
    sidebar = main_window._sidebar
    assert len(sidebar._buttons) == 4

    # Check button texts
    labels = [btn.text() for btn in sidebar._buttons]
    assert any("Entrevista" in lbl for lbl in labels)
    assert any("Documentos" in lbl for lbl in labels)
    assert any("Configuración API" in lbl for lbl in labels)
    assert any("Ajustes" in lbl for lbl in labels)

    # Test page switching for all 4 tabs
    for idx in range(4):
        sidebar._buttons[idx].click()
        assert main_window._stack.currentIndex() == idx


def test_interview_view_components(main_window):
    view = main_window._view_interview
    assert isinstance(view, InterviewView)
    assert view._text_question is not None
    assert view._text_answer is not None
    assert view._audio_meter is not None
    assert view._conn_badge is not None
    assert view._audio_badge is not None
    assert view._btn_session_toggle is not None
    assert view._combo_provider.count() >= 2


def test_documents_view_components(main_window):
    view = main_window._view_documents
    assert isinstance(view, DocumentsView)
    assert view._table is not None
    assert view._lbl_count is not None
    assert view._search_input is not None
    assert view._btn_import is not None
    assert view._btn_delete is not None


def test_api_keys_view_components(main_window):
    view = main_window._view_api_keys
    assert isinstance(view, ApiKeysView)
    assert view._btn_select_groq is not None
    assert view._btn_select_gemini is not None
    assert view._masked_input is not None
    assert view._btn_save is not None
    assert view._btn_test is not None

    # Test switching between Groq and Gemini
    view._btn_select_gemini.click()
    assert view._current_selected_provider == "Gemini"
    view._btn_select_groq.click()
    assert view._current_selected_provider == "GroqCloud"





def test_settings_view_components(main_window):
    view = main_window._view_settings
    assert isinstance(view, SettingsView)
    assert view._combo_audio_source is not None
    assert view._combo_devices is not None
    assert view._combo_whisper is not None
    assert view._chk_zero_audio.isChecked()
    assert not view._chk_zero_audio.isEnabled()  # Enforced invariant
    assert view._text_system_prompt is not None
    assert view._btn_save is not None

