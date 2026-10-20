"""
Remodax - Settings DTOs
Data Transfer Objects for application settings and device selections.
"""

from dataclasses import dataclass
from typing import List


from src.config.constants import DEFAULT_INTERVIEW_SYSTEM_PROMPT


@dataclass
class AudioDeviceDTO:
    index: int
    name: str
    is_loopback: bool
    channels: int
    default_sample_rate: float


@dataclass
class SettingsDTO:
    active_provider: str
    active_model: str
    audio_source: str
    audio_device_index: int
    whisper_model: str
    allow_external_rag: bool
    persist_audio: bool
    dark_mode: bool
    system_prompt: str = DEFAULT_INTERVIEW_SYSTEM_PROMPT

