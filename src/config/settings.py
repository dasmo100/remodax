"""
Remodax - Application Settings & Path Management
Manages local directories, secure paths, and application state defaults.
"""

from dataclasses import dataclass
from pathlib import Path
import sys
from src.config.constants import (
    APP_NAME,
    APP_DATA_DIR,
    DATABASE_PATH,
    DOCUMENTS_STORAGE_DIR,
    PROVIDER_GROQ,
    DEFAULT_GROQ_MODEL,
    DEFAULT_WHISPER_MODEL,
    DEFAULT_ALLOW_EXTERNAL_RAG,
    DEFAULT_PERSIST_AUDIO,
)

# Ensure workspace venv site-packages is discoverable if present (development only)
if not getattr(sys, "frozen", False):
    _venv_site = Path(__file__).resolve().parent.parent.parent / "venv" / "Lib" / "site-packages"
    if _venv_site.exists() and str(_venv_site) not in sys.path:
        sys.path.insert(0, str(_venv_site))


@dataclass
class AppConfig:
    """Runtime application configuration and paths."""
    app_name: str = APP_NAME
    app_data_dir: Path = APP_DATA_DIR
    database_path: Path = DATABASE_PATH
    documents_dir: Path = DOCUMENTS_STORAGE_DIR
    
    # Defaults
    default_provider: str = PROVIDER_GROQ
    default_model: str = DEFAULT_GROQ_MODEL
    whisper_model: str = DEFAULT_WHISPER_MODEL
    allow_external_rag: bool = DEFAULT_ALLOW_EXTERNAL_RAG
    persist_audio: bool = DEFAULT_PERSIST_AUDIO

    def initialize_filesystem(self) -> None:
        """Creates required local directories with appropriate user-only permissions."""
        try:
            self.app_data_dir.mkdir(parents=True, exist_ok=True)
            self.documents_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # Fallback for sandboxed, restricted, or portable environments
            fallback_dir = Path.home() / f".{self.app_name.lower()}"
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                docs_dir = fallback_dir / "documents"
                docs_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                fallback_dir = (Path.cwd() / f".{self.app_name.lower()}_storage").resolve()
                fallback_dir.mkdir(parents=True, exist_ok=True)
                docs_dir = fallback_dir / "documents"
                docs_dir.mkdir(parents=True, exist_ok=True)

            self.app_data_dir = fallback_dir
            self.database_path = fallback_dir / "remodax_local.db"
            self.documents_dir = docs_dir

    @staticmethod
    def is_windows() -> bool:
        """Validates if running on Windows (10/11 required for WASAPI loopback & Keyring)."""
        return sys.platform.startswith("win")
