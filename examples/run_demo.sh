#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Run scripts/bootstrap.sh first" >&2; exit 1; }
set -a; source .env; set +a
central="http://${APP_HOST}:${CENTRAL_PORT}"
auth=(-H "Authorization: Bearer ${APP_API_KEY}")
service=(-H "Authorization: Bearer ${MCP_SHARED_KEY}")
curl -fsS -X POST "$central/v1/mcp-servers" "${service[@]}" -H 'Content-Type: application/json' \
  -d "{\"name\":\"fw_mcp\",\"mcp_url\":\"http://${APP_HOST}:${MCP_PORT}/mcp\"}"
curl -fsS -X PUT "$central/v1/agents/firewall-analyst" "${auth[@]}" -H 'Content-Type: application/json' \
  -d '{"description":"Read-only firewall analyst","mcp_servers":["fw_mcp"],"allowed_tools":{"fw_mcp":["search_firewall_logs","summarize_firewall_logs"]}}'
curl -fsS -X POST "$central/v1/agents/firewall-analyst:invoke" "${auth[@]}" -H 'Content-Type: application/json' \
  -d '{"message":"Use summarize_firewall_logs with protocol TCP, action BLOCK, and group_by action. Report the blocked event count."}'
