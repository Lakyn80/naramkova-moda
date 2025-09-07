# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System deps (pro balíčky jako bcrypt, psycopg2 atd.) ─────────────────────
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential \
     libffi-dev \
     curl \
  && rm -rf /var/lib/apt/lists/*

# ── Python env ────────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ── Zkopíruj jen požadované soubory pro instalaci závislostí ────────────────
# Pokud máš requirements v backend/requirements.txt, použijeme ho.
COPY backend/requirements.txt /app/backend/requirements.txt

# ── Instalace Python závislostí ──────────────────────────────────────────────
RUN pip install --upgrade pip \
 && pip install -r /app/backend/requirements.txt \
 && pip install gunicorn

# ── Zbytek zdrojáků ──────────────────────────────────────────────────────────
# Kopírujeme jen backend – frontend teď do image netaháme.
COPY backend /app/backend

# (Volitelně) Pokud máš .env.production, můžeš si ji zabalit do image:
# COPY backend/.env.production /app/backend/.env
# ENV DOTENV_PATH=/app/backend/.env

# ── Runtime ──────────────────────────────────────────────────────────────────
EXPOSE 8000

# U tebe je app factory v backend/app.py => "backend.app:create_app()"
# -w 3 = 3 worker procesy, --threads 4 = 4 thready na worker
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "3", "--threads", "4", "--timeout", "60", "backend.app:create_app()"]
