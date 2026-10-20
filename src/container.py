"""
Remodax - Dependency Injection Container
Composes all application layers following Clean Architecture & SOLID inversion of control.
"""

from typing import Optional
from pathlib import Path
from src.config.settings import AppConfig
from src.config.logging_config import setup_logging
from src.infrastructure.security.keyring_manager import WindowsCredentialManager
from src.infrastructure.storage.database import SQLiteDatabase
from src.infrastructure.storage.sqlite_history_repo import SQLiteHistoryRepository
from src.infrastructure.storage.sqlite_settings_repo import SQLiteSettingsRepository
from src.infrastructure.storage.sqlite_document_repo import SQLiteDocumentRepository
from src.infrastructure.documents.pdf_parser import PyMuPDFParser
from src.infrastructure.documents.docx_parser import DocxParser
from src.infrastructure.documents.rag_engine import LocalRAGEngine
from src.infrastructure.audio.wasapi_capture import WasapiAudioCaptureService
from src.infrastructure.audio.whisper_transcriber import WhisperTranscriber
from src.infrastructure.ai.groq_provider import GroqProvider
from src.infrastructure.ai.gemini_provider import GeminiProvider
from src.infrastructure.ai.provider_factory import AIProviderFactory
from src.application.use_cases.security_use_cases import ManageApiKeysUseCase
from src.application.use_cases.interview_use_cases import InterviewSessionUseCase
from src.application.use_cases.ai_use_cases import GenerateAIAnswerUseCase
from src.application.use_cases.document_use_cases import DocumentManagementUseCase
from src.application.use_cases.history_use_cases import HistoryManagementUseCase
from src.application.use_cases.settings_use_cases import SettingsUseCase


class AppContainer:
    """Central Composition Root for the Remodax application."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.logger = setup_logging()

        # 1. Initialize local filesystem
        self.config.initialize_filesystem()

        # 2. Infrastructure - Security & Database
        self.secrets_manager = WindowsCredentialManager()
        self.database = SQLiteDatabase(self.config.database_path)
        self.database.initialize_schema()

        # 3. Infrastructure - Repositories
        self.history_repo = SQLiteHistoryRepository(self.database)
        self.settings_repo = SQLiteSettingsRepository(self.database)
        self.document_repo = SQLiteDocumentRepository(self.database)

        # 4. Infrastructure - Documents & RAG
        self.pdf_parser = PyMuPDFParser()
        self.docx_parser = DocxParser()
        self.parsers = [self.pdf_parser, self.docx_parser]
        self.rag_engine = LocalRAGEngine()

        # Index existing documents from storage into local RAG engine
        try:
            stored_docs = self.document_repo.list_documents()
            for doc_meta in stored_docs:
                p = Path(doc_meta.filepath)
                if p.exists():
                    suffix = p.suffix.lower()
                    parser = next((pr for pr in self.parsers if pr.supports_extension(suffix)), None)
                    if parser:
                        parsed = parser.parse_file(str(p))
                        self.rag_engine.index_document(parsed)
        except Exception as doc_ex:
            self.logger.warning("Aviso pre-indexando documentos existentes: %s", doc_ex)

        # 5. Infrastructure - Audio
        self.audio_capture = WasapiAudioCaptureService()
        self.whisper_transcriber = WhisperTranscriber(
            model_size=self.config.whisper_model,
            secrets_manager=self.secrets_manager
        )

        # 6. Infrastructure - AI
        self.groq_provider = GroqProvider(self.secrets_manager)
        self.gemini_provider = GeminiProvider(self.secrets_manager)
        self.ai_factory = AIProviderFactory(self.groq_provider, self.gemini_provider)

        # 7. Application Use Cases
        self.security_use_cases = ManageApiKeysUseCase(self.secrets_manager, self.ai_factory)
        self.interview_use_cases = InterviewSessionUseCase(
            self.audio_capture,
            self.whisper_transcriber,
            self.history_repo
        )
        self.ai_use_cases = GenerateAIAnswerUseCase(
            self.ai_factory,
            self.secrets_manager,
            self.rag_engine,
            self.history_repo,
            self.settings_repo
        )
        self.document_use_cases = DocumentManagementUseCase(
            self.parsers,
            self.rag_engine,
            self.document_repo
        )
        self.history_use_cases = HistoryManagementUseCase(self.history_repo)
        self.settings_use_cases = SettingsUseCase(self.settings_repo, self.audio_capture)

        self.logger.info("Contenedor de dependencias de Remodax inicializado con éxito.")
