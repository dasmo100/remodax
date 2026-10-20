# Especificación de Ciberseguridad y Privacidad - Remodax

Remodax incorpora controles estrictos de seguridad por diseño (Security by Design) para garantizar que las credenciales del usuario, los documentos corporativos o personales y el audio capturado permanezcan protegidos en todo momento.

---

## 1. Almacenamiento Seguro de Credenciales (Windows Credential Manager)

- **Principio:** Nunca almacenar API Keys ni contraseñas en archivos `.env`, archivos de configuración de texto plano, código fuente o bases de datos locales.
- **Implementación:**
  - Se utiliza la biblioteca estándar del sistema operativo a través de `keyring`, delegando el cifrado en el subsistema nativo **Windows Credential Manager** (`Windows Credential Vault`).
  - Identificador de Servicio: `Remodax_Desktop_App`.
  - Usuarios: `groq_api_key`, `gemini_api_key`.
  - Las claves se leen únicamente en memoria en el momento exacto de ejecutar la llamada a la API y no se persisten en ninguna variable global permanente.

---

## 2. Enmascaramiento y Prevención de Exposición (Zero-Leak Policy)

- **En la Interfaz de Usuario:**
  - Los campos de entrada utilizan `MaskedKeyInput` con modo contraseña (`QLineEdit.EchoMode.Password`) por defecto.
  - Al visualizar claves existentes, se enmascaran permanentemente mostrando únicamente prefijos y sufijos no sensibles:
    ```
    gsk_1234567890abcdef12345678  -->  gsk_••••••••5678
    ```
- **En los Logs y Consola:**
  - Se implementó un filtro de logging `SensitiveDataFilter` (`src/config/logging_config.py`).
  - Intercepta mediante expresiones regulares cualquier patrón coincidente con claves de Groq (`gsk_...`), Google Gemini (`AIzaSy...`), tokens de portador o sk keys y los reemplaza por `[REDACTED_API_KEY]` antes de emitirlos.

---

## 3. Política de Cero Persistencia de Audio (Zero Audio Persistence)

- **Problema de Privacidad:** Grabar audio de llamadas, reuniones o entrevistas en disco expone información confidencial a accesos no autorizados o indexaciones forenses.
- **Garantía Remodax:**
  - El motor de audio captura mediante **WASAPI Loopback** directamente hacia un búfer circular efímero en memoria RAM (`EphemeralAudioBuffer`).
  - El búfer es consumido directamente por el modelo de transcripción Whisper y se descarta o sobrescribe de forma inmediata.
  - No se generan archivos `.wav`, `.mp3` ni temporales en disco por defecto.

---

## 4. Privacidad Documental y Consentimiento Explícito para RAG

- **Aislamiento Local:**
  - Los archivos PDF y Word procesados residen únicamente en el almacenamiento local del usuario (`%LOCALAPPDATA%\Remodax\documents`).
  - La indexación de fragmentos para RAG se realiza de forma local mediante `LocalRAGEngine` (sin enviar documentos a bases de datos vectoriales en la nube de terceros).
- **Consentimiento por Consulta:**
  - En la vista de entrevistas existe la casilla explícita: **"Adjuntar contexto de documentos (RAG)"**.
  - Si el usuario no activa esta opción, **ningún fragmento ni metadato de sus documentos es incluido en la llamada a las APIs externas de Groq o Gemini**.

---

## 5. Prevención de Fugas en Control de Versiones (.gitignore)

El archivo `.gitignore` excluye taxativamente:
- Bases de datos SQLite: `*.db`, `*.sqlite`, `*.sqlite3`, `data/`, `storage/`.
- Archivos confidenciales: `.env`, `.env.*`, `*credentials*`, `*secret*`, `api_keys.json`.
- Documentos privados: `*.pdf`, `*.docx`, `documents_storage/`.
- Archivos y búferes de audio: `*.wav`, `*.mp3`, `audio_cache/`.
- Compilaciones y artefactos de distribución: `dist/`, `build/`, `*.exe`, `*.spec`.
