"""Sarvam AI LLM Provider implementation for natural conversational Hinglish."""
import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class SarvamLLMProvider(BaseLLMProvider):
    """Conversational LLM using Sarvam AI (sarvam-105b-conversations)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        api_base: str = "https://api.sarvam.ai/v1",
    ):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")
        if not self.api_key:
            from pathlib import Path
            env_path = Path(__file__).resolve().parent.parent.parent / ".env"
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("SARVAM_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip()
                        os.environ["SARVAM_API_KEY"] = self.api_key
        self.model_name = model_name or os.environ.get("SARVAM_MODEL", "sarvam-105b-conversations")
        self.api_base = api_base.rstrip("/")
        self.provider_name = "sarvam"

    def generate_reply(
        self,
        messages: List[ChatMessage],
        customer_context: Dict[str, Any],
        detected_intent: Optional[str] = None,
    ) -> LLMResponse:
        t0 = time.perf_counter()

        # 1. Out-of-scope steering check (MuRIL model integration)
        steer_text = self.check_and_steer(detected_intent)
        if steer_text:
            return LLMResponse(
                reply_text=steer_text,
                provider_name=self.provider_name,
                model_name=self.model_name,
                latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                steered_back=True,
                steered_from_intent=detected_intent,
            )

        if not self.api_key:
            return LLMResponse(
                reply_text="[Sarvam API Key missing in .env. Please set SARVAM_API_KEY in .env]",
                provider_name=self.provider_name,
                model_name=self.model_name,
                latency_ms=0.0,
            )

        # 2. Dynamic, Natural Hinglish System Prompt
        persona_name = customer_context.get("persona_name", "Customer")
        system_prompt = (
            "You are an empathetic, highly knowledgeable AI Credit Card Assistant for an Indian bank.\n"
            "STRICT LANGUAGE REQUIREMENT:\n"
            "- Speak ONLY in natural, fluent, Romanized Hinglish (Hindi written in English letters, mixed naturally with English, exactly as Indians speak and chat on WhatsApp).\n"
            "- Always reply directly to the customer's last message. Never repeat previous replies.\n"
            "- If they ask for more card options, explain alternatives like Regalia Gold (travel & lounge perks), Millennia (cashback on Amazon/Flipkart/Zomato), or MoneyBack.\n"
            "- Keep answers warm, friendly, concise, and helpful (1-3 sentences).\n"
            "- Send only clean text without markdown asterisks (*), bullets, or special symbols.\n"
            f"- Customer Name: {persona_name}."
        )

        formatted_msgs = [{"role": "system", "content": system_prompt}]
        for m in messages:
            # Clean message content
            text = m.content.strip()
            if text:
                formatted_msgs.append({"role": m.role, "content": text})

        req_body = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": 0.7,
            "max_tokens": 200,
        }

        try:
            req = urllib.request.Request(
                f"{self.api_base}/chat/completions",
                data=json.dumps(req_body).encode("utf-8"),
                headers={
                    "api-subscription-key": self.api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "HinglishCardAssistant/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=18.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply_text = data["choices"][0]["message"]["content"].strip()
                # Remove any markdown formatting if present
                reply_text = reply_text.replace("**", "").replace("*", "")
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)

                return LLMResponse(
                    reply_text=reply_text,
                    provider_name=self.provider_name,
                    model_name=self.model_name,
                    latency_ms=latency_ms,
                )
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            err_msg = str(e)
            if hasattr(e, "read"):
                try:
                    err_msg = e.read().decode()
                except Exception:
                    pass
            print(f"Sarvam LLM Error: {err_msg}")
            # Fall back gracefully to conversational mock
            from app.llm.mock import MockLLMProvider
            fallback = MockLLMProvider().generate_reply(messages, customer_context, detected_intent)
            fallback.provider_name = f"sarvam-fallback"
            return fallback
