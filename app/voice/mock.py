"""Mock Voice provider with simulated speech-to-text and browser fallback for TTS."""
from typing import Optional
from app.voice.base import BaseVoiceProvider


class MockVoiceProvider(BaseVoiceProvider):
    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        return "Namaste, mujhe ek credit card ke liye apply karna hai."

    def text_to_speech(self, text: str) -> Optional[str]:
        # Return None to instruct frontend to use browser's native window.speechSynthesis
        return None
