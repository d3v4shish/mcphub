#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  cp .env.example .env
  app_key=$(openssl rand -hex 32)
  mcp_key=$(openssl rand -hex 32)
  sed -i "s/replace-with-a-long-random-value/$app_key/" .env
  sed -i "s/replace-with-a-different-long-random-value/$mcp_key/" .env
  chmod 600 .env
  echo "Created .env with local secrets."
fi
uv sync --locked --group dev
echo "Start Ollama, then run: ollama pull llama3.1:8b"
