"""
Remodax - Unit and Integration Tests: AI Providers & Streaming
Tests Groq, Gemini, Factory, Real API verification rejection, and Streaming Use Cases.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.config.constants import (
    PROVIDER_GROQ,
    PROVIDER_GEMINI,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    GROQ_SUPPORTED_MODELS,
    GEMINI_SUPPORTED_MODELS,
    KEYRING_SERVICE_NAME,
    KEYRING_GROQ_USER,
    KEYRING_GEMINI_USER,
)
from src.domain.entities.ai_models import AIRequest, AIResponseChunk, AIProviderType
from src.domain.exceptions import AIProviderException, SecurityCredentialException
from src.infrastructure.ai.groq_provider import GroqProvider
from src.infrastructure.ai.gemini_provider import GeminiProvider
from src.infrastructure.ai.provider_factory import AIProviderFactory
from src.application.use_cases.ai_use_cases import GenerateAIAnswerUseCase
from src.application.use_cases.security_use_cases import ManageApiKeysUseCase
from src.infrastructure.storage.sqlite_history_repo import SQLiteHistoryRepository


def test_groq_supported_models(mock_secrets_manager):
    provider = GroqProvider(mock_secrets_manager)
    models = provider.get_supported_models()
    assert models == GROQ_SUPPORTED_MODELS
    assert DEFAULT_GROQ_MODEL in models
    assert provider.provider_type == AIProviderType.GROQ


def test_gemini_supported_models(mock_secrets_manager):
    provider = GeminiProvider(mock_secrets_manager)
    models = provider.get_supported_models()
    assert models == GEMINI_SUPPORTED_MODELS
    assert DEFAULT_GEMINI_MODEL in models
    assert provider.provider_type == AIProviderType.GEMINI


def test_groq_empty_key_fails(mock_secrets_manager):
    provider = GroqProvider(mock_secrets_manager)
    with pytest.raises(AIProviderException) as exc_info:
        provider.test_connection("")
    assert "No se ha proporcionado una API Key" in str(exc_info.value)


def test_gemini_empty_key_fails(mock_secrets_manager):
    provider = GeminiProvider(mock_secrets_manager)
    with pytest.raises(AIProviderException) as exc_info:
        provider.test_connection("   ")
    assert "No se ha proporcionado una API Key" in str(exc_info.value)


def test_groq_real_invalid_key_fails(mock_secrets_manager):
    """
    Verifies that GroqProvider genuinely tests the API without faking success.
    An invalid API Key MUST be rejected and raise AIProviderException.
    """
    provider = GroqProvider(mock_secrets_manager)
    with pytest.raises(AIProviderException) as exc_info:
        provider.test_connection("gsk_invalid_test_key_0123456789abcdef0123456789abcdef")
    
    # Must reject with 401 AuthenticationError or Connection error, never return True
    err_msg = str(exc_info.value)
    assert any(term in err_msg for term in ["inválida", "401", "conexión", "servidores"])


def test_gemini_real_invalid_key_fails(mock_secrets_manager):
    """
    Verifies that GeminiProvider genuinely tests the API without faking success.
    An invalid API Key MUST be rejected and raise AIProviderException.
    """
    provider = GeminiProvider(mock_secrets_manager)
    with pytest.raises(AIProviderException) as exc_info:
        provider.test_connection("AIzaSyInvalidKeyForTestVerification_987654321")
    
    # Must reject with 400 ClientError or Connection error, never return True
    err_msg = str(exc_info.value)
    assert any(term in err_msg for term in ["inválida", "400", "403", "conexión", "servidores"])


def test_ai_provider_factory_resolution(mock_secrets_manager):
    groq_p = GroqProvider(mock_secrets_manager)
    gemini_p = GeminiProvider(mock_secrets_manager)
    factory = AIProviderFactory(groq_p, gemini_p)
    groq_client = factory.get_client(AIProviderType.GROQ)
    assert isinstance(groq_client, GroqProvider)

    gemini_client = factory.get_client(AIProviderType.GEMINI)
    assert isinstance(gemini_client, GeminiProvider)


def test_groq_generate_stream_unconfigured_key_raises(mock_secrets_manager):
    provider = GroqProvider(mock_secrets_manager)
    request = AIRequest(prompt="¿Cuál es tu función?")
    with pytest.raises(AIProviderException) as exc_info:
        list(provider.generate_stream(request))
    assert "No se ha configurado la API Key de Groq" in str(exc_info.value)


def test_gemini_generate_stream_unconfigured_key_raises(mock_secrets_manager):
    provider = GeminiProvider(mock_secrets_manager)
    request = AIRequest(prompt="¿Cuál es tu función?")
    with pytest.raises(AIProviderException) as exc_info:
        list(provider.generate_stream(request))
    assert "No se ha configurado la API Key de Gemini" in str(exc_info.value)


def test_gemini_generate_stream_upgrades_deprecated_model(mock_secrets_manager):
    from unittest.mock import patch
    mock_secrets_manager.save_secret(KEYRING_SERVICE_NAME, KEYRING_GEMINI_USER, "AIzaSyTestKey_valid")
    provider = GeminiProvider(mock_secrets_manager)
    req = AIRequest(prompt="Pregunta técnica")

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_chunk = MagicMock()
        mock_chunk.text = "Respuesta técnica precisa."
        mock_client.models.generate_content_stream.return_value = [mock_chunk]

        # When caller requests deprecated gemini-2.5-flash
        chunks = list(provider.generate_stream(req, model_name="gemini-2.5-flash"))
        assert len(chunks) == 2
        assert chunks[0].delta_text == "Respuesta técnica precisa."

        # Verify model was automatically upgraded to DEFAULT_GEMINI_MODEL (gemini-3.8-flash)
        call_kwargs = mock_client.models.generate_content_stream.call_args[1]
        assert call_kwargs["model"] == "gemini-3.8-flash"
        config_arg = call_kwargs["config"]
        assert config_arg.max_output_tokens == 220
        assert config_arg.thinking_config is not None
        assert "low" in str(config_arg.thinking_config.thinking_level).lower()


def test_generate_ai_answer_use_case_streaming(mock_secrets_manager, temp_sqlite_db, local_rag_engine):
    """
    Tests streaming AI generation orchestration, chunk dispatching,
    and SQLite history persistence.
    """
    history_repo = SQLiteHistoryRepository(temp_sqlite_db)
    
    # Configure fake valid key in mock secrets manager
    mock_secrets_manager.save_secret(KEYRING_SERVICE_NAME, KEYRING_GROQ_USER, "gsk_test_stored_key")

    mock_client = MagicMock()
    # Simulate stream chunks
    mock_chunks = [
        AIResponseChunk(delta_text="Hola", is_final=False),
        AIResponseChunk(delta_text=", soy", is_final=False),
        AIResponseChunk(delta_text=" Remodax.", is_final=False),
        AIResponseChunk(delta_text="", is_final=True),
    ]
    mock_client.generate_stream.return_value = iter(mock_chunks)

    mock_factory = MagicMock()
    mock_factory.get_client.return_value = mock_client

    use_case = GenerateAIAnswerUseCase(
        ai_factory=mock_factory,
        secrets_manager=mock_secrets_manager,
        rag_service=local_rag_engine,
        history_repo=history_repo
    )

    chunks = list(use_case.execute_stream(
        question="Preséntate brevemente",
        provider_name=PROVIDER_GROQ,
        model_name=DEFAULT_GROQ_MODEL,
        allow_external_rag=False
    ))

    # Verify streamed chunks
    assert len(chunks) == 4
    full_text = "".join(c.delta_text for c in chunks)
    assert full_text == "Hola, soy Remodax."

    # Verify AIRequest had spoken first-person instructions
    dispatched_req = mock_client.generate_stream.call_args[0][0]
    assert "PRIMERA PERSONA" in dispatched_req.system_instruction

    # Verify history persistence in SQLite
    history = history_repo.search_history("Remodax")
    assert len(history) == 1
    assert history[0].question_text == "Preséntate brevemente"
    assert history[0].answer_text == "Hola, soy Remodax."
    assert history[0].ai_provider == PROVIDER_GROQ
    assert history[0].ai_model == DEFAULT_GROQ_MODEL


def test_manage_api_keys_use_case_test_real_rejection(mock_secrets_manager):
    """
    Ensures ManageApiKeysUseCase correctly maps real rejection into TestApiKeyResultDTO(success=False).
    """
    factory = AIProviderFactory(
        GroqProvider(mock_secrets_manager),
        GeminiProvider(mock_secrets_manager)
    )
    use_case = ManageApiKeysUseCase(mock_secrets_manager, factory)

    # Groq test with invalid key
    groq_res = use_case.test_api_key(PROVIDER_GROQ, "gsk_invalid_test_key_abc")
    assert groq_res.success is False
    assert groq_res.provider == PROVIDER_GROQ
    assert len(groq_res.message) > 5

    # Gemini test with invalid key
    gemini_res = use_case.test_api_key(PROVIDER_GEMINI, "AIzaSyInvalidKey_xyz")
    assert gemini_res.success is False
    assert gemini_res.provider == PROVIDER_GEMINI
    assert len(gemini_res.message) > 5
