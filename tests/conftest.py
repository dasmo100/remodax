"""
Remodax - Pytest Configuration & Test Fixtures
Provides isolated memory-backed mocks for ports, keyring, and SQLite.
"""

import pytest
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

from src.domain.ports.security_port import ISecretsManager
from src.infrastructure.storage.database import SQLiteDatabase
from src.infrastructure.storage.sqlite_history_repo import SQLiteHistoryRepository
from src.infrastructure.storage.sqlite_settings_repo import SQLiteSettingsRepository
from src.infrastructure.storage.sqlite_document_repo import SQLiteDocumentRepository
from src.infrastructure.documents.rag_engine import LocalRAGEngine
from src.infrastructure.security.mask_utils import mask_api_key


class InMemoryMockSecretsManager(ISecretsManager):
    """In-memory mock for Windows Credential Manager to run fast hermetic tests."""

    def __init__(self):
        self._vault: Dict[str, str] = {}

    def save_secret(self, service_name: str, username: str, secret_value: str) -> bool:
        self._vault[f"{service_name}:{username}"] = secret_value
        return True

    def get_secret(self, service_name: str, username: str) -> Optional[str]:
        return self._vault.get(f"{service_name}:{username}")

    def delete_secret(self, service_name: str, username: str) -> bool:
        key = f"{service_name}:{username}"
        if key in self._vault:
            del self._vault[key]
            return True
        return False

    def has_secret(self, service_name: str, username: str) -> bool:
        return f"{service_name}:{username}" in self._vault

    def mask_secret(self, secret_value: Optional[str]) -> str:
        return mask_api_key(secret_value)


@pytest.fixture
def mock_secrets_manager():
    return InMemoryMockSecretsManager()


@pytest.fixture
def temp_sqlite_db(tmp_path: Path):
    db_file = tmp_path / "test_remodax.db"
    db = SQLiteDatabase(db_file)
    db.initialize_schema()
    return db


@pytest.fixture
def local_rag_engine():
    return LocalRAGEngine()
