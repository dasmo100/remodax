"""
Remodax - Sanitized Logging Configuration
Ensures that no API Keys, secrets, or confidential tokens are ever written to console or logs.
"""

import logging
import re
from typing import Any

# Regular expressions detecting common API key patterns
KEY_PATTERNS = [
    re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE),          # Groq API Keys
    re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}", re.IGNORECASE),       # Google Gemini / GCP Keys
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),           # Generic OpenAI / LLM Keys
    re.compile(r"bearer\s+[a-zA-Z0-9._-]{20,}", re.IGNORECASE),  # Bearer tokens
]


class SensitiveDataFilter(logging.Filter):
    """
    Log filter that intercepts and sanitizes sensitive credentials
    before they are dispatched to stdout, stderr, or log files.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @staticmethod
    def _sanitize(text: str) -> str:
        sanitized = text
        for pattern in KEY_PATTERNS:
            sanitized = pattern.sub("[REDACTED_API_KEY]", sanitized)
        return sanitized


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures application logger with cybersecurity masking filters."""
    logger = logging.getLogger("remodax")
    logger.setLevel(level)

    # Avoid duplicate handlers if reconfigured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger
