"""
Remodax - Unit Tests: Use Cases & Local Services
Tests local RAG keyword search, SQLite history queries, and settings persistence.
"""

from src.domain.entities.document import Document, DocumentChunk
from src.domain.entities.interview import InterviewSession, QuestionAnswer
from src.domain.entities.settings_entity import UserSettings, AudioSourceType
from src.infrastructure.storage.sqlite_history_repo import SQLiteHistoryRepository
from src.infrastructure.storage.sqlite_settings_repo import SQLiteSettingsRepository
from src.infrastructure.documents.rag_engine import LocalRAGEngine
from src.application.use_cases.security_use_cases import ManageApiKeysUseCase
from src.application.dtos.api_key_dto import SaveApiKeyRequestDTO
from src.config.constants import PROVIDER_GROQ


def test_local_rag_engine_retrieval(local_rag_engine: LocalRAGEngine):
    doc = Document(filename="guia.pdf", filepath="/path/guia.pdf", file_type="pdf", file_size_bytes=500)
    chunk1 = DocumentChunk(document_id=doc.id, chunk_index=0, content="Python soporta tipado estático opcional con type hints.")
    chunk2 = DocumentChunk(document_id=doc.id, chunk_index=1, content="PySide6 es la biblioteca oficial de Qt para Python.")
    doc.chunks = [chunk1, chunk2]

    local_rag_engine.index_document(doc)

    # Search for Qt
    results = local_rag_engine.search_context("Cómo usar la biblioteca Qt en mi app", top_k=1)
    assert len(results) == 1
    assert "PySide6" in results[0].content


def test_sqlite_history_repository(temp_sqlite_db):
    repo = SQLiteHistoryRepository(temp_sqlite_db)

    # Save session
    session = InterviewSession(title="Sesión Demo")
    repo.save_session(session)

    # Save Q&A
    qa = QuestionAnswer(
        session_id=session.id,
        question_text="Explica qué es un decorador en Python",
        answer_text="Un decorador es una función que modifica el comportamiento de otra función.",
        ai_provider="GroqCloud",
        ai_model="llama-3.3-70b-versatile",
        response_latency_ms=120.0
    )
    repo.save_qa(qa)

    # Search
    search_results = repo.search_history("decorador")
    assert len(search_results) == 1
    assert search_results[0].question_text == qa.question_text


def test_sqlite_settings_repository(temp_sqlite_db):
    repo = SQLiteSettingsRepository(temp_sqlite_db)

    initial_settings = repo.load_settings()
    assert initial_settings.active_provider == "GroqCloud"
    assert "PRIMERA PERSONA" in initial_settings.system_prompt

    updated = UserSettings(
        active_provider="Gemini",
        active_model="gemini-3.8-flash",
        audio_source=AudioSourceType.MICROPHONE,
        allow_external_rag=True,
        system_prompt="Custom spoken prompt"
    )
    repo.save_settings(updated)

    loaded = repo.load_settings()
    assert loaded.active_provider == "Gemini"
    assert loaded.active_model == "gemini-3.8-flash"
    assert loaded.audio_source == AudioSourceType.MICROPHONE
    assert loaded.allow_external_rag is True
    assert loaded.system_prompt == "Custom spoken prompt"

    # Test legacy prompt and model migration: gemini-2.5-flash -> gemini-3.8-flash
    legacy_settings = UserSettings(
        active_model="gemini-2.5-flash",
        system_prompt="Reglas: 1. Usa expresiones naturales como 'En mi experiencia...'"
    )
    repo.save_settings(legacy_settings)
    migrated = repo.load_settings()
    assert migrated.active_model == "gemini-3.8-flash"
    assert "PROHIBIDO 'EN MI EXPERIENCIA'" in migrated.system_prompt
    assert "CORRECCIÓN TÉCNICA RIGUROSA" in migrated.system_prompt
    assert "PREFERENTEMENTE 2 A 3 LÍNEAS" in migrated.system_prompt
    assert "SOAP" in migrated.system_prompt



def test_security_use_case_save_and_status(mock_secrets_manager):
    class FakeAIFactory:
        def get_client(self, _):
            pass

    use_case = ManageApiKeysUseCase(mock_secrets_manager, FakeAIFactory())

    # Initially not configured
    status = use_case.get_provider_key_status(PROVIDER_GROQ)
    assert status.is_configured is False
    assert status.masked_key == "No configurada"

    # Save key
    saved = use_case.save_api_key(SaveApiKeyRequestDTO(provider=PROVIDER_GROQ, api_key="gsk_1234567890abcdef12345678"))
    assert saved is True

    # Check status again
    status = use_case.get_provider_key_status(PROVIDER_GROQ)
    assert status.is_configured is True
    assert status.masked_key.startswith("gsk_")
    assert "••••••••" in status.masked_key
