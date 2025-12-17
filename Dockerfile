FROM python:3.11-slim

WORKDIR /app/backend

# systémové závislosti (nemění se → cache)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ⬇️ NEJDŮLEŽITĚJŠÍ ZMĚNA:
# nejdřív jen requirements → pip install se cachuje
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# až POTOM celý backend (často se mění)
COPY backend/ /app/backend

EXPOSE 5050

CMD ["gunicorn", "-b", "0.0.0.0:5050", "--timeout", "300", "app:app"]

