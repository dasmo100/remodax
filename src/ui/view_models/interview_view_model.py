"""
Remodax - Interview ViewModel
Bridges Interview UI with Application Use Cases using Qt signals and background threads.
Guarantees asynchronous non-blocking UI and prevents duplicate or overlapping AI generations.
"""

import time
import logging
import threading
from PySide6.QtCore import QObject, Signal
from typing import Optional
from src.application.use_cases.interview_use_cases import InterviewSessionUseCase
from src.application.use_cases.ai_use_cases import GenerateAIAnswerUseCase
from src.domain.entities.settings_entity import AudioSourceType
from src.domain.ports.storage_port import ISettingsRepository

logger = logging.getLogger("remodax.interview.vm")


class InterviewViewModel(QObject):
    """Coordinates active interview session state and AI answer streaming."""

    sessionStatusChanged = Signal(bool, str)     # (is_active, message)
    transcriptionReceived = Signal(str)          # live question text
    answerChunkReceived = Signal(str)            # delta text
    answerCompleted = Signal(str)                # full text
    errorOccurred = Signal(str)                  # error message

    def __init__(
        self,
        interview_use_cases: InterviewSessionUseCase,
        ai_use_cases: GenerateAIAnswerUseCase,
        settings_repo: Optional[ISettingsRepository] = None
    ):
        super().__init__()
        self._interview_use_cases = interview_use_cases
        self._ai_use_cases = ai_use_cases
        self._settings_repo = settings_repo
        self._current_session_id = None

        self._lock = threading.Lock()
        self._is_generating = False
        self._generation_id = 0
        self._last_dispatched_question = ""
        self._last_dispatched_norm_question = ""
        self._last_dispatched_time = 0.0

    @property
    def is_generating_answer(self) -> bool:
        with self._lock:
            return self._is_generating

    def get_user_settings(self):
        """Loads non-sensitive configuration defaults from local storage."""
        if self._settings_repo:
            try:
                return self._settings_repo.load_settings()
            except Exception as ex:
                logger.warning("No se pudieron cargar los ajustes en InterviewViewModel: %s", ex)
        return None

    def start_interview(
        self,
        title: str = "Sesión Activa",
        is_loopback: Optional[bool] = None,
        device_index: Optional[int] = None
    ) -> None:
        # Load audio configuration from user settings if not explicitly passed
        if is_loopback is None and self._settings_repo:
            try:
                user_settings = self._settings_repo.load_settings()
                is_loopback = (user_settings.audio_source == AudioSourceType.WASAPI_LOOPBACK)
                if device_index is None:
                    device_index = user_settings.audio_device_index
            except Exception:
                is_loopback = True

        if is_loopback is None:
            is_loopback = True
        if device_index is None:
            device_index = -1

        source_type = AudioSourceType.WASAPI_LOOPBACK if is_loopback else AudioSourceType.MICROPHONE
        dev_idx = None if device_index < 0 else device_index

        try:
            dto = self._interview_use_cases.start_session(
                title=title,
                audio_source=source_type,
                device_index=dev_idx,
                on_transcription_ready=self._on_transcription_arrived
            )
            self._current_session_id = dto.id
            self.sessionStatusChanged.emit(True, f"Sesión iniciada ({dto.audio_source})")
        except Exception as ex:
            self.errorOccurred.emit(f"Error al iniciar sesión: {str(ex)}")

    def stop_interview(self) -> None:
        try:
            dto = self._interview_use_cases.stop_session()
            self._current_session_id = None
            with self._lock:
                self._is_generating = False
            self.sessionStatusChanged.emit(False, "Sesión finalizada.")
        except Exception as ex:
            self.errorOccurred.emit(f"Error al detener sesión: {str(ex)}")

    def ask_ai_question(
        self,
        question: str,
        provider: str,
        model: str,
        allow_external_rag: bool,
        force: bool = False
    ) -> None:
        """
        Dispatches streaming answer generation on a background worker thread.
        Prevents duplicate in-flight requests and cancels prior streams gracefully if a new question arrives.
        """
        clean_q = question.strip()
        if not clean_q:
            return

        import re
        norm_q = re.sub(r"[^\w\s]", "", clean_q.lower()).strip()

        now = time.time()
        with self._lock:
            # Deduplication check: reject same question if automatically triggered within 5.0s (debounce)
            if not force and norm_q == self._last_dispatched_norm_question and (now - self._last_dispatched_time) < 5.0:
                logger.debug("Debounce: Pregunta idéntica descartada en ViewModel: '%s'", clean_q)
                return

            self._generation_id += 1
            gen_id = self._generation_id
            self._is_generating = True
            self._last_dispatched_question = clean_q
            self._last_dispatched_norm_question = norm_q
            self._last_dispatched_time = now

        def worker(my_id: int):
            try:
                full_text = []
                chunks = self._ai_use_cases.execute_stream(
                    question=clean_q,
                    provider_name=provider,
                    model_name=model,
                    session_id=self._current_session_id,
                    allow_external_rag=allow_external_rag
                )
                for chunk in chunks:
                    with self._lock:
                        if my_id != self._generation_id:
                            # A newer question arrived; stop emitting chunks to UI
                            return
                    if chunk.delta_text:
                        full_text.append(chunk.delta_text)
                        self.answerChunkReceived.emit(chunk.delta_text)

                with self._lock:
                    if my_id == self._generation_id:
                        self.answerCompleted.emit("".join(full_text))
            except Exception as ex:
                with self._lock:
                    if my_id == self._generation_id:
                        self.errorOccurred.emit(str(ex))
            finally:
                with self._lock:
                    if my_id == self._generation_id:
                        self._is_generating = False

        thread = threading.Thread(target=worker, args=(gen_id,), daemon=True)
        thread.start()

    def _on_transcription_arrived(self, question_text: str) -> None:
        self.transcriptionReceived.emit(question_text)
