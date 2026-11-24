# Prompt: build "Hinglish Card Assistant", a demo project for my own Hinglish NLP model

> Paste everything below this line into your AI coding assistant (Claude Code, Cursor, etc.) on Windows,
> opened in an EMPTY folder. Put this whole `windows_handoff` folder next to it first and tell the AI where it is.

---

You are building a **standalone demo project on Windows** (PowerShell, Python 3.11). You have no other context, so
read this whole prompt and the files it points to before writing code. Ask me before deviating from it.

## 1. Background (what exists already)

- I built a **Hinglish intent classifier** for a Kaggle competition (Anveshan Data Sprint 2, NLP, rank 1 on the
  public leaderboard, macro F1 0.870). It classifies short user queries written in **Hindi (Devanagari), romanized
  Hinglish, or code-mixed text** into 56 intents.
- The deployable version is **MuRIL-large** (`google/muril-large-cased`) fine-tuned on all training data with
  romanization + chat-style augmentation + pseudo-labels. It runs on **CPU**.
- The handoff folder contains:
  - `model_service/serve.py` – a working FastAPI service for the model (`POST /predict`, `POST /predict/batch`,
    `GET /health`, and a demo page at `/`). Reuse it as-is; don't rewrite it.
  - `model_service/labels.json` – the 56 intent names (id → name).
  - `model_service/intent_client.py` – a tiny standard-library client: `classify_intent(text)`.
  - `model_service/requirements.txt`, `Dockerfile`.
  - `training/anveshan_muril_deploy.ipynb` – the notebook that trains the model on a Kaggle/Colab GPU and produces
    `muril_intent.zip`. `training/common.py` has the Devanagari→Latin romanizer and the augmentation
    (`augment`, `chatify`, `romanize`, `light`). Reuse these for phase 2.
  - `SCENARIOS.md` – the 12 demo scenarios (customer personas) with expected outcomes. **These are the acceptance tests.**
- The model weights are NOT in this folder. I will download `muril_intent.zip` from Kaggle/Google Drive and unzip it
  to `model_service/muril_intent/`. Until then, build everything so it runs with `INTENT_MODE=mock` (see §4).
- This demo is modelled on my company's onboarding prototype ("OmniSpark"), which used Claude for the conversation.
  **This demo must not use Claude or any Anthropic API.** Conversation goes through **Groq** or **Sarvam AI**
  (I'll provide keys), and my own model does the intent understanding.

## 2. What to build

A web app where a customer applies for a **credit card** by **chatting or speaking** in English, Hindi or Hinglish.
Three parts, each in its own module:

1. **Understanding (my model).** Every customer message first goes to the intent service. Show the detected intent,
   confidence and latency in a side panel on every turn, because that panel is the point of the demo.
2. **Conversation (LLM via Groq or Sarvam).** Writes the assistant's replies in the customer's language and style
   (reply in Hinglish if they wrote Hinglish), asks for the next missing field, and explains the offer.
   It **never decides** eligibility, limit or card type.
3. **Decision engine (plain Python rules, no AI).** Bureau score bands, new-to-credit handling, Account Aggregator
   (AA) income verification, FOIR, secured/student/pre-approved paths, exactly as described in `SCENARIOS.md`.
   Mock the bureau, AA and bank lookups with the persona data, and keep the thresholds in one config file.

Plus:

4. **Voice.** A mic button in the chat. Speech-to-text and text-to-speech go through the selected provider
   (Groq: Whisper STT; Sarvam: its Indian-language STT and TTS). If TTS is unavailable, fall back to the browser's
   `speechSynthesis`. Modes: text only, voice in, voice in + voice out.
5. **Persona runner.** A dropdown with the 12 scenarios. "Auto-play" drives the conversation with that persona's
   scripted answers, **written in Hinglish**, at a readable pace. The engine then produces its decision, and a green or
   red badge shows whether it matched the expected status and path. "Talk yourself" lets me type or speak as the
   customer for that persona.
6. **Dashboard panel** (right side): per turn, the detected intent + confidence + latency (my model); the LLM provider,
   model and latency; the current journey step; the decision path; and the "watch for" points from `SCENARIOS.md`
   ticking off as they happen.

## 3. Phase 2: a banking intent model (important)

My competition model knows **56 general voice-assistant intents** (alarm, weather, music, email, calendar, lights …),
**not banking intents**. So:

- **Phase 1 (build first):** use it as-is. It recognises Hinglish requests that are outside the card journey
  (e.g. "kal ka mausam kaisa hai" → `weather_query`). The assistant then politely steers back to the application, which
  shows the model working on real Hinglish. For in-journey answers, the LLM extracts the fields.
- **Phase 2:** add a script, `training/make_banking_dataset.py`. It defines about 15 banking intents (e.g. `apply_card`,
  `check_eligibility`, `give_income`, `give_pan`, `give_dob`, `ask_documents`, `ask_fees`, `compare_cards`,
  `consent_yes`, `consent_no`, `ask_status`, `talk_to_human`, `greeting`, `out_of_scope`). It uses the Groq/Sarvam LLM
  to generate about 150 varied examples per intent in Devanagari Hindi, romanized Hinglish and English, then applies
  `common.py`'s `augment()`. Also adapt the training notebook into `training/train_banking.ipynb` (same recipe, new
  labels). When I drop the trained model in `model_service/muril_banking/`, the app uses it for routing via an env var
  (`INTENT_MODEL_DIR`), with no code changes.

## 4. Configuration and modes (`.env`, with a committed `.env.example`)

```
LLM_PROVIDER=groq            # groq | sarvam | mock
GROQ_API_KEY=
SARVAM_API_KEY=
INTENT_MODE=service          # service | mock
INTENT_SERVICE_URL=http://localhost:8000
VOICE_PROVIDER=groq          # groq | sarvam | browser
```

- `mock` LLM: canned replies so the whole app, including all 12 scenarios, runs with **no keys and no internet**.
- `mock` intent: a small keyword rule, so the app runs before the model zip is downloaded.
- Put each provider behind a small interface (`llm/base.py`, `llm/groq.py`, `llm/sarvam.py`, `llm/mock.py`; the same
  pattern for voice) so adding a provider is one file.
- **Check the current Groq and Sarvam API docs for model names and endpoints. Don't guess them.** Groq is
  OpenAI-compatible; use the official SDKs or plain HTTP.

## 5. Tech and layout

- Backend: FastAPI (one app on port 8100). The intent model runs as a separate process on port 8000 (`serve.py`).
- Frontend: a single static HTML/JS page served by the backend (no build step, no Node). It must look clean and work
  in light and dark mode.
- Suggested layout: `app/main.py`, `app/engine/` (rules + config + mock bureau/AA), `app/llm/`, `app/voice/`,
  `app/personas.py`, `app/static/index.html`, `model_service/` (copied from the handoff), `training/`, `tests/`.
- Windows: give PowerShell commands, use `pathlib`, and avoid bash-only scripts and macOS-only tools. Provide
  `run_all.ps1`, which starts the model service and the app and opens the browser.

## 6. Rules

- The LLM never decides credit. It only talks and extracts fields, and the engine decides.
- Keep API keys only in `.env`. Add `.env` and `model_service/muril_intent*/` to `.gitignore`. Never print or log keys.
- Use only fake persona data (no real PAN or phone numbers). Generate valid-format dummy PANs.
- Don't copy code from my company's repositories. Build this from scratch from this prompt.

## 7. Done means

1. `pytest` passes, including one test per scenario asserting the engine's `expected status` and `expected path` from
   `SCENARIOS.md`.
2. With `LLM_PROVIDER=mock` and `INTENT_MODE=mock`, all 12 personas auto-play end to end with no keys.
3. With my Groq or Sarvam key and the real model, a typed and a spoken Hinglish conversation both work, and the
   dashboard shows my model's intent on every turn.
4. A `README.md` that tells me, step by step on Windows, how to install, add keys, download and unzip the model, run,
   and show the demo (including a 2-minute demo script for a presentation).

Start by restating the plan in a short list and asking me anything that's unclear, then build it in this order:
engine + tests → mock end-to-end → UI → real LLM provider → voice → phase-2 dataset script.
