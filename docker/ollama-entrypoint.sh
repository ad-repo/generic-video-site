#!/bin/sh
set -e

# If a seed directory exists, copy models into runtime OLLAMA_HOME
if [ -d "/seed_ollama" ]; then
  mkdir -p "$OLLAMA_HOME"
  cp -r /seed_ollama/* "$OLLAMA_HOME" 2>/dev/null || true
fi

exec /bin/ollama serve

