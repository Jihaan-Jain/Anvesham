# Read me first

## What's in this folder

| Path | What it is |
|---|---|
| `PROMPT.md` | Paste this into the AI on Windows. It builds the whole demo project from it. |
| `SCENARIOS.md` | The 12 credit-card personas and their expected outcomes (the acceptance tests). |
| `model_service/` | The FastAPI service for the Hinglish MuRIL model, plus a client and a Dockerfile. |
| `training/anveshan_muril_deploy.ipynb` | Trains the deployable model on Kaggle or Colab (T4 GPU, about 40 minutes). |
| `training/common.py`, `train.csv`, `pseudo_labels.csv` | Romanizer and augmentation code, plus the training data. |

## Steps

1. **Train the model (once).** Upload `training/anveshan_muril_deploy.ipynb` to Kaggle (GPU T4) or Colab (T4).
   - Kaggle: add the competition data and the `anveshan-pseudo` dataset as inputs, turn **Internet on**, then
     **Save Version → Save & Run All (Commit)**. Download `muril_intent.zip` from the **Output** tab.
   - Colab: upload `train.csv` and `pseudo_labels.csv` from `training/`, then **Run all**. The zip is saved to
     `MyDrive/anveshan_deploy/muril_intent.zip`.
2. **Copy this whole folder to Windows.**
3. Unzip `muril_intent.zip` into `model_service\muril_intent\`.
4. **Test the model on its own** (PowerShell, inside `model_service`):
   ```powershell
   py -3.11 -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   $env:MODEL_DIR = ".\muril_intent"; .venv\Scripts\uvicorn serve:app --port 8000
   ```
   Open http://localhost:8000 and try "kal subah 7 baje alarm lagao".
5. **Build the demo app:** open an empty folder in your AI assistant, point it at this folder, and paste `PROMPT.md`.
6. Get a free **Groq** key (console.groq.com) and/or a **Sarvam** key (dashboard.sarvam.ai) and put them in `.env`.
   Never commit or share keys.

## Honest limits to mention in the presentation

- The competition model knows 56 **general assistant** intents, not banking ones. That's why phase 2 trains a banking
  intent model with the same pipeline.
- The Kaggle data may be restricted to the competition. Use it for the demo and presentation, not in a client product.
