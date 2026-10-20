"""
Remodax - AI Domain Entities
Defines provider types, request payloads, and streaming response chunks.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


from src.config.constants import DEFAULT_INTERVIEW_SYSTEM_PROMPT


class AIProviderType(str, Enum):
    """Supported AI Providers."""
    GROQ = "GroqCloud"
    GEMINI = "Gemini"


@dataclass
class AIRequest:
    """Represents a prompt payload dispatched to an LLM provider."""
    prompt: str
    system_instruction: str = DEFAULT_INTERVIEW_SYSTEM_PROMPT
    context_chunks: List[str] = field(default_factory=list)
    temperature: float = 0.5
    max_tokens: int = 220
    allow_external_rag: bool = False  # Privacy guardrail: must be explicitly approved


@dataclass
class AIResponseChunk:
    """Streaming chunk received from AI provider."""
    delta_text: str = ""
    is_final: bool = False
    error_message: Optional[str] = None
    latency_ms: float = 0.0
