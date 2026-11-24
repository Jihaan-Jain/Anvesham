"""Groq LLM Provider implementation using OpenAI-compatible API."""
import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class GroqLLMProvider(BaseLLMProvider):
    """Conversational LLM using Groq's high-speed inference (Llama 3.3 70B / Llama 3.1 8B)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        api_base: str = "https://api.groq.com/openai/v1",
    ):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.model_name = model_name or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_base = api_base.rstrip("/")
        self.provider_name = "groq"

    def generate_reply(
        self,
        messages: List[ChatMessage],
        customer_context: Dict[str, Any],
        detected_intent: Optional[str] = None,
    ) -> LLMResponse:
        t0 = time.perf_counter()

        # 1. Out-of-scope steering check
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
                reply_text="[Groq API Key missing in .env. Please set GROQ_API_KEY or switch LLM_PROVIDER=mock]",
                provider_name=self.provider_name,
                model_name=self.model_name,
                latency_ms=0.0,
            )

        # 2. System prompt enforcing Hinglish style and strict non-decision boundary
        system_prompt = (
            "You are the friendly, empathetic AI Credit Card Assistant for an Indian bank.\n"
            "Style and Language:\n"
            "- Always match the customer's language and style. If they speak or write in romanized Hinglish, "
            "reply in warm, natural conversational Hinglish (e.g., 'Aapka application process ho raha hai', "
            "'Haan bilkul, hum aage badhte hain').\n"
            "- Be concise, professional and helpful (1-3 sentences).\n"
            "CRITICAL OPERATIONAL BOUNDARY:\n"
            "- You NEVER decide credit eligibility, limits, card type, or decline/approval on your own.\n"
            "- The bank's rule engine makes all credit decisions.\n"
            "- Your role is to guide the customer, explain the offer, collect missing fields, and reassure them.\n"
            f"Context: Customer {customer_context.get('persona_name', 'Applicant')}, "
            f"Step: {customer_context.get('journey_step', 'onboarding')}."
        )

        formatted_msgs = [{"role": "system", "content": system_prompt}]
        for m in messages:
            formatted_msgs.append({"role": m.role, "content": m.content})

        req_body = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": 0.6,
            "max_tokens": 250,
        }

        try:
            req = urllib.request.Request(
                f"{self.api_base}/chat/completions",
                data=json.dumps(req_body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "HinglishCardAssistant/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply_text = data["choices"][0]["message"]["content"].strip()
                usage = data.get("usage", {})
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)

                return LLMResponse(
                    reply_text=reply_text,
                    provider_name=self.provider_name,
                    model_name=self.model_name,
                    latency_ms=latency_ms,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return LLMResponse(
                reply_text=f"Groq API error ({e}). Please check your API key or network connection.",
                provider_name=self.provider_name,
                model_name=self.model_name,
                latency_ms=latency_ms,
            )
