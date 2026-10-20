# Estado de Módulos y Hoja de Ruta - Remodax

Este documento detalla el estado actual de la arquitectura base y los pasos pendientes para el desarrollo integral de cada módulo obligatorio.

---

## 1. Módulo: Entrevistas en Tiempo Real
- **Estado Actual (Arquitectura Base):**
  - [x] Contratos de dominio definidos (`IAudioCaptureService`, `IAudioTranscriber`, `QuestionAnswer`, `InterviewSession`).
  - [x] Caso de uso `InterviewSessionUseCase` implementado.
  - [x] Búfer circular volátil en memoria RAM (`EphemeralAudioBuffer`) con política de cero persistencia en disco.
  - [x] Adaptador de captura WASAPI Loopback para Windows mediante `sounddevice` con manejo de fallback.
  - [x] Adaptador de transcripción Whisper con `faster-whisper` estructurado.
  - [x] Interfaz `InterviewView` y `InterviewViewModel` con controles de inicio/fin, caja de transcripción, visor de streaming y checkbox de autorización RAG.
- **Pendiente de Implementación Fina:**
  - [ ] Descarga automática y caché local de pesos del modelo Whisper (`tiny`, `base`, `small`).
  - [ ] Calibración fina de Voice Activity Detection (VAD) para detección automática de silencios entre preguntas.
  - [ ] Soporte para visualizador gráfico de forma de onda (audio visualizer widget).

---

## 2. Módulo: Gestión de Documentos y RAG Local
- **Estado Actual (Arquitectura Base):**
  - [x] Entidades de dominio `Document` y `DocumentChunk`.
  - [x] Contratos `IDocumentParser`, `IRAGService`, `IDocumentRepository`.
  - [x] Parsers para PDF (`PyMuPDFParser`) y Word (`DocxParser`) con división de fragmentos (sliding window).
  - [x] Motor de búsqueda local en memoria `LocalRAGEngine` (BM25/TF-IDF) completamente offline y privado.
  - [x] Repositorio SQLite `SQLiteDocumentRepository` para persistencia de metadatos.
  - [x] Interfaz `DocumentsView` y `DocumentsViewModel` con explorador de archivos, tabla y eliminación.
- **Pendiente de Implementación Fina:**
  - [ ] Integración opcional de modelos locales de embeddings vectoriales (ej. all-MiniLM-L6-v2 mediante ONNX Runtime).
  - [ ] Soporte para visualización previa del documento dentro de la interfaz.

---

## 3. Módulo: Configuración de API Keys y Seguridad
- **Estado Actual (Arquitectura Base):**
  - [x] Contrato `ISecretsManager` y modelo `ApiKeyStatusDTO`.
  - [x] Adaptador `WindowsCredentialManager` utilizando `keyring` (Windows Credential Vault).
  - [x] Utilidad de enmascaramiento `mask_api_key` (`gsk_••••••••1234`).
  - [x] Filtro de logging `SensitiveDataFilter` para anonimizar credenciales en logs.
  - [x] Caso de uso `ManageApiKeysUseCase` para guardar, probar, obtener y eliminar claves.
  - [x] Interfaz `ApiKeysView` con `MaskedKeyInput` y botones de prueba de conexión en hilos secundarios.
- **Pendiente de Implementación Fina:**
  - [ ] Soporte para cuotas de uso y visualización del balance disponible si la API del proveedor lo expone.

---

## 4. Módulo: Inteligencia Artificial y Streaming
- **Estado Actual (Arquitectura Base):**
  - [x] Contratos `IAIClient` y `IAIProviderFactory`.
  - [x] Adaptador `GroqProvider` para modelos Llama 3.3 / Llama 3.1 con streaming ultrarrápido.
  - [x] Adaptador `GeminiProvider` para la API oficial de Google Gemini (`google-genai`).
  - [x] Fábrica `AIProviderFactory` para conmutación dinámica de proveedores.
  - [x] Inyección condicional de contexto RAG supeditada al consentimiento explícito del usuario.
- **Pendiente de Implementación Fina:**
  - [ ] Parámetros avanzados ajustables por el usuario (temperatura, top_p, max_tokens, system prompt personalizado).
  - [ ] Mecanismo de fallback automático: si Groq agota rate limits, consultar automáticamente a Gemini.

---

## 5. Módulo: Historial de Consultas
- **Estado Actual (Arquitectura Base):**
  - [x] Contrato `IHistoryRepository` y DTOs de historial.
  - [x] Implementación `SQLiteHistoryRepository` con esquema relacional SQLite (`sessions` y `qa_records`).
  - [x] Caso de uso `HistoryManagementUseCase` con búsqueda por palabras clave y limpieza total.
  - [x] Interfaz `HistoryView` con tabla de registros y barra de filtrado en tiempo real.
- **Pendiente de Implementación Fina:**
  - [ ] Exportación de historial a formatos externos (CSV, Markdown o JSON).
  - [ ] Filtrado por rango de fechas o proveedor de IA.

---

## 6. Módulo: Configuración y Preferencias
- **Estado Actual (Arquitectura Base):**
  - [x] Contrato `ISettingsRepository` y entidad `UserSettings`.
  - [x] Implementación `SQLiteSettingsRepository` con almacenamiento clave-valor.
  - [x] Caso de uso `SettingsUseCase` con enumeración de hardware de audio disponible en Windows.
  - [x] Interfaz `SettingsView` con selector de dispositivos, tamaño de modelo Whisper y políticas de privacidad fijas.
- **Pendiente de Implementación Fina:**
  - [ ] Prueba de audio en vivo (mic check) con barra de nivel de volumen (VU meter).
  - [ ] Selección de atajos de teclado globales de Windows (hotkeys) para pausar o activar la IA.
