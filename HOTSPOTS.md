# Hotspots

- Ollama inference dominates end-to-end agent latency and memory usage.
- SQLite aggregation and database-file I/O dominate direct firewall analytics; the fixed TCP/BLOCK aggregate measured 2.386 ms median locally.
- MCP discovery/tool calls add local HTTP round trips. MCPHub bounds connect, request, tool-call, response-size, iteration, call-count, and total agent execution limits; a future benchmark will separate these from Ollama inference.
