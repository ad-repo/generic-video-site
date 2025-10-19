#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Fast deployment with cache..."

# Stop existing containers
echo "Stopping containers..."
docker-compose down || true

# Ensure persistent directories exist and have correct permissions
echo "Setting up persistent directories..."
# Use relative paths for local development
mkdir -p ./db
chmod 777 ./db
echo "✅ Database will persist in ./db/"

mkdir -p ./ollama
chmod 777 ./ollama
echo "✅ Ollama models will persist in ./ollama/"

# Build with cache (much faster for development)
echo "Building with cache using uv..."
DOCKER_BUILDKIT=1 docker-compose build

# Start containers
echo "Starting containers..."
docker-compose up -d

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready on :11434..."
until curl -sf http://localhost:11434/api/tags >/dev/null; do
  sleep 2
done

# Pre-pull summarization models (idempotent)
echo "Pulling baseline Ollama models if not present (trimmed + fastest)..."
docker-compose exec -T ollama ollama pull llama3.2:1b || true
docker-compose exec -T ollama ollama pull llama3.1:8b || true
docker-compose exec -T ollama ollama pull llama3.2:3b || true
docker-compose exec -T ollama ollama pull qwen2.5:3b-instruct || true

# Restart app to pick up OLLAMA_MODEL env changes
echo "Restarting app to pick up model selection..."
docker-compose restart generic-video-site

# Wait for app to be healthy
echo "Waiting for app health on :8000/health..."
until curl -sf http://localhost:8000/health >/dev/null; do
  sleep 2
done

echo "✅ Fast deployment completed!"
echo "🔥 Used build cache for faster iteration"
echo "💡 For production deployments, use: ./deploy-with-cache-clear.sh"
echo ""
echo "Check your browser for the updated site."
