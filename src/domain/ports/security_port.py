"""
Remodax - Security Domain Ports
Abstract interface for Credential Manager interaction, key masking, and secrets hygiene.
"""

from abc import ABC, abstractmethod
from typing import Optional


class ISecretsManager(ABC):
    """Port for securely storing and accessing API credentials via OS Credential Vault."""

    @abstractmethod
    def save_secret(self, service_name: str, username: str, secret_value: str) -> bool:
        """Stores a secret securely in OS credential manager."""
        pass

    @abstractmethod
    def get_secret(self, service_name: str, username: str) -> Optional[str]:
        """Retrieves a secret from OS credential manager."""
        pass

    @abstractmethod
    def delete_secret(self, service_name: str, username: str) -> bool:
        """Removes a secret from OS credential manager."""
        pass

    @abstractmethod
    def has_secret(self, service_name: str, username: str) -> bool:
        """Checks if a secret is configured without exposing it."""
        pass

    @abstractmethod
    def mask_secret(self, secret_value: Optional[str]) -> str:
        """Masks secret to prevent UI or log exposure (e.g., 'gsk_••••••••1234')."""
        pass
