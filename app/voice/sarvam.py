"""Sarvam AI Voice provider (Saaras:v3 STT and Bulbul:v3 TTS)."""
import os
import json
import urllib.request
import uuid
from typing import Optional

from app.voice.base import BaseVoiceProvider


class SarvamVoiceProvider(BaseVoiceProvider):
    """Voice provider using Sarvam AI's Saaras:v3 STT and Bulbul:v3 TTS."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://api.sarvam.ai",
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
        self.api_base = api_base.rstrip("/")

    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe speech using Sarvam Saaras:v3 model."""
        if not self.api_key:
            return "Namaste, credit card application aage badhaiye."

        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        body = bytearray()

        # Model parameter - updated to official saaras:v3
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
        body.extend(b"saaras:v3\r\n")

        # Language code
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="language_code"\r\n\r\n')
        body.extend(b"hi-IN\r\n")

        # Audio file
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
            f'Content-Type: audio/wav\r\n\r\n'.encode("utf-8")
        )
        body.extend(audio_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            f"{self.api_base}/speech-to-text",
            data=bytes(body),
            headers={
                "api-subscription-key": self.api_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("transcript", "").strip()
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, "read"):
                try:
                    err_msg = e.read().decode()
                except Exception:
                    pass
            print(f"Sarvam STT Warning: {err_msg}")
            return ""

    def text_to_speech(self, text: str) -> Optional[str]:
        """Generate speech audio using Sarvam Bulbul:v3 TTS model."""
        if not self.api_key:
            return None

        clean_text = text.replace("**", "").replace("*", "").strip()[:400]
        if not clean_text:
            return None

        req_body = {
            "inputs": [clean_text],
            "target_language_code": "hi-IN",
            "speaker": "priya",
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v3",
        }

        req = urllib.request.Request(
            f"{self.api_base}/text-to-speech",
            data=json.dumps(req_body).encode("utf-8"),
            headers={
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                audios = data.get("audios", [])
                if audios:
                    return audios[0]  # Base64 audio
        except Exception as e:
            print(f"Sarvam TTS fallback: {e}")
            return None
        return None
