"""
Remodax - Google Gemini AI Provider Infrastructure
Implements real streaming completions and verification via Google GenAI SDK.
"""

import logging
from typing import Iterator, List
from src.config.constants import (
    KEYRING_SERVICE_NAME,
    KEYRING_GEMINI_USER,
    DEFAULT_GEMINI_MODEL,
    GEMINI_SUPPORTED_MODELS,
)
from src.domain.entities.ai_models import AIRequest, AIResponseChunk, AIProviderType
from src.domain.ports.ai_port import IAIClient
from src.domain.ports.security_port import ISecretsManager
from src.domain.exceptions import AIProviderException

logger = logging.getLogger("remodax.ai.gemini")


class GeminiProvider(IAIClient):
    """Client for Google Gemini LLM completions."""

    def __init__(self, secrets_manager: ISecretsManager):
        self._secrets = secrets_manager

    @property
    def provider_type(self) -> AIProviderType:
        return AIProviderType.GEMINI

    def get_supported_models(self) -> List[str]:
        return list(GEMINI_SUPPORTED_MODELS)

    def _get_api_key(self) -> str:
        key = self._secrets.get_secret(KEYRING_SERVICE_NAME, KEYRING_GEMINI_USER)
        return key.strip() if key else ""

    def test_connection(self, api_key: str) -> bool:
        """
        Validates API Key with a real call to Google Gemini servers.
        Never simulates success: returns True only if authenticated.
        """
        if not api_key or not api_key.strip():
            raise AIProviderException("No se ha proporcionado una API Key para probar.")

        clean_key = api_key.strip()

        try:
            from google import genai
            from google.genai import errors

            client = genai.Client(api_key=clean_key)
            # Real live verification call to Gemini
            client.models.list()
            logger.info("Verificación exitosa con la API de Google Gemini.")
            return True

        except ImportError as ex:
            logger.error("SDK 'google-genai' no disponible: %s", str(ex))
            raise AIProviderException("La biblioteca 'google-genai' no está instalada en el entorno.") from ex

        except Exception as ex:
            # Inspect Gemini specific errors
            err_type = type(ex).__name__
            err_msg = str(ex)

            if "400" in err_msg or "API key not valid" in err_msg or "INVALID_ARGUMENT" in err_msg:
                logger.warning("Fallo de autenticación con Gemini API Key: Clave inválida.")
                raise AIProviderException("API Key de Google Gemini inválida o con formato erróneo (Error 400).") from ex

            if "403" in err_msg or "PERMISSION_DENIED" in err_msg:
                logger.warning("Permiso denegado con Gemini API Key.")
                raise AIProviderException("Acceso denegado a Google Gemini API (Error 403). Verifica los permisos del proyecto.") from ex

            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                logger.warning("Cuota de Gemini agotada o límite de tasa alcanzado.")
                raise AIProviderException("Límite de cuota o peticiones excedido en Gemini (Error 429).") from ex

            if "Connection" in err_type or "connect" in err_msg.lower() or "socket" in err_msg.lower() or "winerror" in err_msg.lower():
                logger.error("Error de conexión con Google Gemini: %s", err_msg)
                raise AIProviderException("Error de conexión con los servidores de Google Gemini. Verifica tu red.") from ex

            logger.error("Error durante validación de Gemini: %s", err_msg)
            raise AIProviderException(f"Error devuelto por Google Gemini: {err_msg}") from ex

    def generate_stream(self, request: AIRequest, model_name: str = DEFAULT_GEMINI_MODEL) -> Iterator[AIResponseChunk]:
        api_key = self._get_api_key()
        if not api_key:
            raise AIProviderException(
                "No se ha configurado la API Key de Gemini. "
                "Por favor ingrésala y guárdala en la sección 'Configuración API'."
            )

        # Assemble prompt contents (RAG context + question)
        prompt_parts = []
        if request.allow_external_rag and request.context_chunks:
            context_text = "\n---\n".join(request.context_chunks)
            prompt_parts.append(f"Contexto documental de apoyo:\n{context_text}\n")

        prompt_parts.append(f"Pregunta del entrevistador:\n{request.prompt}")
        prompt_content = "\n".join(prompt_parts)

        try:
            from google import genai
            from google.genai import errors, types

            client = genai.Client(api_key=api_key)
            # Automatic upgrade if deprecated/legacy model requested
            if not model_name or "2.5-flash" in model_name or model_name not in GEMINI_SUPPORTED_MODELS:
                selected_model = DEFAULT_GEMINI_MODEL
            else:
                selected_model = model_name

            # Ultra-low latency optimization for live spoken interviews:
            # - thinking_level="low": Minimizes reasoning latency so streaming starts immediately (<1s)
            # - max_output_tokens=350: Capping avoids runaway generation and speeds up response completion
            thinking_cfg = None
            try:
                if "2.5" in selected_model:
                    thinking_cfg = types.ThinkingConfig(thinking_budget=0)
                elif "lite" in selected_model.lower():
                    thinking_cfg = types.ThinkingConfig(thinking_level="minimal")
                else:
                    thinking_cfg = types.ThinkingConfig(thinking_level="low")
            except Exception as cfg_err:
                logger.debug("No se pudo configurar thinking_config: %s", cfg_err)

            config = types.GenerateContentConfig(
                system_instruction=request.system_instruction or None,
                temperature=request.temperature,
                max_output_tokens=220,
                thinking_config=thinking_cfg,
            )

            try:
                response = client.models.generate_content_stream(
                    model=selected_model,
                    contents=prompt_content,
                    config=config
                )

                for chunk in response:
                    if chunk.text:
                        yield AIResponseChunk(delta_text=chunk.text, is_final=False)

                yield AIResponseChunk(delta_text="", is_final=True)
                return

            except Exception as stream_ex:
                # If thinking_config is rejected by the endpoint, retry without thinking_config
                if "thinking" in str(stream_ex).lower() and config and config.thinking_config:
                    logger.warning("Reintentando Gemini sin thinking_config: %s", stream_ex)
                    config.thinking_config = None
                    retry_resp = client.models.generate_content_stream(
                        model=selected_model,
                        contents=prompt_content,
                        config=config
                    )
                    for chunk in retry_resp:
                        if chunk.text:
                            yield AIResponseChunk(delta_text=chunk.text, is_final=False)
                    yield AIResponseChunk(delta_text="", is_final=True)
                    return

                # If requested model is not found or deprecated, seamlessly retry with DEFAULT_GEMINI_MODEL
                if ("404" in str(stream_ex) or "NOT_FOUND" in str(stream_ex) or "no longer available" in str(stream_ex)) and selected_model != DEFAULT_GEMINI_MODEL:
                    logger.warning("Modelo %s no disponible, reintentando con %s: %s", selected_model, DEFAULT_GEMINI_MODEL, stream_ex)
                    fallback_response = client.models.generate_content_stream(
                        model=DEFAULT_GEMINI_MODEL,
                        contents=prompt_content,
                        config=config
                    )
                    for chunk in fallback_response:
                        if chunk.text:
                            yield AIResponseChunk(delta_text=chunk.text, is_final=False)
                    yield AIResponseChunk(delta_text="", is_final=True)
                    return

                # If rate-limited or quota exhausted on free tier (e.g. gemini-3.8-flash 20 req/day cap),
                # seamlessly failover to ultra-fast gemini-3.5-flash-lite
                if ("429" in str(stream_ex) or "RESOURCE_EXHAUSTED" in str(stream_ex)) and selected_model != "gemini-3.5-flash-lite":
                    logger.warning("Límite de cuota en %s, failover automático a gemini-3.5-flash-lite", selected_model)
                    lite_config = types.GenerateContentConfig(
                        system_instruction=request.system_instruction or None,
                        temperature=request.temperature,
                        max_output_tokens=350,
                    )
                    fallback_response = client.models.generate_content_stream(
                        model="gemini-3.5-flash-lite",
                        contents=prompt_content,
                        config=lite_config
                    )
                    for chunk in fallback_response:
                        if chunk.text:
                            yield AIResponseChunk(delta_text=chunk.text, is_final=False)
                    yield AIResponseChunk(delta_text="", is_final=True)
                    return

                raise stream_ex

        except ImportError as ex:
            raise AIProviderException("La biblioteca 'google-genai' no está disponible.") from ex

        except Exception as ex:
            err_msg = str(ex)
            if "400" in err_msg or "API key not valid" in err_msg:
                raise AIProviderException("Error de autenticación: Tu API Key de Gemini es inválida.") from ex
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                raise AIProviderException("Límite de cuota de Gemini excedido (Rate Limit 429). Espera unos segundos.") from ex
            if "404" in err_msg or "NOT_FOUND" in err_msg or "no longer available" in err_msg:
                raise AIProviderException(f"El modelo de Gemini solicitado no está disponible. Usa el modelo recomendado: {DEFAULT_GEMINI_MODEL}.") from ex
            if "Connection" in type(ex).__name__ or "connect" in err_msg.lower():
                raise AIProviderException("Fallo de conexión al comunicarse con los servidores de Google Gemini.") from ex

            raise AIProviderException(f"Error durante la generación con Gemini: {err_msg}") from ex
