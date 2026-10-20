"""
Remodax - Unit Tests for VAD, Whisper Transcription, and Document Parsers
Ensures audio question end detection, whisper-large-v3-turbo integration,
and document RAG processing work correctly.
"""

import io
import time
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.infrastructure.audio.buffer_manager import QuestionVoiceActivityDetector
from src.infrastructure.audio.whisper_transcriber import WhisperTranscriber
from src.infrastructure.documents.pdf_parser import PyMuPDFParser
from src.infrastructure.documents.docx_parser import DocxParser
from src.infrastructure.documents.rag_engine import LocalRAGEngine
from src.config.constants import KEYRING_SERVICE_NAME, KEYRING_GROQ_USER, DEFAULT_GROQ_MODEL


def test_vad_speech_and_silence_detection():
    detected_questions = []

    def on_question(audio_chunk):
        detected_questions.append(audio_chunk)

    vad = QuestionVoiceActivityDetector(
        sample_rate=16000,
        silence_threshold=0.02,
        pause_duration_sec=0.1,  # Shortened for fast unit test
        min_speech_duration_sec=0.05,
        pre_roll_sec=0.05,
        on_question_detected=on_question
    )

    # 1. Feed pure silence
    silence_frame = np.zeros(800, dtype=np.float32)
    vad.process_frame(silence_frame)
    assert len(detected_questions) == 0

    # 2. Feed speech frames (RMS > 0.02)
    speech_frame = np.ones(800, dtype=np.float32) * 0.1
    for _ in range(5):
        vad.process_frame(speech_frame)
    assert len(detected_questions) == 0

    # 3. Feed silence frame to begin silence measurement
    vad.process_frame(silence_frame)
    # Wait past pause duration
    time.sleep(0.12)
    # Feed next silence frame to complete pause detection
    vad.process_frame(silence_frame)

    # Question should be detected now
    assert len(detected_questions) == 1
    assert len(detected_questions[0]) > 0


def test_whisper_audio_to_wav_bytes():
    audio_data = np.sin(np.linspace(0, 2 * np.pi * 440, 16000)).astype(np.float32)
    wav_bytes = WhisperTranscriber._audio_to_wav_bytes(audio_data, 16000)

    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 44  # WAV header + data
    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"


def test_whisper_transcriber_groq_integration(mock_secrets_manager):
    mock_secrets_manager.save_secret(KEYRING_SERVICE_NAME, KEYRING_GROQ_USER, "gsk_valid_key")
    transcriber = WhisperTranscriber(
        model_size="whisper-large-v3-turbo",
        secrets_manager=mock_secrets_manager
    )

    fake_response = MagicMock()
    fake_response.text = "¿Cómo optimizar una base de datos?"

    with patch("groq.Groq") as mock_groq_class:
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = fake_response

        dummy_audio = np.ones(16000, dtype=np.float32) * 0.05
        result = transcriber.transcribe(dummy_audio)

        assert result == "¿Cómo optimizar una base de datos?"
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["model"] == "whisper-large-v3-turbo"


def test_docx_parser_and_rag_indexing(tmp_path):
    docx_file = tmp_path / "cv.docx"

    # Create dummy docx file
    from docx import Document as NewDocx
    d = NewDocx()
    d.add_paragraph("Experiencia profesional en Python, FastApi y Docker.")
    d.add_paragraph("Educación: Ingeniería de Software con honores.")
    d.save(str(docx_file))

    parser = DocxParser(chunk_size=100)
    assert parser.supports_extension(".docx") is True

    parsed_doc = parser.parse_file(str(docx_file))
    assert parsed_doc.filename == "cv.docx"
    assert len(parsed_doc.chunks) >= 1

    # Index into RAG engine
    rag = LocalRAGEngine()
    rag.index_document(parsed_doc)

    res = rag.search_context("Docker y Python", top_k=1)
    assert len(res) == 1
    assert "Python" in res[0].content


def test_default_groq_model_is_gpt_oss_20b():
    assert DEFAULT_GROQ_MODEL == "openai/gpt-oss-20b"
