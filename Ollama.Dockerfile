FROM ollama/ollama:latest

# Pre-pull models into a seed directory during build
ENV OLLAMA_HOME=/seed_ollama
RUN (ollama serve & sleep 2; \
     ollama pull llama3.2:1b || true; \
     ollama pull llama3.1:8b || true; \
     ollama pull llama3.2:3b || true; \
     ollama pull qwen2.5:3b-instruct || true; \
     pkill -f ollama || true)

# Runtime defaults
ENV OLLAMA_HOME=/root/.ollama
COPY docker/ollama-entrypoint.sh /usr/local/bin/ollama-entrypoint.sh
RUN chmod +x /usr/local/bin/ollama-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/ollama-entrypoint.sh"]

