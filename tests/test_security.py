"""
Remodax - Unit Tests: Cybersecurity & Secrets Protection
Validates masking algorithms, logging sanitization, and credential handling.
"""

import logging
from src.infrastructure.security.mask_utils import mask_api_key
from src.config.logging_config import SensitiveDataFilter


def test_mask_api_key():
    # Long Groq style key
    groq_key = "gsk_1234567890abcdefghijklmn"
    masked = mask_api_key(groq_key)
    assert masked.startswith("gsk_")
    assert masked.endswith("klmn")
    assert "••••••••" in masked
    assert "abcdef" not in masked

    # Empty or None keys
    assert mask_api_key("") == "No configurada"
    assert mask_api_key(None) == "No configurada"

    # Short key
    assert mask_api_key("12345") == "••••••••"


def test_sensitive_data_log_filter():
    filter_obj = SensitiveDataFilter()

    # Create dummy log record with potential leaked key
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Iniciando conexión con key gsk_1234567890abcdef1234567890",
        args=(),
        exc_info=None
    )

    filter_obj.filter(record)
    assert "gsk_" not in record.msg
    assert "[REDACTED_API_KEY]" in record.msg
