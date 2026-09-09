# MCPHub

MCPHub is a local, authenticated multi-server MCP hub for security analytics. A central FastAPI service registers standard MCP servers and lets a local Ollama agent call only explicitly allowed tools.

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

- `POST /v1/mcp-servers` accepts `name` and loopback `mcp_url`.
- `PUT /v1/agents/{name}` stores an explicit MCP-server/tool allowlist.
- `POST /v1/agents/{name}:invoke` accepts `{"message":"..."}`.
- `/healthz`, `/readyz`, and `/metrics` are local operational endpoints.

The firewall database is opened read-only. Raw SQL is deliberately unsupported.

## Multi-MCP routing evaluation

`asset-mcp` and `threat-mcp` provide deterministic inventory and threat-intelligence fixtures on ports `9016` and `9017`. `scripts/run.sh` starts all three MCP services and the central API. Then execute `uv run python examples/evaluate_routing.py`; it registers a `security-analyst` agent with six explicitly allowed tools and scores five fixed prompts by selected tool and expected answer text.
