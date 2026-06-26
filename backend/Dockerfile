# SwingAI API (FastAPI) — production image for Render/Railway/Fly.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# system deps for asyncpg/cryptography wheels are prebuilt; keep the image lean
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# The host platform sets $PORT. Run migrations/seed on boot via the app lifespan.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
