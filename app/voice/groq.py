"""Groq Voice implementation using Whisper STT."""
import os
import json
import urllib.request
import uuid
from typing import Optional

from app.voice.base import BaseVoiceProvider


class GroqVoiceProvider(BaseVoiceProvider):
    """Voice provider using Groq Whisper (whisper-large-v3) for speech-to-text."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "whisper-large-v3",
        api_base: str = "https://api.groq.com/openai/v1",
    ):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")

    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe speech audio via Groq Whisper API."""
        if not self.api_key:
            return "Namaste, credit card ke liye apply karna hai."

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        
        # Build multipart/form-data body
        body = bytearray()
        
        # 1. model parameter
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
        body.extend(f"{self.model_name}\r\n".encode("utf-8"))
        
        # 2. prompt hinting Hinglish context
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="prompt"\r\n\r\n')
        body.extend(b"Hinglish conversation about Indian credit card application.\r\n")

        # 3. audio file payload
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f'Content-Type: audio/wav\r\n\r\n'.encode("utf-8")
        )
        body.extend(audio_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            f"{self.api_base}/audio/transcriptions",
            data=bytes(body),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=20.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("text", "").strip()
        except Exception as e:
            return f"STT error: {e}"

    def text_to_speech(self, text: str) -> Optional[str]:
        # Groq Whisper is STT only; returns None so frontend smoothly uses browser's SpeechSynthesis
        return None
