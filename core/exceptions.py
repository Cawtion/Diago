"""
Diago Custom Exception Hierarchy
Provides structured error types for all subsystems.
"""


class DiagoError(Exception):
    """Base exception for all Diago errors."""

    def __init__(self, message: str = "", detail: str = ""):
        self.detail = detail
        super().__init__(message)


class AudioError(DiagoError):
    """Errors related to audio recording, loading, or processing."""
    pass


class AudioRecordingError(AudioError):
    """Failed to record audio from microphone."""
    pass


class AudioFileError(AudioError):
    """Failed to load or save an audio file."""
    pass


class AudioProcessingError(AudioError):
    """Error during audio preprocessing or feature extraction."""
    pass


class DatabaseError(DiagoError):
    """Errors related to database operations."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Failed to connect to or initialize the database."""
    pass


class DatabaseQueryError(DatabaseError):
    """A database query failed."""
    pass


class DiagnosticError(DiagoError):
    """Errors in the diagnostic engine pipeline."""
    pass


class FingerprintError(DiagnosticError):
    """Error during fingerprint generation or matching."""
    pass


class LLMError(DiagoError):
    """Errors related to LLM provider communication."""
    pass


class LLMConfigError(LLMError):
    """LLM is misconfigured (missing API key, bad provider, etc.)."""
    pass


class LLMConnectionError(LLMError):
    """Failed to connect to an LLM provider."""
    pass


class ConfigError(DiagoError):
    """Errors related to application configuration."""
    pass


class SearchError(DiagoError):
    """Errors related to web search (Tavily)."""
    pass
