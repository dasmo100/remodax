"""
Remodax - Masking & Security Sanitizer Utilities
Provides helpers to mask API keys and confidential strings safely.
"""

from typing import Optional


def mask_api_key(raw_key: Optional[str]) -> str:
    """
    Masks an API key for safe UI visualization.
    Examples:
        'gsk_1234567890abcdef1234' -> 'gsk_••••••••1234'
        'AIzaSyB1234567890abcdef123' -> 'AIza••••••••f123'
        '' or None -> 'No configurada'
    """
    if not raw_key or not raw_key.strip():
        return "No configurada"

    key = raw_key.strip()
    length = len(key)

    if length <= 8:
        return "••••••••"

    prefix = key[:4]
    suffix = key[-4:]
    return f"{prefix}••••••••{suffix}"
