"""Base interface for Speech-to-Text and Text-to-Speech providers."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseVoiceProvider(ABC):
    """Abstract interface for speech processing."""

    @abstractmethod
    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe speech audio into text."""
        pass

    @abstractmethod
    def text_to_speech(self, text: str) -> Optional[str]:
        """Convert text into base64-encoded audio (mp3/wav) or None if client should fallback."""
        pass
