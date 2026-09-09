# Build and run

Requires Python 3.11–3.14, `uv`, and Ollama for the real-agent demo.

```bash
./scripts/bootstrap.sh
./scripts/build.sh
./scripts/test.sh
./scripts/run.sh
./scripts/benchmark.sh
```

`bootstrap.sh` is the only script that creates `.env`; it generates local keys once. `run.sh` starts the firewall, asset-inventory, and threat-intelligence MCP processes and foregrounds the central API, cleaning up the children on exit.
