"""
Remodax - Settings & Device Configuration Use Cases
Manages application configuration, audio input devices, and privacy flags.
"""

from typing import List
from src.domain.entities.settings_entity import UserSettings, AudioSourceType
from src.domain.ports.storage_port import ISettingsRepository
from src.domain.ports.audio_port import IAudioCaptureService
from src.application.dtos.settings_dto import SettingsDTO, AudioDeviceDTO


class SettingsUseCase:
    """Orchestrates configuration persistence and audio hardware inspection."""

    def __init__(
        self,
        settings_repo: ISettingsRepository,
        audio_capture: IAudioCaptureService
    ):
        self._settings_repo = settings_repo
        self._audio_capture = audio_capture

    def get_settings(self) -> SettingsDTO:
        s = self._settings_repo.load_settings()
        return SettingsDTO(
            active_provider=s.active_provider,
            active_model=s.active_model,
            audio_source=s.audio_source.value,
            audio_device_index=s.audio_device_index,
            whisper_model=s.whisper_model,
            allow_external_rag=s.allow_external_rag,
            persist_audio=s.persist_audio,
            dark_mode=s.dark_mode,
            system_prompt=s.system_prompt
        )

    def update_settings(self, new_settings: SettingsDTO) -> None:
        source_enum = (
            AudioSourceType.MICROPHONE
            if "Micro" in new_settings.audio_source
            else AudioSourceType.WASAPI_LOOPBACK
        )
        entity = UserSettings(
            active_provider=new_settings.active_provider,
            active_model=new_settings.active_model,
            audio_source=source_enum,
            audio_device_index=new_settings.audio_device_index,
            whisper_model=new_settings.whisper_model,
            allow_external_rag=new_settings.allow_external_rag,
            persist_audio=new_settings.persist_audio,
            dark_mode=new_settings.dark_mode,
            system_prompt=new_settings.system_prompt
        )
        self._settings_repo.save_settings(entity)

    def list_audio_devices(self) -> List[AudioDeviceDTO]:
        raw_devices = self._audio_capture.get_available_devices()
        return [
            AudioDeviceDTO(
                index=d.get("index", -1),
                name=d.get("name", "Unknown Device"),
                is_loopback=d.get("is_loopback", False),
                channels=d.get("channels", 2),
                default_sample_rate=float(d.get("sample_rate", 44100.0))
            )
            for d in raw_devices
        ]
