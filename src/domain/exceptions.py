"""
Remodax - Domain Exceptions
Defines core business domain exception hierarchies.
"""


class RemodaxException(Exception):
    """Base exception for all Remodax application errors."""
    pass


class RemodaxDomainException(RemodaxException):
    """Business rule or invariant violation."""
    pass


class AudioCaptureException(RemodaxDomainException):
    """Raised when audio capture initialization or streaming fails."""
    pass


class TranscriptionException(RemodaxDomainException):
    """Raised when audio transcription (STT) fails."""
    pass


class DocumentParseException(RemodaxDomainException):
    """Raised when document reading, parsing or chunking fails."""
    pass


class UnsupportedDocumentFormatException(DocumentParseException):
    """Raised when user supplies an unsupported file type."""
    pass


class SecurityCredentialException(RemodaxDomainException):
    """Raised when reading or saving credentials to Windows Credential Manager fails."""
    pass


class AIProviderException(RemodaxDomainException):
    """Raised when AI API communication or streaming fails."""
    pass


class StorageException(RemodaxDomainException):
    """Raised when database or local persistence operations fail."""
    pass
