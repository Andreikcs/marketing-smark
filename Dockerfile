# smark Studio — Super Editor (Railway)
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIND_HOST=0.0.0.0 \
    PORT=8080

WORKDIR /app

# deps de sistema leves (Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código do vault (sem .env / .secrets / .git — ver .dockerignore)
COPY . .

# editor.json mínimo se faltar no build context
RUN test -f editor.json || echo '{"posts":[],"version":1}' > editor.json

EXPOSE 8080
CMD ["python3", "scripts/editor_server.py"]
