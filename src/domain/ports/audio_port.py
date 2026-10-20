"""
Remodax - Audio Domain Ports
Abstract interfaces for audio capture (WASAPI Loopback / Microphone) and Speech-To-Text.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Any, Optional
import numpy as np


class IAudioCaptureService(ABC):
    """Port for audio capturing hardware/software interface."""

    @abstractmethod
    def start_capture(
        self,
        callback: Callable[[np.ndarray], None],
        device_index: Optional[int] = None,
        is_loopback: bool = True
    ) -> None:
        """Starts capturing audio stream asynchronously."""
        pass

    @abstractmethod
    def stop_capture(self) -> None:
        """Stops active audio capturing and flushes buffers."""
        pass

    @abstractmethod
    def is_capturing(self) -> bool:
        """Returns True if audio capturing is active."""
        pass

    @abstractmethod
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Lists available Windows audio input and loopback output devices."""
        pass


class IAudioTranscriber(ABC):
    """Port for converting captured audio buffers to text via Whisper."""

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribes raw audio float32 buffer into textual question/sentence."""
        pass

    @abstractmethod
    def load_model(self, model_size: str = "base") -> None:
        """Loads or swaps Whisper model in memory."""
        pass
