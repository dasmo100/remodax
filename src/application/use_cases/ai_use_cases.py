"""
Remodax - AI Generation Use Cases
Handles streaming AI responses, RAG context enrichment with consent checks, and Q&A recording.
"""

import time
from typing import Iterator, Optional
from src.config.constants import (
    KEYRING_SERVICE_NAME,
    KEYRING_GROQ_USER,
    KEYRING_GEMINI_USER,
    PROVIDER_GROQ,
    DEFAULT_INTERVIEW_SYSTEM_PROMPT,
)
from src.domain.entities.ai_models import AIRequest, AIResponseChunk, AIProviderType
from src.domain.entities.interview import QuestionAnswer
from src.domain.ports.ai_port import IAIProviderFactory
from src.domain.ports.document_port import IRAGService
from src.domain.ports.security_port import ISecretsManager
from src.domain.ports.storage_port import IHistoryRepository, ISettingsRepository
from src.domain.exceptions import AIProviderException, SecurityCredentialException
from src.application.dtos.interview_dto import QuestionAnswerDTO


class GenerateAIAnswerUseCase:
    """Orchestrates RAG context lookup, security authorization, and streaming AI generation."""

    def __init__(
        self,
        ai_factory: IAIProviderFactory,
        secrets_manager: ISecretsManager,
        rag_service: IRAGService,
        history_repo: IHistoryRepository,
        settings_repo: Optional[ISettingsRepository] = None
    ):
        self._ai_factory = ai_factory
        self._secrets = secrets_manager
        self._rag_service = rag_service
        self._history_repo = history_repo
        self._settings_repo = settings_repo

    def execute_stream(
        self,
        question: str,
        provider_name: str,
        model_name: str,
        session_id: Optional[str] = None,
        allow_external_rag: bool = False,
        system_instruction: Optional[str] = None
    ) -> Iterator[AIResponseChunk]:
        """
        Executes streaming LLM response.
        Enforces user consent before attaching private document chunks to external API.
        """
        # 1. Retrieve API Key securely from OS Credential Manager
        username = KEYRING_GROQ_USER if provider_name == PROVIDER_GROQ else KEYRING_GEMINI_USER
        api_key = self._secrets.get_secret(KEYRING_SERVICE_NAME, username)
        if not api_key or not api_key.strip():
            raise SecurityCredentialException(
                f"No se ha configurado la API Key para {provider_name}. "
                "Por favor ingrésela en la sección de Configuración de API."
            )

        # 2. Privacy Guardrail: RAG Context injection
        context_chunks = []
        if allow_external_rag:
            # Query local RAG engine for matching document fragments
            matched_chunks = self._rag_service.search_context(question, top_k=3)
            context_chunks = [c.content for c in matched_chunks]

        # 3. Determine system instruction (user setting > argument > default spoken prompt)
        instruction = system_instruction
        if not instruction and self._settings_repo:
            try:
                user_settings = self._settings_repo.load_settings()
                if user_settings.system_prompt and user_settings.system_prompt.strip():
                    instruction = user_settings.system_prompt.strip()
            except Exception:
                pass

        if not instruction:
            instruction = DEFAULT_INTERVIEW_SYSTEM_PROMPT

        # 4. Build Request
        request = AIRequest(
            prompt=question,
            system_instruction=instruction,
            context_chunks=context_chunks,
            allow_external_rag=allow_external_rag
        )

        enum_provider = AIProviderType.GROQ if provider_name == PROVIDER_GROQ else AIProviderType.GEMINI
        client = self._ai_factory.get_client(enum_provider)

        start_time = time.time()
        accumulated_answer: list[str] = []

        try:
            for chunk in client.generate_stream(request, model_name=model_name):
                if chunk.delta_text:
                    accumulated_answer.append(chunk.delta_text)
                yield chunk

            # Complete and persist in local history
            latency_ms = (time.time() - start_time) * 1000
            full_answer = "".join(accumulated_answer)

            qa_entity = QuestionAnswer(
                session_id=session_id,
                question_text=question,
                answer_text=full_answer,
                ai_provider=provider_name,
                ai_model=model_name,
                response_latency_ms=latency_ms,
                context_used=bool(context_chunks)
            )
            self._history_repo.save_qa(qa_entity)

        except Exception as ex:
            raise AIProviderException(f"Error en comunicación con {provider_name}: {str(ex)}") from ex
