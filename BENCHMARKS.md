# Benchmarks

Run `scripts/benchmark.sh` on the fixed bundled database. It executes 100 identical TCP/BLOCK summaries and prints median/minimum latency. Record the machine, command, date, and result here before making any performance claim.

## 2026-09-09 baseline

- Command: `APP_API_KEY=benchmark-app MCP_SHARED_KEY=benchmark-mcp FIREWALL_DATABASE_PATH=mcp_servers/firewall_logs.db uv run python examples/benchmark.py`
- Fixture: bundled 10,000-event SQLite firewall log database; 100 identical TCP/BLOCK summaries.
- Machine: AMD Ryzen 7 7800X3D, 16 logical CPUs.
- First run: median `2.386 ms`, minimum `1.082 ms`.
- Immediate repeat through `scripts/benchmark.sh`: median `1.462 ms`, minimum `0.964 ms`.

The variation is consistent with local filesystem/SQLite cache state. These are baseline observations, not improvement claims.
