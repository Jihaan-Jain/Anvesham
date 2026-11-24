"""Factory for instantiating the configured LLM provider."""
import os
from app.llm.base import BaseLLMProvider
from app.llm.mock import MockLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """Instantiate the active LLM provider from environment configuration."""
    provider_type = os.environ.get("LLM_PROVIDER", "mock").lower()

    if provider_type == "groq":
        from app.llm.groq import GroqLLMProvider
        return GroqLLMProvider()
    elif provider_type == "sarvam":
        from app.llm.sarvam import SarvamLLMProvider
        return SarvamLLMProvider()
    else:
        return MockLLMProvider()
