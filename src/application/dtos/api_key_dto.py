"""
Remodax - API Key DTOs
Data Transfer Objects for security operations and key validation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiKeyStatusDTO:
    provider: str
    is_configured: bool
    masked_key: str  # Always masked, e.g. "gsk_••••••••1234"


@dataclass
class SaveApiKeyRequestDTO:
    provider: str
    api_key: str


@dataclass
class TestApiKeyResultDTO:
    provider: str
    success: bool
    message: str
