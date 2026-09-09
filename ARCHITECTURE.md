# Architecture

The `mcphub` package contains the generic control plane. `central.py` exposes the authenticated HTTP API and registry persistence; `routing.py` maps model-visible `server__tool` IDs to exact MCP server/native tool identities; `policy.py` validates agent → server → native-tool permissions; `mcp_client.py` owns MCP v2 negotiation, request metadata, HTTP transport limits, and tool result limits; `url_validation.py` is the single loopback-URL trust boundary. The client disables redirects, so a validated local endpoint cannot redirect the hub to a remote host.

The central FastAPI process stores MCP inventory, discovered tool schemas, agents, and explicit agent/tool associations in SQLite WAL mode. It exposes only policy-authorized namespaced schemas to Ollama and translates selected IDs back to native MCP names at execution. It revalidates stored policy against the current registered manifest before every invocation. HTTP work is asynchronous; SQLite is deliberately operated by one API worker. No prompt or tool payload records are persisted.

Firewall, asset-inventory, and threat-intelligence are deterministic local example MCP servers. The firewall example owns read-only access to its SQLite fixture; every example service requires the shared Bearer key for `/mcp`.
