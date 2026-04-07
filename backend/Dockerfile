FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile spacy==3.8.11 && \
    pip install --no-cache-dir --no-compile -r requirements.txt

# ── Dev stage ────────────────────────────────────────────────────────────────
FROM base AS dev
RUN python -m spacy download de_core_news_lg && \
    python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Prod stage ───────────────────────────────────────────────────────────────
FROM base AS prod
RUN python -m spacy download de_core_news_lg
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
