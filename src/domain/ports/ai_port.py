"""
Remodax - AI Domain Ports
Abstract interfaces for AI LLM providers and streaming response engines.
"""

from abc import ABC, abstractmethod
from typing import Iterator
from src.domain.entities.ai_models import AIRequest, AIResponseChunk, AIProviderType


class IAIClient(ABC):
    """Port for communicating with an individual AI Provider (Groq, Gemini)."""

    @property
    @abstractmethod
    def provider_type(self) -> AIProviderType:
        """Returns provider identifier."""
        pass

    @abstractmethod
    def generate_stream(self, request: AIRequest, model_name: str) -> Iterator[AIResponseChunk]:
        """Streams response tokens from provider API."""
        pass

    @abstractmethod
    def test_connection(self, api_key: str) -> bool:
        """Validates API Key connectivity with provider."""
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """Returns list of models supported by this provider."""
        pass


class IAIProviderFactory(ABC):
    """Factory interface for instantiating or resolving AI clients."""

    @abstractmethod
    def get_client(self, provider_type: AIProviderType) -> IAIClient:
        """Returns client implementation matching the provider."""
        pass
