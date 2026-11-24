"""Base interface and data models for conversational LLM providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    reply_text: str
    provider_name: str
    model_name: str
    latency_ms: float
    steered_back: bool = False
    steered_from_intent: Optional[str] = None
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0


# Non-banking intents from 56-class MuRIL model that should trigger polite Hinglish steering
OUT_OF_SCOPE_INTENTS = {
    "weather_query": "weather (mausam)",
    "alarm_podcast_coffee_game": "alarm / podcast",
    "music_play": "music (gaana)",
    "music_like": "music",
    "music_dislike": "music",
    "music_settings": "music settings",
    "food_order": "food ordering (khana)",
    "food_order_status": "food delivery status",
    "light_on": "home automation (lights)",
    "light_off": "home automation (lights)",
    "light_dim": "light brightness",
    "light_brighten": "light brightness",
    "light_change_colour": "light colors",
    "smart_plug_on": "smart plug",
    "smart_plug_off": "smart plug",
    "vacuum_cleaner": "vacuum cleaner",
    "joke": "joke (chutkula)",
    "train_ticket_booking": "train tickets",
    "taxi_booking": "cab booking",
    "cooking_recipe": "cooking recipes",
    "cooking_tips": "cooking tips",
}


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM conversation providers."""

    @abstractmethod
    def generate_reply(
        self,
        messages: List[ChatMessage],
        customer_context: Dict[str, Any],
        detected_intent: Optional[str] = None,
    ) -> LLMResponse:
        """Generate conversational response in customer's language and style."""
        pass

    def check_and_steer(self, detected_intent: Optional[str]) -> Optional[str]:
        """If intent is recognized as out-of-scope non-banking query, generate polite steer text."""
        if detected_intent and detected_intent in OUT_OF_SCOPE_INTENTS:
            intent_label = OUT_OF_SCOPE_INTENTS[detected_intent]
            return (
                f"Main samajh gaya aap {intent_label} ke baare mein baat kar rahe hain, "
                f"par main aapka Card Assistant hoon! Aaiye pehle aapke credit card application ko complete karte hain. "
                f"Hum kahan the — kya hum aage proceed karein?"
            )
        return None
