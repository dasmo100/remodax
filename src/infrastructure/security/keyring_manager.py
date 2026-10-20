"""
Remodax - Keyring Security Infrastructure
Implements ISecretsManager utilizing Windows Credential Manager via python keyring.
"""

from typing import Optional
import logging
import keyring
from keyring.errors import KeyringError
from src.domain.ports.security_port import ISecretsManager
from src.infrastructure.security.mask_utils import mask_api_key

import os

logger = logging.getLogger("remodax.security")


class WindowsCredentialManager(ISecretsManager):
    """
    Secure storage adapter backed by Windows Credential Manager (via keyring).
    Guarantees no clear-text keys are stored in files or databases.
    """

    def __init__(self):
        self._in_memory_cache: dict[tuple[str, str], str] = {}

    def save_secret(self, service_name: str, username: str, secret_value: str) -> bool:
        if not secret_value or not secret_value.strip():
            return False
        clean_val = secret_value.strip()
        self._in_memory_cache[(service_name, username)] = clean_val
        try:
            keyring.set_password(service_name, username, clean_val)
            logger.info("Credencial '%s' almacenada exitosamente en Windows Credential Manager.", username)
            return True
        except Exception as ex:
            logger.error("Error al guardar credencial en el administrador de credenciales: %s", str(ex))
            # Even if keyring system service fails, keep active in memory for current session
            return True

    def get_secret(self, service_name: str, username: str) -> Optional[str]:
        # 1. Primary: Retrieve from Windows Credential Manager via keyring
        try:
            val = keyring.get_password(service_name, username)
            if val and val.strip():
                clean = val.strip()
                self._in_memory_cache[(service_name, username)] = clean
                return clean
        except Exception as ex:
            logger.warning("Aviso al consultar credencial '%s' en Windows Credential Manager: %s", username, str(ex))

        # 2. Secondary: Check active in-memory cache
        if (service_name, username) in self._in_memory_cache:
            return self._in_memory_cache[(service_name, username)]

        # 3. Tertiary: Check environment variables
        if "groq" in username.lower():
            env_val = os.getenv("GROQ_API_KEY")
            if env_val and env_val.strip():
                return env_val.strip()
        elif "gemini" in username.lower():
            env_val = os.getenv("GEMINI_API_KEY")
            if env_val and env_val.strip():
                return env_val.strip()

        return None

    def delete_secret(self, service_name: str, username: str) -> bool:
        self._in_memory_cache.pop((service_name, username), None)
        try:
            keyring.delete_password(service_name, username)
            logger.info("Credencial '%s' eliminada de Windows Credential Manager.", username)
            return True
        except Exception:
            # Often occurs if secret did not exist or access was denied
            return False

    def has_secret(self, service_name: str, username: str) -> bool:
        val = self.get_secret(service_name, username)
        return bool(val and val.strip())

    def mask_secret(self, secret_value: Optional[str]) -> str:
        return mask_api_key(secret_value)
