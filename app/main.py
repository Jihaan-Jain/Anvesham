"""FastAPI application for Hinglish Card Assistant demo (Port 8100)."""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent
env_file = ROOT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k:
                os.environ[k] = v

from app.engine.rules import DecisionEngine
from app.engine.config import CONFIG
from app.personas import ALL_PERSONAS, get_persona, list_personas
from app.intent.service import classify_intent
from app.llm.base import ChatMessage
from app.llm.factory import get_llm_provider
from app.voice.factory import get_voice_provider

app = FastAPI(title="Hinglish Card Assistant", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

engine = DecisionEngine(CONFIG)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona_id: str = Field("ntb_super_prime")
    history: List[Dict[str, str]] = Field(default_factory=list)
    turn_index: int = Field(0)
    voice_out: bool = Field(False)


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "llm_provider": os.environ.get("LLM_PROVIDER", "mock"),
        "intent_mode": os.environ.get("INTENT_MODE", "mock"),
        "intent_service_url": os.environ.get("INTENT_SERVICE_URL", "http://localhost:8000"),
        "voice_provider": os.environ.get("VOICE_PROVIDER", "mock"),
    }


@app.get("/api/personas")
def get_all_personas():
    return {"personas": list_personas()}


@app.post("/api/chat")
def chat_turn(req: ChatRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    t_start = time.perf_counter()

    # 1. Intent Classification (MuRIL-base model service or mock)
    intent_data = classify_intent(req.message, top_k=3)

    # 2. Conversational LLM (Groq / Sarvam / Mock)
    llm = get_llm_provider()
    chat_messages = [ChatMessage(role=m.get("role", "user"), content=m.get("text", "")) for m in req.history]
    chat_messages.append(ChatMessage(role="user", content=req.message))

    customer_ctx = {
        "persona_id": req.persona_id,
        "persona_name": persona.name,
        "journey_step": "income_declaration" if req.turn_index >= 1 else "identification",
        "turn_index": req.turn_index,
    }

    llm_resp = llm.generate_reply(
        messages=chat_messages,
        customer_context=customer_ctx,
        detected_intent=intent_data.get("intent"),
    )

    # 3. Decision Engine Evaluation (Pure Python deterministic rules)
    decision = engine.evaluate(persona.profile)
    matched = (decision.status == persona.expected_status and decision.path == persona.expected_path)

    # 4. Watch-for Points tracking
    triggered_watch = persona.watch_for[: min(len(persona.watch_for), req.turn_index + 1)]

    # 5. Optional Voice TTS
    tts_audio_base64 = None
    if req.voice_out:
        voice = get_voice_provider()
        tts_audio_base64 = voice.text_to_speech(llm_resp.reply_text)

    total_latency = round((time.perf_counter() - t_start) * 1000, 1)

    return {
        "reply": llm_resp.reply_text,
        "intent": intent_data,
        "llm": {
            "provider": llm_resp.provider_name,
            "model": llm_resp.model_name,
            "latency_ms": llm_resp.latency_ms,
            "steered_back": llm_resp.steered_back,
            "steered_from_intent": llm_resp.steered_from_intent,
        },
        "decision": {
            "status": decision.status.value,
            "path": decision.path.value,
            "credit_limit": decision.credit_limit,
            "product_name": decision.product_name,
            "reason": decision.reason,
            "hard_pull_performed": decision.hard_pull_performed,
            "income_verification_method": decision.income_verification_method,
            "kyc_mode": decision.kyc_mode,
            "foir": decision.foir,
            "matched_expected": matched,
            "expected_status": persona.expected_status.value,
            "expected_path": persona.expected_path.value,
        },
        "watch_points": {
            "all": persona.watch_for,
            "active": triggered_watch,
            "completed_count": len(triggered_watch),
            "total_count": len(persona.watch_for),
        },
        "tts_audio_base64": tts_audio_base64,
        "total_latency_ms": total_latency,
    }


@app.post("/api/voice/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    voice = get_voice_provider()
    audio_bytes = await audio_file.read()
    transcription = voice.speech_to_text(audio_bytes, audio_file.filename)
    return {"transcription": transcription}


@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Hinglish Card Assistant backend ready. Frontend loading...</h1>")


# Serve static assets if any
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
