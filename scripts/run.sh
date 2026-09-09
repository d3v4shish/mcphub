#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Run scripts/bootstrap.sh first" >&2; exit 1; }
set -a; source .env; set +a
ASSET_MCP_PORT=${ASSET_MCP_PORT:-9016}
THREAT_MCP_PORT=${THREAT_MCP_PORT:-9017}
uv run firewall-mcp &
firewall_pid=$!
uv run asset-mcp &
asset_pid=$!
uv run threat-mcp &
threat_pid=$!
cleanup() { kill "$firewall_pid" "$asset_pid" "$threat_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
ready=0
for _ in $(seq 1 30); do
  if curl -fsS "http://${APP_HOST}:${MCP_PORT}/healthz" >/dev/null 2>&1 && \
    curl -fsS "http://${APP_HOST}:${ASSET_MCP_PORT}/healthz" >/dev/null 2>&1 && \
    curl -fsS "http://${APP_HOST}:${THREAT_MCP_PORT}/healthz" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.2
done
if [[ "$ready" -ne 1 ]]; then
  echo "MCP services did not become healthy" >&2
  exit 1
fi
uv run mcphub
