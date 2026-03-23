FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL=http://ollama:11434 \
    MKM_HTTP_HOST=0.0.0.0

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mkmchat ./mkmchat

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && mkdir -p /app/.cache/huggingface \
    && chown -R appuser:appgroup /app

ENV HOME=/app \
    HF_HOME=/app/.cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/app/.cache/huggingface/hub

USER appuser

EXPOSE 8080

CMD ["python", "-m", "mkmchat", "http", "8080"]
