# Architecture

The local firewall MCP process owns read-only access to the SQLite firewall fixture and exposes `search_firewall_logs` and `summarize_firewall_logs` over Streamable HTTP at `/mcp`. Two deterministic local MCP fixtures add asset-inventory (`lookup_asset`, `find_assets_by_owner`) and threat-intelligence (`lookup_ip_reputation`, `list_high_risk_indicators`) tools. Every MCP service requires the shared Bearer key; the firewall health route is public only on loopback.

The central FastAPI process stores MCP inventory, discovered tool schemas, agents, and explicit agent/tool associations in SQLite WAL mode. It uses MCP JSON-RPC over HTTP to discover/call tools and Ollama's local chat API to run a bounded, four-call tool loop. HTTP work is asynchronous; SQLite is deliberately operated by one API worker. No prompt or log records are persisted.
