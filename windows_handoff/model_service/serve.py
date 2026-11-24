"""Hinglish intent classifier service (MuRIL-base, CPU).

Run:   MODEL_DIR=./muril_intent uvicorn serve:app --host 0.0.0.0 --port 8000
API:   POST /predict  {"text": "kal subah 7 baje alarm lagao", "top_k": 3}
       POST /predict/batch {"texts": [...]}
       GET  /health
Demo:  open http://localhost:8000/ in a browser.
"""
import json, os, time
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIR = Path(os.environ.get("MODEL_DIR", "./muril_intent"))
MAX_LEN = int(os.environ.get("MAX_LEN", "64"))
torch.set_num_threads(int(os.environ.get("TORCH_THREADS", str(os.cpu_count() or 4))))

tok = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, torch_dtype=torch.float32).eval()
labels_file = MODEL_DIR / "labels.json"
NAMES = json.loads(labels_file.read_text())["names"] if labels_file.exists() else \
    [model.config.id2label[i] for i in range(model.config.num_labels)]

app = FastAPI(title="Hinglish Intent Classifier", version="1.0")


class Query(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)


class Batch(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=64)
    top_k: int = Field(1, ge=1, le=10)


@torch.inference_mode()
def classify(texts: list[str], top_k: int) -> list[dict]:
    enc = tok(texts, padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt")
    probs = torch.softmax(model(**enc).logits.float(), -1)
    p, i = probs.topk(top_k, -1)
    return [{
        "text": t,
        "intent": NAMES[int(ii[0])], "intent_id": int(ii[0]), "confidence": round(float(pp[0]), 4),
        "top": [{"intent": NAMES[int(a)], "intent_id": int(a), "confidence": round(float(b), 4)} for a, b in zip(ii, pp)],
    } for t, pp, ii in zip(texts, p, i)]


@app.get("/health")
def health():
    return {"status": "ok", "model": str(MODEL_DIR), "num_intents": len(NAMES)}


@app.post("/predict")
def predict(q: Query):
    t0 = time.perf_counter()
    out = classify([q.text.strip()], q.top_k)[0]
    out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out


@app.post("/predict/batch")
def predict_batch(b: Batch):
    texts = [t.strip() for t in b.texts]
    if any(not t for t in texts):
        raise HTTPException(422, "empty text in batch")
    return {"results": classify(texts, b.top_k)}


@app.get("/", response_class=HTMLResponse)
def demo():
    return DEMO_HTML


DEMO_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hinglish Intent Classifier</title>
<style>
:root{--bg:#f7f7f8;--card:#fff;--ink:#1d1d1f;--muted:#6b6b72;--accent:#3b5bdb;--bar:#dbe4ff}
@media (prefers-color-scheme:dark){:root{--bg:#141416;--card:#1e1e22;--ink:#ececf1;--muted:#9a9aa3;--accent:#748ffc;--bar:#2b3566}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
main{max-width:640px;margin:40px auto;padding:0 16px}
.card{background:var(--card);border-radius:14px;padding:20px;box-shadow:0 1px 3px #0002}
h1{font-size:22px;margin:0 0 4px} p{color:var(--muted);margin:0 0 16px}
form{display:flex;gap:8px} input{flex:1;padding:12px;border-radius:10px;border:1px solid #8884;background:transparent;color:inherit;font-size:16px}
button{padding:12px 18px;border:0;border-radius:10px;background:var(--accent);color:#fff;font-weight:600;cursor:pointer}
.ex{margin:12px 0 0;display:flex;flex-wrap:wrap;gap:6px}.ex span{font-size:13px;padding:4px 10px;border-radius:99px;border:1px solid #8884;cursor:pointer}
.row{margin-top:14px}.lab{display:flex;justify-content:space-between;font-size:14px}
.track{height:10px;background:var(--bar);border-radius:6px;overflow:hidden}.fill{height:100%;background:var(--accent)}
.top{font-size:20px;font-weight:700;margin-top:18px}.meta{color:var(--muted);font-size:13px}
</style></head><body><main><div class="card">
<h1>Hinglish Intent Classifier</h1><p>MuRIL-base, fine-tuned on Hindi + romanized Hinglish assistant queries (56 intents).</p>
<form id="f"><input id="q" placeholder="e.g. kal subah 7 baje alarm lagao" autocomplete="off"><button>Classify</button></form>
<div class="ex" id="ex"></div><div id="out"></div></div></main>
<script>
const EX=["kal subah 7 baje alarm lagao","aaj delhi ka mausam kaisa hai","arijit singh ke gaane chalao","मेरे नए ईमेल दिखाओ","bhai volume thoda kam karo","dominos se pizza order karo"];
const ex=document.getElementById('ex'),out=document.getElementById('out'),q=document.getElementById('q');
EX.forEach(t=>{const s=document.createElement('span');s.textContent=t;s.onclick=()=>{q.value=t;run()};ex.appendChild(s)});
document.getElementById('f').onsubmit=e=>{e.preventDefault();run()};
async function run(){const t=q.value.trim();if(!t)return;out.innerHTML='<p class="meta">Classifying...</p>';
 try{const r=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,top_k:5})});
 const d=await r.json();if(!r.ok)throw new Error(JSON.stringify(d));
 out.innerHTML=`<div class="top">${d.intent}</div><div class="meta">confidence ${(d.confidence*100).toFixed(1)}% · ${d.latency_ms} ms</div>`+
  d.top.map(x=>`<div class="row"><div class="lab"><span>${x.intent}</span><span>${(x.confidence*100).toFixed(1)}%</span></div><div class="track"><div class="fill" style="width:${x.confidence*100}%"></div></div></div>`).join('');
 }catch(err){out.innerHTML='<p class="meta">Error: '+err.message+'</p>'}}
</script></body></html>"""
