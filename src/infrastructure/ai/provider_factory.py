"""
Remodax - AI Provider Factory
Provides dynamic instantiation and resolution of configured AI clients.
"""

from typing import Dict
from src.domain.entities.ai_models import AIProviderType
from src.domain.ports.ai_port import IAIClient, IAIProviderFactory
from src.infrastructure.ai.groq_provider import GroqProvider
from src.infrastructure.ai.gemini_provider import GeminiProvider


class AIProviderFactory(IAIProviderFactory):
    """Concrete factory resolving AI clients by enum type."""

    def __init__(self, groq_provider: GroqProvider, gemini_provider: GeminiProvider):
        self._providers: Dict[AIProviderType, IAIClient] = {
            AIProviderType.GROQ: groq_provider,
            AIProviderType.GEMINI: gemini_provider,
        }

    def get_client(self, provider_type: AIProviderType) -> IAIClient:
        client = self._providers.get(provider_type)
        if not client:
            raise ValueError(f"Proveedor no soportado: {provider_type}")
        return client
