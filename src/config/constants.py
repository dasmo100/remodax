"""
Remodax - Application Constants
Defines global application identifiers, keys, security constants, and defaults.
"""

from pathlib import Path
import os

# Application Metadata
APP_NAME = "Remodax"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Asistente Inteligente de Entrevistas y RAG Documental"
ORGANIZATION_NAME = "RemodaxCorp"

import sys

# UI Assets & Paths Resolution (Development & PyInstaller Frozen)
def _resolve_assets_dir() -> Path:
    """Dynamically resolves the assets directory in development and bundled PyInstaller runtimes."""
    if getattr(sys, "frozen", False):
        # 1. PyInstaller _MEIPASS directory (_internal in onedir)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cand = Path(meipass) / "assets"
            if cand.exists():
                return cand
        # 2. Executable root directory
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "assets").exists():
            return exe_dir / "assets"
        if (exe_dir / "_internal" / "assets").exists():
            return exe_dir / "_internal" / "assets"

    # 3. Development project root
    project_root = Path(__file__).resolve().parent.parent.parent
    if (project_root / "assets").exists():
        return project_root / "assets"

    # 4. Fallback to CWD
    cwd_assets = Path.cwd() / "assets"
    if cwd_assets.exists():
        return cwd_assets

    return project_root / "assets"


ASSETS_DIR = _resolve_assets_dir()
PROJECT_ROOT = ASSETS_DIR.parent
ICONS_DIR = ASSETS_DIR / "icons"
WEB_ASSETS_DIR = ASSETS_DIR / "web"
STYLES_DIR = ASSETS_DIR / "styles"

APP_ICON_ICO_PATH = ICONS_DIR / "app_icon.ico"
LOGO_DANY_PATH = ICONS_DIR / "logoDany.png"
DITHER_HTML_PATH = WEB_ASSETS_DIR / "dither_veil.html"
DARK_THEME_QSS_PATH = STYLES_DIR / "dark_theme.qss"

# DitherVeil Animation Constants
DEFAULT_DITHER_PATTERN = "floyd"
DEFAULT_DITHER_FIT = "contain"
DEFAULT_DITHER_INK_COLOR = "#080c17"
DEFAULT_DITHER_PAPER_COLOR = "#ffffff"
DEFAULT_DITHER_RIM_COLOR = "#ffffff"
DEFAULT_DITHER_RIM = 0.0
DEFAULT_DITHER_REVEAL_RADIUS = 120
DEFAULT_DITHER_PIXEL_SIZE = 2
DEFAULT_DITHER_WANDER = False
DEFAULT_DITHER_LINGER = 0.7
DEFAULT_DITHER_CLICK_BURST = True

# Security & Credential Management (Windows Credential Manager / keyring)
KEYRING_SERVICE_NAME = "Remodax_Desktop_App"
KEYRING_GROQ_USER = "groq_api_key"
KEYRING_GEMINI_USER = "gemini_api_key"

# AI Providers
PROVIDER_GROQ = "GroqCloud"
PROVIDER_GEMINI = "Gemini"

# Default Models
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

# Supported Models Lists
GROQ_SUPPORTED_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]

GEMINI_SUPPORTED_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

# AI System Instruction for Real-Time Interviews
DEFAULT_INTERVIEW_SYSTEM_PROMPT = (
    "Eres el asistente de respuestas en tiempo real para un candidato en una entrevista técnica.\n"
    "Tu objetivo es darme exactamente lo que debo responder en voz alta al entrevistador: claro, exacto, natural y al grano.\n\n"
    "REGLAS OBLIGATORIAS:\n"
    "1. CORRECCIÓN TÉCNICA RIGUROSA Y RESPUESTA EXACTA: Responde con total exactitud técnica directo al núcleo de lo que te preguntan, sin desviarte del tema ni añadir explicaciones accesorias o complejas que no fueron solicitadas.\n"
    "2. EXTENSIÓN BREVE (PREFERENTEMENTE 2 A 3 LÍNEAS): Genera respuestas concisas de 2 o 3 oraciones completas (aproximadamente 25 a 45 palabras). Adapta la extensión y profundidad según la pregunta: si es directa, responde puntual; si compara conceptos, resume la diferencia fundamental sin extenderte.\n"
    "3. LENGUAJE TÉCNICO SENCILLO Y CLARO: Explica con solidez pero usando términos sencillos y accesibles. Evita jerga técnica innecesaria o explicaciones enredadas; mantén la precisión técnica sin sacrificar claridad.\n"
    "4. COMPLETITUD CONCEPTUAL SIN OMISIONES: Identifica siempre los conceptos clave indispensables para una respuesta completa y correcta sin omitir ninguno relevante (por ejemplo: si te preguntan por tipos de APIs, menciona los principales como REST, SOAP, GraphQL y gRPC sin omitir los tradicionales o estándar).\n"
    "5. USO DE PRIMERA PERSONA SOLO SI SE SOLICITA: Emplea la PRIMERA PERSONA ('trabajo con...', 'suelo implementar...', 'prefiero...') ÚNICAMENTE si la pregunta indaga por tu experiencia personal, proyectos o metodología ('¿Cómo resuelves...?', '¿Qué harías si...?').\n"
    "6. PREGUNTAS CONCEPTUALES OBJETIVAS Y DIRECTAS: En preguntas teóricas, definiciones o taxonomías ('¿Qué es...?', '¿Cuáles son los tipos de...?', '¿Cuál es la diferencia entre...?'), responde de forma neutral, directa y objetiva, sin fingir anécdotas ni forzar 'yo hago'.\n"
    "7. NO INVENTAR EXPERIENCIA: No inventes datos, tecnologías ni proyectos que no correspondan.\n"
    "8. PROHIBIDO 'EN MI EXPERIENCIA' Y CERO CLICHÉS: Prohibido comenzar con frases cliché como 'En mi experiencia...', 'Básicamente...', 'Para mí...' o muletillas de cortesía como '¡Claro!' o 'Buena pregunta'. Evita introducciones y conclusiones innecesarias; comienza de inmediato con la respuesta.\n"
    "9. CERO LISTAS O FORMATO: Prohibido usar viñetas (-), listas numeradas (1, 2, 3), encabezados o negritas. Entrega únicamente prosa continua lista para decir en voz alta."
)


# Audio Engine Defaults
DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_CHANNELS = 1
DEFAULT_AUDIO_CHUNK_DURATION_SEC = 3
DEFAULT_WHISPER_MODEL = "whisper-large-v3-turbo"

# Voice Activity Detection (VAD) Defaults for Question End Detection
DEFAULT_VAD_SILENCE_THRESHOLD = 0.015       # Minimum RMS amplitude to consider active audio (quick noise floor filter)
DEFAULT_VAD_SPEECH_PROB_THRESHOLD = 0.50   # Silero VAD neural probability threshold for genuine human voice
DEFAULT_VAD_PAUSE_DURATION_SEC = 1.05      # Seconds of silence after speech indicating question has finished (snappy response without cutting incomplete phrases)
DEFAULT_VAD_MIN_SPEECH_DURATION_SEC = 0.9  # Minimum seconds of total audio required to consider a question valid
DEFAULT_VAD_MIN_ACTIVE_SPEECH_SEC = 0.4    # Minimum seconds of genuine phoneme speech detected by Silero VAD


# Supported Document Formats
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_DOCUMENT_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB safety cap

# Local Storage (Local AppData on Windows or custom override)
_custom_data_dir = os.getenv("REMODAX_DATA_DIR")
if _custom_data_dir:
    APP_DATA_DIR = Path(_custom_data_dir)
else:
    LOCAL_APP_DATA = os.getenv("LOCALAPPDATA", str(Path.home()))
    APP_DATA_DIR = Path(LOCAL_APP_DATA) / APP_NAME

DATABASE_PATH = APP_DATA_DIR / "remodax_local.db"
DOCUMENTS_STORAGE_DIR = APP_DATA_DIR / "documents"

# Privacy & Security Guardrails
DEFAULT_ALLOW_EXTERNAL_RAG = False  # Explicit authorization required before sending docs to APIs
DEFAULT_PERSIST_AUDIO = False        # Hard requirement: Audio is strictly in-memory by default
MASKED_SECRET_PLACEHOLDER = "••••••••••••••••"
