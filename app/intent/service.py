"""Intent service wrapper supporting both live MuRIL model service and high-fidelity mock mode."""
import os
import time
import re
import json
from pathlib import Path
from typing import Dict, Any, List

INTENT_MODE = os.environ.get("INTENT_MODE", "mock").lower()
INTENT_SERVICE_URL = os.environ.get("INTENT_SERVICE_URL", "http://localhost:8000")

# Load all 56 official intent names from model_service/labels.json
LABELS_FILE = Path(__file__).parent.parent.parent / "model_service" / "labels.json"
try:
    ALL_56_LABELS = json.loads(LABELS_FILE.read_text(encoding="utf-8"))["names"]
except Exception:
    ALL_56_LABELS = [
        "datetime_query", "light_change_colour", "train_ticket_booking", "food_order_status", "stock_price",
        "greeting", "local_events", "music_dislike", "smart_plug_off", "cooking_recipe",
        "currency_exchange", "traffic_query", "general_chitchat", "weather_query", "volume_up",
        "email_add_contact", "food_order", "contact_lookup", "light_brighten", "place_recommendation",
        "audiobook_play", "list_create_or_add", "news_query", "smart_plug_on", "joke",
        "definition_query", "social_media_query", "music_settings", "audio_settings", "calendar_remove",
        "light_dim", "calendar_query", "email_send", "vacuum_cleaner", "volume_down",
        "radio_play", "cooking_tips", "timezone_convert", "maths", "light_off",
        "light_on", "transport_route_query", "music_like", "email_check", "music_play",
        "volume_mute", "social_media_post", "general_knowledge", "calendar_reminder_set", "alarm_remove",
        "list_remove", "taxi_booking", "movie_recommendation", "song_info", "list_query",
        "alarm_podcast_coffee_game"
    ]

# Intent to ID mapping
LABEL_TO_ID = {name: idx for idx, name in enumerate(ALL_56_LABELS)}

# High-fidelity Hinglish, Devanagari Hindi, and English pattern matcher for the 56 intents
MOCK_PATTERNS = [
    # Alarms / Podcasts / Games (Class 55)
    (r"\b(alarm|jaga|uth|uthana|baje|uthna|wake|podcasts?|coffee|game)\b", "alarm_podcast_coffee_game", 0.96),
    # Weather (Class 13)
    (r"\b(mausam|weather|baarish|rain|temperature|dhoop|thand|barish|garmi)\b", "weather_query", 0.95),
    # Music (Class 44, 35)
    (r"\b(gaana|sangeet|song|music|arijit|spotify|baja|sunao|play)\b", "music_play", 0.94),
    (r"\b(radio|fm|vividh bharti)\b", "radio_play", 0.92),
    # Food Order & Delivery (Class 16, 3)
    (r"\b(pizza|burger|khana|food|bhookh|zomato|swiggy|dominos|order)\b", "food_order", 0.95),
    (r"\b(order status|delivery status|khana kahan pahuncha)\b", "food_order_status", 0.93),
    # Smart Home & Lights (Class 40, 39, 1, 8, 23)
    (r"\b(batti|light|bulb|roshni) (on|chalu|jalao|start)\b", "light_on", 0.93),
    (r"\b(batti|light|bulb|roshni) (off|band|bujhao|stop)\b", "light_off", 0.94),
    (r"\b(light|batti).*colour\b", "light_change_colour", 0.91),
    (r"\b(plug on|switch on)\b", "smart_plug_on", 0.90),
    (r"\b(plug off|switch off)\b", "smart_plug_off", 0.90),
    # Volumes (Class 14, 34, 45)
    (r"\b(volume badhao|awaz badhao|volume up)\b", "volume_up", 0.93),
    (r"\b(volume kam|awaz kam|volume down|dheere)\b", "volume_down", 0.93),
    (r"\b(mute|chup|shant|sound off)\b", "volume_mute", 0.92),
    # Travel / Transit (Class 2, 51, 11)
    (r"\b(train|railway|ticket|irctc|seat|pnr)\b", "train_ticket_booking", 0.93),
    (r"\b(cab|taxi|uber|ola|auto|ride)\b", "taxi_booking", 0.92),
    (r"\b(traffic|jam|rasta|route)\b", "traffic_query", 0.91),
    # Email & Calendar (Class 43, 32, 31, 48)
    (r"\b(email|mail|inbox|sandesh) (check|dikhao|read)\b", "email_check", 0.92),
    (r"\b(email|mail) (bhejo|send|karo)\b", "email_send", 0.91),
    (r"\b(calendar|schedule|meeting|reminder)\b", "calendar_query", 0.91),
    # Entertainment & Chitchat (Class 5, 24, 22, 4)
    (r"\b(joke|hasao|chutkula|funny)\b", "joke", 0.94),
    (r"\b(news|samachar|khabar|headline)\b", "news_query", 0.92),
    (r"\b(stock|share|nifty|sensex|market)\b", "stock_price", 0.90),
    (r"\b(time|samay|kitne baje|waqt)\b", "datetime_query", 0.93),
    (r"\b(namaste|hello|hi|hey|pranam|kese ho|kaise ho|good morning|namaskar)\b", "greeting", 0.97),
]


def classify_mock(text: str, top_k: int = 3) -> Dict[str, Any]:
    """Deterministic, high-fidelity mock classifier replicating MuRIL-base outputs."""
    t0 = time.perf_counter()
    text_lower = text.lower()

    matched_intent = "general_chitchat"
    confidence = 0.88

    for pattern, intent, conf in MOCK_PATTERNS:
        if re.search(pattern, text_lower):
            matched_intent = intent
            confidence = conf
            break

    intent_id = LABEL_TO_ID.get(matched_intent, 12)
    latency_ms = round((time.perf_counter() - t0) * 1000 + 17.5, 1)

    # Build top-k predictions with realistic softmax probability distribution
    alt_candidates = [n for n in ALL_56_LABELS if n != matched_intent]
    alt1 = alt_candidates[intent_id % len(alt_candidates)]
    alt2 = alt_candidates[(intent_id + 7) % len(alt_candidates)]

    p_rem = round(1.0 - confidence, 4)
    p_alt1 = round(p_rem * 0.7, 4)
    p_alt2 = round(p_rem - p_alt1, 4)

    top_list = [
        {"intent": matched_intent, "intent_id": intent_id, "confidence": confidence},
        {"intent": alt1, "intent_id": LABEL_TO_ID[alt1], "confidence": p_alt1},
        {"intent": alt2, "intent_id": LABEL_TO_ID[alt2], "confidence": p_alt2},
    ][:top_k]

    return {
        "text": text,
        "intent": matched_intent,
        "intent_id": intent_id,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "mode": "mock",
        "top": top_list,
    }


def classify_intent(text: str, top_k: int = 3, timeout: float = 3.0) -> Dict[str, Any]:
    """Classify text intent via live MuRIL service or high-fidelity mock fallback."""
    mode = os.environ.get("INTENT_MODE", "mock").lower()

    if mode == "service":
        try:
            from model_service.intent_client import classify_intent as client_classify
            res = client_classify(text, top_k=top_k, timeout=timeout)
            res["mode"] = "service"
            return res
        except Exception as e:
            # Service unavailable, fall back gracefully to mock with warning
            mock_res = classify_mock(text, top_k=top_k)
            mock_res["fallback_warning"] = f"Intent service at {INTENT_SERVICE_URL} unreachable ({e}). Used mock fallback."
            return mock_res
    else:
        return classify_mock(text, top_k=top_k)
