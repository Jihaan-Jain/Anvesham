"""Tiny client for the intent service — copy into any Python project (e.g. an omnispark integration).
Only needs the standard library.

    from intent_client import classify_intent
    classify_intent("kal subah 7 baje alarm lagao")
    # {'intent': 'alarm_podcast_coffee_game', 'intent_id': 55, 'confidence': 0.97, ...}
"""
import json, os, urllib.request

INTENT_URL = os.environ.get("INTENT_SERVICE_URL", "http://localhost:8000")


def classify_intent(text: str, top_k: int = 3, timeout: float = 5.0) -> dict:
    req = urllib.request.Request(
        f"{INTENT_URL}/predict",
        data=json.dumps({"text": text, "top_k": top_k}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    import sys
    print(json.dumps(classify_intent(" ".join(sys.argv[1:]) or "aaj mausam kaisa hai"), ensure_ascii=False, indent=2))
