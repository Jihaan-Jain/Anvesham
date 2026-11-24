"""Conversational Hinglish Mock LLM Provider with dynamic multi-turn context awareness."""
import time
import re
from typing import List, Dict, Any, Optional
from app.llm.base import BaseLLMProvider, ChatMessage, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Dynamic Hinglish conversational generator with context-aware responses."""

    def __init__(self, model_name: str = "mock-hinglish-v2"):
        self.model_name = model_name
        self.provider_name = "mock"

    def generate_reply(
        self,
        messages: List[ChatMessage],
        customer_context: Dict[str, Any],
        detected_intent: Optional[str] = None,
    ) -> LLMResponse:
        t0 = time.perf_counter()

        # 1. Out-of-scope steering check (MuRIL intent model)
        steer_text = self.check_and_steer(detected_intent)
        if steer_text:
            return LLMResponse(
                reply_text=steer_text,
                provider_name=self.provider_name,
                model_name=self.model_name,
                latency_ms=round((time.perf_counter() - t0) * 1000 + 15.0, 1),
                steered_back=True,
                steered_from_intent=detected_intent,
            )

        # 2. Get last user message
        last_user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m.content.lower().strip()
                break

        persona_id = customer_context.get("persona_id", "")
        turn_index = customer_context.get("turn_index", 0)

        # 3. Dynamic context-aware Hinglish reply
        reply = self._dynamic_hinglish_reply(persona_id, last_user_msg, turn_index, customer_context)

        latency_ms = round((time.perf_counter() - t0) * 1000 + 18.0, 1)
        return LLMResponse(
            reply_text=reply,
            provider_name=self.provider_name,
            model_name=self.model_name,
            latency_ms=latency_ms,
            steered_back=False,
        )

    def _dynamic_hinglish_reply(self, persona_id: str, text: str, turn_index: int, ctx: Dict[str, Any]) -> str:
        name = ctx.get("persona_name", "Ji").split()[0]

        # Case: User wants more options / alternatives
        if re.search(r"\b(more option|aur option|other|dusra|choice|acha|pasand|change)\b", text):
            return (
                f"Bilkul {name} ji! Hamare paas aur bhi shandar cards hain: "
                "1) Regalia Gold — agar aapko free airport lounge aur travel miles pasand hain. "
                "2) Millennia — agar aapko Amazon, Flipkart aur Zomato par 5% direct cashback chahiye. "
                "Aapki preference kya hai — travel ya shopping cashback?"
            )

        # Case: User mentions travel / lounge
        if re.search(r"\b(travel|lounge|flight|airport|hotel)\b", text):
            return (
                f"Travel ke liye Regalia Gold Card ekdum perfect hai {name} ji! "
                "Ismein domestic aur international lounge access free milta hai aur dining par 5X reward points. "
                "Kya is card ke saath proceed karein?"
            )

        # Case: User mentions shopping / cashback
        if re.search(r"\b(cashback|shopping|discount|amazon|flipkart|zomato)\b", text):
            return (
                f"Shopping ke liye Millennia Card best rahega {name} ji! "
                "Online spends par flat 5% cashback milta hai jo seedhe statement mein credit ho jata hai. "
                "Is card ko finalize kar dein?"
            )

        # Case: User agrees / confirms / says yes
        if re.search(r"\b(yes|haan|ha|kro|proceed|confirm|theek|done|le lo|bhejo|sahi)\b", text) and turn_index > 0:
            return (
                f"Bohot badhiya {name} ji! Aapka credit evaluation hamare engine ne approve kar diya hai. "
                "Bas last digital step baki hai — Aadhaar OTP se 2 minute mein eKYC complete karein aur card activate ho jayega!"
            )

        # Case: User asks about fees / charges
        if re.search(r"\b(fee|charges|annual|paisa|kitna|free)\b", text):
            return (
                f"{name} ji, yeh card First Year Free offer ke sath aata hai! "
                "Aur saal mein ₹1 lakh spend karne par annual fee completely waive off ho jati hai. Koi hidden charge nahi hai."
            )

        # Case: User asks about salary / documents / CIBIL
        if re.search(r"\b(income|salary|cibil|score|document|slip|statement)\b", text):
            return (
                f"Aapka financial record bohot achha hai {name} ji. "
                "Aapko koi physical document branch le jaane ki zaroorat nahi hai, sab digital verification se ho jayega."
            )

        # Persona-specific initial introductions (Turn 0 or generic)
        if persona_id == "etb_preapproved":
            return (
                f"Namaste {name} ji! Bank ke saath aapke shandar relationship ke wajah se "
                "aapke account par pre-approved Millennia Card offer ready hai with limit ₹2,50,000. Zero documentation!"
            )
        elif persona_id == "student":
            return (
                f"Hi {name}! Students ke liye hamara Campus Credit Builder Card best hai. "
                "Bina kisi salary slip ke small FD se card active ho jata hai aur CIBIL score banna start ho jata hai!"
            )
        elif persona_id == "ntb_super_prime":
            return (
                f"Namaste {name} ji! Aapka CIBIL score 810 exceptional hai, isliye income proof completely waive hai. "
                "Hamara premium Infinia Metal Card with ₹3,50,000 limit aapke liye ready hai. Kya offer explore karein?"
            )
        elif persona_id == "ntb_prime":
            return (
                f"Hello {name} ji! Bureau se aapki estimated income ₹1,10,000 derive ho gayi hai. "
                "Apna ghar hone ke karan instant Regalia Gold card offer unlock hua hai. Kya hum proceed karein?"
            )
        elif persona_id in ("ntc_overstated", "ntc_secured", "ntb_low_score"):
            return (
                f"Namaste {name} ji! Aapke credit profile ke liye hamara Step-Up Secured Credit Builder card sabse best hai. "
                "Yeh timely payments ke sath 6 mahine mein aapka CIBIL score 750+ pahuncha dega."
            )

        # Default natural fallback
        return (
            f"Haan ji {name} ji! Main aapki baat samajh gaya. "
            "Aap apni suvidha anusaar bataiye — aap card ke baare mein kya detail janna chahte hain?"
        )
