"""Zero-dependency Standard Library HTTP Server for Hinglish Card Assistant.

Runs on pure Python (3.10+) with NO external pip packages required.
Serves on port 8100, exactly matching app.main's endpoints:
- GET  /              -> Static frontend (app/static/index.html)
- GET  /api/health    -> Health & config status
- GET  /api/personas  -> 12 personas with acceptance rules & watch-points
- POST /api/chat      -> Intent classification + Hinglish LLM + Decision Engine
- POST /api/voice/stt -> Speech to text
"""
import sys
import os
import json
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Auto-load .env using standard library
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

STATIC_FILE = ROOT_DIR / "app" / "static" / "index.html"
engine = DecisionEngine(CONFIG)


class CardAssistantHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            if STATIC_FILE.exists():
                content = STATIC_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "index.html not found")
            return

        if path == "/api/health":
            self._send_json({
                "status": "healthy",
                "server": "standard_library_http",
                "llm_provider": os.environ.get("LLM_PROVIDER", "mock"),
                "intent_mode": os.environ.get("INTENT_MODE", "mock"),
                "intent_service_url": os.environ.get("INTENT_SERVICE_URL", "http://localhost:8000"),
                "voice_provider": os.environ.get("VOICE_PROVIDER", "mock"),
            })
            return

        if path == "/api/personas":
            self._send_json({"personas": list_personas()})
            return

        self.send_error(404, f"Path not found: {path}")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        if path == "/api/chat":
            try:
                req = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
                return

            persona_id = req.get("persona_id", "ntb_super_prime")
            message = req.get("message", "")
            history = req.get("history", [])
            turn_index = req.get("turn_index", 0)
            voice_out = req.get("voice_out", False)

            persona = get_persona(persona_id)
            if not persona:
                self._send_json({"error": "Persona not found"}, status=404)
                return

            t_start = time.perf_counter()

            # 1. Intent Classification (MuRIL-base model or mock)
            intent_data = classify_intent(message, top_k=3)

            # 2. Conversational LLM (Groq / Sarvam / Mock)
            llm = get_llm_provider()
            chat_messages = [
                ChatMessage(role=m.get("role", "user"), content=m.get("text", ""))
                for m in history
            ]
            chat_messages.append(ChatMessage(role="user", content=message))

            customer_ctx = {
                "persona_id": persona_id,
                "persona_name": persona.name,
                "journey_step": "income_declaration" if turn_index >= 1 else "identification",
                "turn_index": turn_index,
            }

            llm_resp = llm.generate_reply(
                messages=chat_messages,
                customer_context=customer_ctx,
                detected_intent=intent_data.get("intent"),
            )

            # 3. Decision Engine Evaluation (Pure Python rules)
            decision = engine.evaluate(persona.profile)
            matched = (
                decision.status == persona.expected_status
                and decision.path == persona.expected_path
            )

            # 4. Watch points tracking
            triggered_watch = persona.watch_for[: min(len(persona.watch_for), turn_index + 1)]

            # 5. Optional Voice TTS
            tts_audio_base64 = None
            if voice_out:
                voice = get_voice_provider()
                tts_audio_base64 = voice.text_to_speech(llm_resp.reply_text)

            total_latency = round((time.perf_counter() - t_start) * 1000, 1)

            resp_payload = {
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
            self._send_json(resp_payload)
            return

        if path == "/api/voice/stt":
            voice = get_voice_provider()
            transcription = voice.speech_to_text(post_data, "recording.wav")
            self._send_json({"transcription": transcription})
            return

        self.send_error(404, f"Path not found: {path}")

    def log_message(self, format, *args):
        # Clean logging
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]} - {args[1]}")


def run_server(port=8100, host="127.0.0.1"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, CardAssistantHandler)
    print("=" * 60)
    print(f"  Hinglish Card Assistant Web Server running at:")
    print(f"  --> http://localhost:{port}/")
    print(f"  (Zero-dependency standard library server - no pip required)")
    print("=" * 60)
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8100"))
    run_server(port=port)
