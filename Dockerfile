FROM python:3.11-slim

WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopíruj backend složku
COPY backend/ /app/backend

WORKDIR /app/backend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5050

CMD ["gunicorn", "-b", "0.0.0.0:5050", "backend.app:app"]