# Hotspots

- Ollama inference dominates end-to-end agent latency and memory usage.
- SQLite aggregation and database-file I/O dominate direct firewall analytics; the fixed TCP/BLOCK aggregate measured 2.386 ms median locally.
- MCP discovery/tool calls add local HTTP round trips. The central service bounds their connection/read timeouts and tool loop count.
