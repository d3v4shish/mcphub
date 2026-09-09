# MCPHub

MCPHub is a policy-controlled, local-first MCP control plane. A central FastAPI service registers standard MCP servers and lets a local Ollama agent call only explicitly allowed tools. Firewall, asset, and threat services are deterministic example servers, not part of the hub's trust model.

## Quick start

```bash
./scripts/bootstrap.sh
ollama serve                 # if Ollama is not already running
ollama pull llama3.1:8b
./scripts/run.sh             # terminal 1
./examples/run_demo.sh       # terminal 2
```

The services bind to `127.0.0.1`: central API on `8015`, MCP on `9015`. The demo registers `fw_mcp`, creates `firewall-analyst`, and invokes it with a real Ollama prompt. `examples/mcp_client.py` directly lists and calls standard MCP tools after sourcing `.env`.

Use `scripts/build.sh`, `scripts/test.sh`, and `scripts/benchmark.sh` from a clean checkout. Tests use the bundled fixed 10,000-event fixture and a fake model; they do not require Ollama or network access.

## API

All `/v1` client routes need `Authorization: Bearer $APP_API_KEY`; MCP registration needs `$MCP_SHARED_KEY`.

- `POST /v1/mcp-servers` accepts `name` and a canonical loopback `mcp_url`.
- `PUT /v1/agents/{name}` stores an explicit `agent -> server -> native tool` allowlist.
- `POST /v1/agents/{name}:invoke` accepts `{"message":"..."}`.
- `/healthz`, `/readyz`, and `/metrics` are local operational endpoints.

Models receive namespaced tool IDs such as `github__search` and `jira__search`; MCPHub maps each ID back to its server and native MCP tool name before `tools/call`. A model may never call a server or tool merely because it exists. Unknown, fabricated, unauthorized, and stale policy entries are denied deterministically.

MCPHub uses the official MCP v2 client for current protocol discovery and legacy fallback. It does not own a hard-coded protocol version, initialization notification, or session ID. Service credentials are sent as a transport header, redirects are disabled, and only `http://localhost`, IPv4 loopback, or IPv6 loopback URLs at `/mcp` are accepted. The firewall database is opened read-only; raw SQL, shells, and generic code-execution tools are deliberately unsupported.

MCP requests have explicit connect, request, tool-call, and response-size limits. The agent has explicit iteration, tool-call, and total-execution-time limits; configure them with the documented `MCP_*` and `AGENT_*` environment variables in `.env.example`.

## Multi-MCP routing evaluation

`asset-mcp` and `threat-mcp` provide deterministic inventory and threat-intelligence fixtures on ports `9016` and `9017`. `scripts/run.sh` starts all three MCP services and the central API. Then execute `uv run python examples/evaluate_routing.py`; it registers a `security-analyst` agent with six explicitly allowed tools and scores five fixed prompts by selected tool and expected answer text.
