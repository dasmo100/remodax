"""
Remodax - Whisper Audio Transcription Infrastructure
Wraps faster-whisper for speech-to-text processing directly from memory buffers.
"""

import logging
import io
import wave
import numpy as np
from typing import Optional
from src.domain.ports.audio_port import IAudioTranscriber
from src.domain.ports.security_port import ISecretsManager
from src.domain.exceptions import TranscriptionException
from src.config.constants import KEYRING_SERVICE_NAME, KEYRING_GROQ_USER, DEFAULT_WHISPER_MODEL

logger = logging.getLogger("remodax.whisper")


class WhisperTranscriber(IAudioTranscriber):
    """
    Speech-to-text service powered by Whisper (whisper-large-v3-turbo via Groq,
    with local faster-whisper fallback).
    Processes audio directly from memory buffers without touching disk.
    """

    def __init__(
        self,
        model_size: str = DEFAULT_WHISPER_MODEL,
        device: str = "cpu",
        compute_type: str = "int8",
        secrets_manager: Optional[ISecretsManager] = None
    ):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._secrets = secrets_manager
        self._local_model = None

    def set_secrets_manager(self, secrets_manager: ISecretsManager) -> None:
        self._secrets = secrets_manager

    def load_model(self, model_size: str = "base") -> None:
        self._model_size = model_size
        local_target = "base" if "turbo" in model_size.lower() or "large" in model_size.lower() else model_size
        try:
            from faster_whisper import WhisperModel
            logger.info("Cargando modelo local Whisper '%s' en %s...", local_target, self._device)
            self._local_model = WhisperModel(local_target, device=self._device, compute_type=self._compute_type)
            logger.info("Modelo local Whisper cargado exitosamente.")
        except ImportError:
            logger.warning("Librería 'faster-whisper' no detectada. Operando en modo stub para local.")
            self._local_model = None
        except Exception as ex:
            logger.warning("No se pudo cargar modelo local Whisper: %s", str(ex))
            self._local_model = None

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribes audio data float32 buffer directly from RAM.
        Validates speech content with Silero VAD before dispatching to Groq whisper-large-v3-turbo.
        Filters out noise, short artifacts, and silence hallucinations.
        """
        if audio_data is None or len(audio_data) == 0:
            return ""

        audio_mono = audio_data.flatten().astype(np.float32)
        # Discard audio fragments shorter than 0.75 seconds (~12,000 samples at 16kHz)
        if len(audio_mono) < int(sample_rate * 0.75):
            return ""

        # Pre-check: Ensure audio actually contains human voice using Silero VAD before calling APIs
        try:
            from faster_whisper.vad import get_speech_timestamps, VadOptions
            opts = VadOptions(threshold=0.45, min_speech_duration_ms=250)
            timestamps = get_speech_timestamps(audio_mono, vad_options=opts)
            if not timestamps and np.std(audio_mono) > 0.001:
                logger.debug("Segmento de audio descartado: VAD no detectó voz humana.")
                return ""
        except Exception as vad_err:
            logger.debug("VAD pre-check omitido: %s", vad_err)

        # 1. Attempt ultra-fast whisper-large-v3-turbo via Groq Cloud
        if self._secrets:
            groq_key = self._secrets.get_secret(KEYRING_SERVICE_NAME, KEYRING_GROQ_USER)
            if groq_key and groq_key.strip():
                try:
                    import groq
                    client = groq.Groq(api_key=groq_key.strip())
                    wav_bytes = self._audio_to_wav_bytes(audio_mono, sample_rate)

                    # Optimize Groq Whisper: temperature=0.0 for zero hallucination, prompt for domain conditioning
                    resp = client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=("audio.wav", wav_bytes, "audio/wav"),
                        language="es",
                        temperature=0.0,
                        prompt="Entrevista laboral técnica. Preguntas del entrevistador claras y precisas:",
                        response_format="json"
                    )
                    transcription = getattr(resp, "text", "") or ""
                    clean_transcription = self._sanitize_transcription(transcription)
                    if clean_transcription:
                        logger.info("Transcripción exitosa con whisper-large-v3-turbo (Groq): '%s'", clean_transcription)
                        return clean_transcription
                except Exception as ex:
                    logger.warning(
                        "Transcripción con Groq whisper-large-v3-turbo no completada: %s. "
                        "Intentando con motor local...",
                        str(ex)
                    )

        # 2. Local Fallback via faster-whisper
        if self._local_model is None:
            try:
                self.load_model(self._model_size)
            except Exception:
                pass

        if self._local_model is not None:
            try:
                segments, info = self._local_model.transcribe(
                    audio_mono,
                    beam_size=1,
                    temperature=0.0,
                    language="es",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=400, threshold=0.5)
                )
                transcription = " ".join([seg.text.strip() for seg in segments]).strip()
                clean_transcription = self._sanitize_transcription(transcription)
                if clean_transcription:
                    logger.info("Transcripción local completada: '%s'", clean_transcription)
                    return clean_transcription
            except Exception as ex:
                logger.error("Error durante transcripción local Whisper: %s", str(ex))

        return ""

    @staticmethod
    def _sanitize_transcription(text: str) -> str:
        """Strips annotations, brackets, and common Whisper silence hallucinations."""
        if not text:
            return ""
        import re
        # Remove [Música], (Risas), [Aplausos], etc.
        cleaned = re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()
        # Remove standalone hallucination keywords
        lower = cleaned.lower()
        hallucinations = ["subtítulos", "subtitulos", "amén", "amen", "gracias por ver", "suscríbete", "suscribete", "bye"]
        for h in hallucinations:
            if lower == h or lower == f"{h}.":
                return ""
        return cleaned

    @staticmethod
    def _audio_to_wav_bytes(audio_mono: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Encodes float32 1D numpy array into in-memory 16-bit PCM WAV bytes without touching disk."""
        clipped = np.clip(audio_mono, -1.0, 1.0)
        int16_samples = (clipped * 32767.0).astype(np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int16_samples.tobytes())
        return buffer.getvalue()
