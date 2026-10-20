"""
Remodax - Settings Domain Entities
Defines user preferences, audio device types, and system configuration models.
"""

from dataclasses import dataclass
from enum import Enum
from src.config.constants import (
    PROVIDER_GROQ,
    DEFAULT_GROQ_MODEL,
    DEFAULT_WHISPER_MODEL,
    DEFAULT_ALLOW_EXTERNAL_RAG,
    DEFAULT_PERSIST_AUDIO,
    DEFAULT_INTERVIEW_SYSTEM_PROMPT,
)


class AudioSourceType(str, Enum):
    """Types of audio input capturing."""
    WASAPI_LOOPBACK = "WASAPI Loopback (Audio del Sistema)"
    MICROPHONE = "Micrófono"


@dataclass
class UserSettings:
    """User preferences stored locally."""
    active_provider: str = PROVIDER_GROQ
    active_model: str = DEFAULT_GROQ_MODEL
    audio_source: AudioSourceType = AudioSourceType.WASAPI_LOOPBACK
    audio_device_index: int = -1  # -1 for default device
    whisper_model: str = DEFAULT_WHISPER_MODEL
    allow_external_rag: bool = DEFAULT_ALLOW_EXTERNAL_RAG
    persist_audio: bool = DEFAULT_PERSIST_AUDIO  # Hardened: default False
    dark_mode: bool = True
    system_prompt: str = DEFAULT_INTERVIEW_SYSTEM_PROMPT
