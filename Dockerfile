# smark Studio — Super Editor (Railway)
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIND_HOST=0.0.0.0 \
    PORT=8080

WORKDIR /app

# Pillow + Chromium.
#
# O Chromium é o que permite ao SERVIDOR compor a arte final. Sem ele, produção
# só sabia mostrar arte gerada no Mac e empurrada à mão — e agendamento era
# impossível (ninguém com o notebook aberto às 9h). É o mesmo renderizador que
# roda local, de propósito: o que o cliente aprova é o que vai pro Instagram.
# As fontes vêm junto senão o Chromium cai em fallback e a tipografia muda.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g libpng16-16 \
    chromium fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código do vault (sem .env / .secrets / .git — ver .dockerignore)
COPY . .

# editor.json mínimo se faltar no build context
RUN test -f editor.json || echo '{"posts":[],"version":1}' > editor.json

EXPOSE 8080
CMD ["python3", "scripts/editor_server.py"]
