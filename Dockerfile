FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
		ca-certificates \
		curl \
		&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY static ./static

ENV VIDEO_BASE_DIR=/videos

EXPOSE 1111
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "1111"]
