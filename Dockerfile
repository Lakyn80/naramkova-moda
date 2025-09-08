# backend/Dockerfile.backend
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Balíčky pro build některých py modulů (reportlab, bcrypt…)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Závislosti – requirements.txt je v KOŘENI projektu
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir gunicorn==22.0.0

# >>> KLÍČOVÁ ZMĚNA: kopírujeme backend/ pod /app/backend/ <<<
COPY backend/ /app/backend/

EXPOSE 5050

# Spouštíme app factory z balíku "backend"
CMD ["gunicorn", "-b", "0.0.0.0:5050", "backend.app:create_app()", "--workers", "2", "--timeout", "120"]
