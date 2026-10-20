"""
Remodax - Main Window Application Shell
Assembles Navigation Sidebar and QStackedWidget containing all 5 primary application views.
"""

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PySide6.QtGui import QIcon
from src.container import AppContainer
from src.config.constants import (
    APP_NAME,
    APP_VERSION,
    ASSETS_DIR,
    APP_ICON_ICO_PATH,
    LOGO_DANY_PATH,
    DARK_THEME_QSS_PATH,
)
from src.ui.components.sidebar import NavigationSidebar
from src.ui.view_models.interview_view_model import InterviewViewModel
from src.ui.view_models.documents_view_model import DocumentsViewModel
from src.ui.view_models.api_keys_view_model import ApiKeysViewModel
from src.ui.view_models.history_view_model import HistoryViewModel
from src.ui.view_models.settings_view_model import SettingsViewModel
from src.ui.views.interview_view import InterviewView
from src.ui.views.documents_view import DocumentsView
from src.ui.views.api_keys_view import ApiKeysView
from src.ui.views.history_view import HistoryView
from src.ui.views.settings_view import SettingsView


class MainWindow(QMainWindow):
    """Main desktop application window for Remodax."""

    def __init__(self, container: AppContainer):
        super().__init__()
        self._container = container

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — Asistente de Entrevistas y RAG")
        self.resize(1180, 780)
        self.setMinimumSize(960, 640)

        # Set App Window Icon (prefers multi-resolution .ico with fallback to logoDany.png)
        if APP_ICON_ICO_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO_PATH)))
        elif LOGO_DANY_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_DANY_PATH)))

        self._load_stylesheet()
        self._init_ui()

    def _load_stylesheet(self) -> None:
        """Applies dark theme QSS stylesheet with dynamic asset path resolution."""
        if DARK_THEME_QSS_PATH.exists():
            with open(DARK_THEME_QSS_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                # Dynamically bind relative url(assets/...) to absolute posix path for QSS rendering
                assets_posix = ASSETS_DIR.as_posix()
                content = content.replace("url(assets/", f"url({assets_posix}/")
                self.setStyleSheet(content)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Navigation Sidebar
        self._sidebar = NavigationSidebar(self)
        main_layout.addWidget(self._sidebar)

        # 2. View Stack
        self._stack = QStackedWidget(self)
        main_layout.addWidget(self._stack)

        # Instantiate ViewModels from Container Use Cases
        vm_interview = InterviewViewModel(
            self._container.interview_use_cases,
            self._container.ai_use_cases,
            self._container.settings_repo
        )
        vm_documents = DocumentsViewModel(self._container.document_use_cases)
        vm_api_keys = ApiKeysViewModel(self._container.security_use_cases)
        vm_history = HistoryViewModel(self._container.history_use_cases)
        vm_settings = SettingsViewModel(self._container.settings_use_cases)

        # Instantiate Views and mount onto Stack
        self._view_interview = InterviewView(vm_interview, self)
        self._view_documents = DocumentsView(vm_documents, self)
        self._view_api_keys = ApiKeysView(vm_api_keys, self)
        self._view_settings = SettingsView(vm_settings, self)

        self._stack.addWidget(self._view_interview)  # index 0
        self._stack.addWidget(self._view_documents)  # index 1
        self._stack.addWidget(self._view_api_keys)   # index 2
        self._stack.addWidget(self._view_settings)   # index 3

        # Wire navigation
        self._sidebar.pageChanged.connect(self._stack.setCurrentIndex)

    def closeEvent(self, event) -> None:
        """Disposes sidebar and active view resources on shutdown."""
        if hasattr(self, "_sidebar") and self._sidebar:
            self._sidebar.cleanup()
        super().closeEvent(event)
