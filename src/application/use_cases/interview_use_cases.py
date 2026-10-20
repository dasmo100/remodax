import threading
import logging
from typing import Callable, Optional
import numpy as np
from src.domain.entities.interview import InterviewSession, QuestionAnswer
from src.domain.entities.settings_entity import AudioSourceType
from src.domain.ports.audio_port import IAudioCaptureService, IAudioTranscriber
from src.domain.ports.storage_port import IHistoryRepository
from src.application.dtos.interview_dto import InterviewSessionDTO
from src.infrastructure.audio.buffer_manager import QuestionVoiceActivityDetector
from src.domain.services.question_detector import QuestionDetector
from src.config.constants import (
    DEFAULT_VAD_SILENCE_THRESHOLD,
    DEFAULT_VAD_PAUSE_DURATION_SEC,
    DEFAULT_VAD_MIN_SPEECH_DURATION_SEC,
    DEFAULT_VAD_SPEECH_PROB_THRESHOLD,
    DEFAULT_VAD_MIN_ACTIVE_SPEECH_SEC,
)

logger = logging.getLogger("remodax.interview")


class InterviewSessionUseCase:
    """Manages active interview session lifecycle and audio feed coordination."""

    def __init__(
        self,
        audio_capture: IAudioCaptureService,
        transcriber: IAudioTranscriber,
        history_repo: IHistoryRepository
    ):
        self._audio_capture = audio_capture
        self._transcriber = transcriber
        self._history_repo = history_repo
        self._active_session: Optional[InterviewSession] = None
        self._transcription_lock = threading.Lock()
        self._is_transcribing = False
        self._vad = QuestionVoiceActivityDetector(
            sample_rate=16000,
            vad_threshold=DEFAULT_VAD_SPEECH_PROB_THRESHOLD,
            silence_threshold=DEFAULT_VAD_SILENCE_THRESHOLD,
            pause_duration_sec=DEFAULT_VAD_PAUSE_DURATION_SEC,
            min_speech_duration_sec=DEFAULT_VAD_MIN_SPEECH_DURATION_SEC,
            min_active_speech_sec=DEFAULT_VAD_MIN_ACTIVE_SPEECH_SEC,
        )

    @property
    def is_session_active(self) -> bool:
        return self._active_session is not None and self._audio_capture.is_capturing()

    def start_session(
        self,
        title: str,
        audio_source: AudioSourceType,
        device_index: Optional[int],
        on_transcription_ready: Callable[[str], None]
    ) -> InterviewSessionDTO:
        session = InterviewSession(
            title=title or "Sesión de Entrevista",
            audio_source=audio_source.value
        )
        self._active_session = session
        self._history_repo.save_session(session)
        self._vad.reset()
        QuestionDetector.reset_history()

        # Callback for when VAD detects end of a complete question
        def on_question_audio_ready(question_audio: np.ndarray) -> None:
            if not self._active_session:
                return

            def transcribe_worker():
                # Avoid concurrent transcription collisions
                with self._transcription_lock:
                    self._is_transcribing = True
                    try:
                        logger.info("Enviando audio de pregunta detectada a Whisper (%d muestras)...", len(question_audio))
                        transcription = self._transcriber.transcribe(question_audio)
                        if transcription and transcription.strip():
                            logger.info("Transcripción obtenida: '%s'", transcription.strip())
                            on_transcription_ready(transcription.strip())
                    except Exception as ex:
                        logger.error("Error durante transcripción de pregunta: %s", str(ex))
                    finally:
                        self._is_transcribing = False

            t = threading.Thread(target=transcribe_worker, daemon=True)
            t.start()

        self._vad.set_callback(on_question_audio_ready)

        # Audio stream callback: runs on audio thread, feeds VAD without blocking
        def audio_frame_callback(audio_data: np.ndarray) -> None:
            if not self._active_session:
                return
            self._vad.process_frame(audio_data)

        is_loopback = (audio_source == AudioSourceType.WASAPI_LOOPBACK)
        self._audio_capture.start_capture(
            callback=audio_frame_callback,
            device_index=device_index,
            is_loopback=is_loopback
        )

        return InterviewSessionDTO(
            id=session.id,
            title=session.title,
            started_at_str=session.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            ended_at_str=None,
            audio_source=session.audio_source,
            qa_count=0
        )

    def stop_session(self) -> Optional[InterviewSessionDTO]:
        if not self._active_session:
            return None

        self._audio_capture.stop_capture()
        self._active_session.close_session()
        self._history_repo.save_session(self._active_session)

        dto = InterviewSessionDTO(
            id=self._active_session.id,
            title=self._active_session.title,
            started_at_str=self._active_session.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            ended_at_str=self._active_session.ended_at.strftime("%Y-%m-%d %H:%M:%S") if self._active_session.ended_at else None,
            audio_source=self._active_session.audio_source,
            qa_count=len(self._active_session.qa_list)
        )
        self._active_session = None
        return dto
