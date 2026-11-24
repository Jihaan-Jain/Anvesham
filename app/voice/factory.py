"""Factory for instantiating the active voice provider."""
import os
from app.voice.base import BaseVoiceProvider
from app.voice.mock import MockVoiceProvider


def get_voice_provider() -> BaseVoiceProvider:
    provider = os.environ.get("VOICE_PROVIDER", "mock").lower()
    
    if provider == "groq":
        from app.voice.groq import GroqVoiceProvider
        return GroqVoiceProvider()
    elif provider == "sarvam":
        from app.voice.sarvam import SarvamVoiceProvider
        return SarvamVoiceProvider()
    else:
        return MockVoiceProvider()
