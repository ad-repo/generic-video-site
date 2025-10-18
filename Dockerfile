FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        && rm -rf /var/lib/apt/lists/*

## Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

COPY app ./app
COPY static ./static

# Create database directory with full permissions for SQLite
# SQLite needs write access to both the database file and directory for temp/journal files
RUN mkdir -p /app/db && \
    chmod 777 /app/db

# Note: Container runs as root (configured in docker-compose.yml) to avoid permission issues

# VIDEO_BASE_DIR is set by docker-compose to match volume mount path

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
