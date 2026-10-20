"""
Remodax - GroqCloud AI Provider Infrastructure
Implements real streaming completions and verification via GroqCloud SDK.
"""

import logging
from typing import Iterator, List
from src.config.constants import (
    KEYRING_SERVICE_NAME,
    KEYRING_GROQ_USER,
    DEFAULT_GROQ_MODEL,
    GROQ_SUPPORTED_MODELS,
)
from src.domain.entities.ai_models import AIRequest, AIResponseChunk, AIProviderType
from src.domain.ports.ai_port import IAIClient
from src.domain.ports.security_port import ISecretsManager
from src.domain.exceptions import AIProviderException

logger = logging.getLogger("remodax.ai.groq")


class GroqProvider(IAIClient):
    """Client for GroqCloud LLM completions."""

    def __init__(self, secrets_manager: ISecretsManager):
        self._secrets = secrets_manager

    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.GROQ

    def get_supported_models(self) -> List[str]:
        return list(GROQ_SUPPORTED_MODELS)

    def _get_api_key(self) -> str:
        key = self._secrets.get_secret(KEYRING_SERVICE_NAME, KEYRING_GROQ_USER)
        return key.strip() if key else ""

    def test_connection(self, api_key: str) -> bool:
        """
        Validates API Key with a real call to Groq servers.
        Never simulates success: returns True only if authenticated.
        """
        if not api_key or not api_key.strip():
            raise AIProviderException("No se ha proporcionado una API Key para probar.")

        clean_key = api_key.strip()

        try:
            import groq

            client = groq.Groq(api_key=clean_key)
            # Real live verification call to Groq
            client.models.list()
            logger.info("Verificación exitosa con la API de GroqCloud.")
            return True

        except ImportError as ex:
            logger.error("SDK 'groq' no disponible: %s", str(ex))
            raise AIProviderException("La biblioteca 'groq' no está instalada en el entorno.") from ex

        except groq.AuthenticationError as ex:
            logger.warning("Fallo de autenticación con Groq API Key.")
            raise AIProviderException("API Key de Groq inválida o no autorizada (Error 401).") from ex

        except groq.RateLimitError as ex:
            logger.warning("Límite de tasa alcanzado en Groq.")
            raise AIProviderException("Límite de cuota o peticiones excedido en Groq (Error 429).") from ex

        except groq.APIConnectionError as ex:
            logger.error("Error de conexión de red con Groq: %s", str(ex))
            raise AIProviderException("Error de conexión con los servidores de Groq. Verifica tu acceso a internet.") from ex

        except groq.APIStatusError as ex:
            logger.error("Error de estado devuelto por Groq: %s", str(ex))
            raise AIProviderException(f"Error de servidor Groq ({ex.status_code}).") from ex

        except Exception as ex:
            logger.error("Error inesperado validando Groq: %s", str(ex))
            raise AIProviderException(f"Error durante la verificación con Groq: {str(ex)}") from ex

    def generate_stream(self, request: AIRequest, model_name: str = DEFAULT_GROQ_MODEL) -> Iterator[AIResponseChunk]:
        api_key = self._get_api_key()
        if not api_key:
            raise AIProviderException(
                "No se ha configurado la API Key de Groq. "
                "Por favor ingrésala y guárdala en la sección 'Configuración API'."
            )

        # Assemble chat messages
        messages = [{"role": "system", "content": request.system_instruction}]

        # Inject RAG context only if authorized
        if request.allow_external_rag and request.context_chunks:
            context_text = "\n---\n".join(request.context_chunks)
            messages.append({
                "role": "system",
                "content": (
                    f"Contexto documental relevante de apoyo:\n{context_text}\n\n"
                    "Instrucción estricta: Utiliza este contenido como contexto para responder sin inventar información. "
                    "No especules ni agregues datos inexistentes. Si la información solicitada no se encuentra en el contexto proporcionado, "
                    "indícalo con total honestidad, claridad y profesionalismo."
                )
            })

        messages.append({"role": "user", "content": request.prompt})

        try:
            import groq

            client = groq.Groq(api_key=api_key)
            selected_model = model_name if model_name in GROQ_SUPPORTED_MODELS else DEFAULT_GROQ_MODEL

            # Low-latency optimization for real-time interview answers:
            # - reasoning_format="hidden": Prevents reasoning tokens from consuming generation budget
            # - max_tokens=max(request.max_tokens, 800): Ample headroom so answers never hit 'length' prematurely
            create_params = {
                "model": selected_model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": max(request.max_tokens, 800),
                "stream": True,
            }
            if "oss" in selected_model.lower() or "qwen" in selected_model.lower():
                create_params["reasoning_format"] = "hidden"
                create_params["reasoning_effort"] = "low"

            try:
                stream = client.chat.completions.create(**create_params)
            except Exception as param_err:
                logger.debug("Reintentando Groq sin parámetros de reasoning: %s", param_err)
                create_params.pop("reasoning_format", None)
                create_params.pop("reasoning_effort", None)
                stream = client.chat.completions.create(**create_params)

            has_content = False
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        has_content = True
                        yield AIResponseChunk(
                            delta_text=delta.content,
                            is_final=False
                        )
                    elif not has_content and hasattr(delta, "reasoning") and delta.reasoning:
                        # Fallback: if model only emitted reasoning tokens and no content yet
                        yield AIResponseChunk(
                            delta_text=delta.reasoning,
                            is_final=False
                        )

            yield AIResponseChunk(delta_text="", is_final=True)

        except ImportError as ex:
            raise AIProviderException("La biblioteca 'groq' no está disponible.") from ex

        except groq.AuthenticationError as ex:
            raise AIProviderException("Error de autenticación: Tu API Key de Groq es inválida o expiró.") from ex

        except groq.RateLimitError as ex:
            raise AIProviderException("Límite de tasa de Groq excedido (Rate Limit 429). Espera unos segundos e intenta nuevamente.") from ex

        except groq.APIConnectionError as ex:
            raise AIProviderException("Fallo de conexión al comunicarse con los servidores de Groq.") from ex

        except groq.APIStatusError as ex:
            raise AIProviderException(f"Error en la API de Groq ({ex.status_code}): {ex.message}") from ex

        except Exception as ex:
            raise AIProviderException(f"Error durante la generación con Groq: {str(ex)}") from ex
