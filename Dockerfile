FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appuser && adduser --system --group appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY backend_main.py .
COPY backend_models.py .
COPY backend_schemas.py .
COPY backend_database.py .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend_main:app --host 0.0.0.0 --port ${PORT:-8000}"]
