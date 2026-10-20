"""
Remodax - API Keys ViewModel
Coordinates credential configuration, testing, and UI feedback without exposing secrets.
"""

import threading
from PySide6.QtCore import QObject, Signal
from src.application.use_cases.security_use_cases import ManageApiKeysUseCase
from src.application.dtos.api_key_dto import SaveApiKeyRequestDTO, TestApiKeyResultDTO


class ApiKeysViewModel(QObject):
    """Handles API Key management and connectivity test feedback."""

    keysStatusLoaded = Signal(list)       # List[ApiKeyStatusDTO]
    keySaved = Signal(str, bool)          # (provider, success)
    keyTested = Signal(object)            # TestApiKeyResultDTO
    errorOccurred = Signal(str)

    def __init__(self, security_use_cases: ManageApiKeysUseCase):
        super().__init__()
        self._security = security_use_cases

    def load_keys_status(self) -> None:
        try:
            statuses = self._security.get_all_keys_status()
            self.keysStatusLoaded.emit(statuses)
        except Exception as ex:
            self.errorOccurred.emit(f"Error cargando estado de credenciales: {str(ex)}")

    def save_key(self, provider: str, raw_key: str) -> None:
        try:
            req = SaveApiKeyRequestDTO(provider=provider, api_key=raw_key)
            success = self._security.save_api_key(req)
            self.keySaved.emit(provider, success)
            if success:
                self.load_keys_status()
        except Exception as ex:
            self.errorOccurred.emit(f"Error al guardar credencial: {str(ex)}")

    def delete_key(self, provider: str) -> None:
        try:
            self._security.delete_api_key(provider)
            self.load_keys_status()
        except Exception as ex:
            self.errorOccurred.emit(f"Error al eliminar credencial: {str(ex)}")

    def test_key(self, provider: str, optional_key: str = "") -> None:
        """Runs test call on background thread to prevent GUI freezing."""
        def worker():
            try:
                res = self._security.test_api_key(provider, optional_key)
                self.keyTested.emit(res)
            except Exception as ex:
                self.errorOccurred.emit(f"Error durante prueba: {str(ex)}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
