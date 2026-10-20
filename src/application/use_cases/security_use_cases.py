"""
Remodax - Security Use Cases
Implements credential vault management, API key testing, and masking.
"""

from typing import List
from src.config.constants import (
    KEYRING_SERVICE_NAME,
    KEYRING_GROQ_USER,
    KEYRING_GEMINI_USER,
    PROVIDER_GROQ,
    PROVIDER_GEMINI,
)
from src.domain.ports.security_port import ISecretsManager
from src.domain.ports.ai_port import IAIProviderFactory
from src.domain.entities.ai_models import AIProviderType
from src.domain.exceptions import AIProviderException
from src.application.dtos.api_key_dto import (
    ApiKeyStatusDTO,
    SaveApiKeyRequestDTO,
    TestApiKeyResultDTO,
)


class ManageApiKeysUseCase:
    """Orchestrates secure storage and query of API keys in Windows Credential Manager."""

    def __init__(self, secrets_manager: ISecretsManager, ai_factory: IAIProviderFactory):
        self._secrets = secrets_manager
        self._ai_factory = ai_factory

    def get_provider_key_status(self, provider: str) -> ApiKeyStatusDTO:
        username = self._get_username_for_provider(provider)
        secret = self._secrets.get_secret(KEYRING_SERVICE_NAME, username)
        is_configured = bool(secret and secret.strip())
        masked = self._secrets.mask_secret(secret)
        return ApiKeyStatusDTO(
            provider=provider,
            is_configured=is_configured,
            masked_key=masked
        )

    def get_all_keys_status(self) -> List[ApiKeyStatusDTO]:
        return [
            self.get_provider_key_status(PROVIDER_GROQ),
            self.get_provider_key_status(PROVIDER_GEMINI),
        ]

    def save_api_key(self, request: SaveApiKeyRequestDTO) -> bool:
        if not request.api_key or not request.api_key.strip():
            return False
        username = self._get_username_for_provider(request.provider)
        return self._secrets.save_secret(
            KEYRING_SERVICE_NAME,
            username,
            request.api_key.strip()
        )

    def delete_api_key(self, provider: str) -> bool:
        username = self._get_username_for_provider(provider)
        return self._secrets.delete_secret(KEYRING_SERVICE_NAME, username)

    def test_api_key(self, provider: str, custom_key: str = "") -> TestApiKeyResultDTO:
        """Validates key by attempting a lightweight API test call."""
        target_key = custom_key.strip()
        if not target_key:
            username = self._get_username_for_provider(provider)
            saved = self._secrets.get_secret(KEYRING_SERVICE_NAME, username)
            target_key = saved.strip() if saved else ""

        if not target_key:
            return TestApiKeyResultDTO(
                provider=provider,
                success=False,
                message="No se ha ingresado ninguna clave para probar."
            )

        try:
            enum_type = AIProviderType.GROQ if provider == PROVIDER_GROQ else AIProviderType.GEMINI
            client = self._ai_factory.get_client(enum_type)
            is_valid = client.test_connection(target_key)
            if is_valid:
                return TestApiKeyResultDTO(
                    provider=provider,
                    success=True,
                    message="Conexión exitosa con el proveedor de IA."
                )
            return TestApiKeyResultDTO(
                provider=provider,
                success=False,
                message="La API Key fue rechazada por el servidor."
            )
        except AIProviderException as ex:
            return TestApiKeyResultDTO(
                provider=provider,
                success=False,
                message=str(ex)
            )
        except Exception as ex:
            return TestApiKeyResultDTO(
                provider=provider,
                success=False,
                message=f"Error durante la prueba de conexión: {str(ex)}"
            )

    @staticmethod
    def _get_username_for_provider(provider: str) -> str:
        if provider == PROVIDER_GROQ:
            return KEYRING_GROQ_USER
        elif provider == PROVIDER_GEMINI:
            return KEYRING_GEMINI_USER
        return f"{provider.lower()}_api_key"
