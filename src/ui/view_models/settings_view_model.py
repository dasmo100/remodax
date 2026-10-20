"""
Remodax - Settings ViewModel
Bridges Preferences & Audio device configuration with UI.
"""

from PySide6.QtCore import QObject, Signal
from src.application.use_cases.settings_use_cases import SettingsUseCase
from src.application.dtos.settings_dto import SettingsDTO


class SettingsViewModel(QObject):
    """Manages application settings and audio device discovery."""

    settingsLoaded = Signal(object)      # SettingsDTO
    devicesLoaded = Signal(list)         # List[AudioDeviceDTO]
    settingsSaved = Signal()
    errorOccurred = Signal(str)

    def __init__(self, settings_use_cases: SettingsUseCase):
        super().__init__()
        self._settings_use_cases = settings_use_cases

    def load_settings(self) -> None:
        try:
            dto = self._settings_use_cases.get_settings()
            self.settingsLoaded.emit(dto)
        except Exception as ex:
            self.errorOccurred.emit(f"Error cargando configuración: {str(ex)}")

    def load_audio_devices(self) -> None:
        try:
            devices = self._settings_use_cases.list_audio_devices()
            self.devicesLoaded.emit(devices)
        except Exception as ex:
            self.errorOccurred.emit(f"Error detectando dispositivos de audio: {str(ex)}")

    def save_settings(self, dto: SettingsDTO) -> None:
        try:
            self._settings_use_cases.update_settings(dto)
            self.settingsSaved.emit()
        except Exception as ex:
            self.errorOccurred.emit(f"Error guardando configuración: {str(ex)}")
