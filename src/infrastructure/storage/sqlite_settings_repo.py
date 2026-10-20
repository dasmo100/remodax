"""
Remodax - SQLite Settings Repository Infrastructure
Implements ISettingsRepository for persisting local non-sensitive application preferences.
"""

from src.config.constants import (
    PROVIDER_GROQ,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_WHISPER_MODEL,
    DEFAULT_INTERVIEW_SYSTEM_PROMPT,
)
from src.domain.entities.settings_entity import UserSettings, AudioSourceType
from src.domain.ports.storage_port import ISettingsRepository
from src.infrastructure.storage.database import SQLiteDatabase


class SQLiteSettingsRepository(ISettingsRepository):
    """Stores user preferences in local SQLite."""

    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def load_settings(self) -> UserSettings:
        with self._db.get_connection() as conn:
            cur = conn.execute("SELECT key, value FROM user_settings;")
            rows = {row["key"]: row["value"] for row in cur.fetchall()}

        if not rows:
            return UserSettings()

        source_val = rows.get("audio_source", AudioSourceType.WASAPI_LOOPBACK.value)
        source_enum = (
            AudioSourceType.MICROPHONE
            if "micr" in str(source_val).lower()
            else AudioSourceType.WASAPI_LOOPBACK
        )

        try:
            device_idx = int(rows.get("audio_device_index", -1))
        except (ValueError, TypeError):
            device_idx = -1

        stored_model = rows.get("active_model", DEFAULT_GROQ_MODEL)
        if stored_model == "gemini-2.5-flash":
            stored_model = DEFAULT_GEMINI_MODEL

        return UserSettings(
            active_provider=rows.get("active_provider", PROVIDER_GROQ),
            active_model=stored_model,
            audio_source=source_enum,
            audio_device_index=device_idx,
            whisper_model=rows.get("whisper_model", DEFAULT_WHISPER_MODEL),
            allow_external_rag=rows.get("allow_external_rag", "0") == "1",
            persist_audio=rows.get("persist_audio", "0") == "1",
            dark_mode=rows.get("dark_mode", "1") == "1",
            system_prompt=(
                DEFAULT_INTERVIEW_SYSTEM_PROMPT
                if (
                    "En mi experiencia...'" in rows.get("system_prompt", "")
                    or "HABLA EN PRIMERA PERSONA" in rows.get("system_prompt", "")
                    or "entre 45 y 75 palabras" in rows.get("system_prompt", "")
                )
                else rows.get("system_prompt", DEFAULT_INTERVIEW_SYSTEM_PROMPT)
            )
        )

    def save_settings(self, settings: UserSettings) -> None:
        source_val = (
            settings.audio_source.value
            if isinstance(settings.audio_source, AudioSourceType)
            else str(settings.audio_source)
        )
        data = {
            "active_provider": settings.active_provider,
            "active_model": settings.active_model,
            "audio_source": source_val,
            "audio_device_index": str(settings.audio_device_index),
            "whisper_model": settings.whisper_model,
            "allow_external_rag": "1" if settings.allow_external_rag else "0",
            "persist_audio": "1" if settings.persist_audio else "0",
            "dark_mode": "1" if settings.dark_mode else "0",
            "system_prompt": settings.system_prompt,
        }
        with self._db.get_connection() as conn:
            for k, v in data.items():
                conn.execute("""
                    INSERT INTO user_settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value;
                """, (k, v))
            conn.commit()
