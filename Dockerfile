FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8502 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    LANG=es_ES.UTF-8 \
    LANGUAGE=es_ES:es \
    LC_ALL=es_ES.UTF-8 \
    PATH="/home/appuser/.local/bin:$PATH" \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libglib2.0-0 \
      libgl1 \
      qpdf \
      libjpeg62-turbo zlib1g libfreetype6 libstdc++6 \
      fonts-dejavu \
      locales \
    && echo "es_ES.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen && update-locale LANG=es_ES.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g $GROUP_ID appuser \
 && useradd -m -u $USER_ID -g $GROUP_ID appuser

USER appuser

# Cache-friendly: copy requirements first
COPY --chown=appuser:appuser requirements.txt .

# Python deps (user install)
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY --chown=appuser:appuser . /app

# Writable dirs
RUN mkdir -p /app/logs /app/data /tmp/matplotlib

VOLUME ["/app/data", "/app/logs"]

EXPOSE 8502

# (Optional) simple healthcheck
# HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
#   CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', 8502))"

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
