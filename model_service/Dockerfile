FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY serve.py .
# model folder (unzipped muril_intent.zip) is copied in at build time
COPY muril_intent ./muril_intent
ENV MODEL_DIR=/app/muril_intent
EXPOSE 8000
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
