# TODO

- [x] Package application with locked dependencies; contract: a clean checkout builds with `uv`. Validation: `scripts/build.sh`.
- [x] Implement authenticated v1 registry, persistence, MCP discovery, and agent invocation. Validation: API/integration tests.
- [x] Replace raw firewall SQL with read-only typed MCP tools. Validation: in-process MCP tests and fixed fixture results.
- [x] Provide deterministic build, run, test, benchmark, and demonstration scripts. Validation: scripts exit successfully on a configured local machine.
- [x] Record measured benchmark results and current bottlenecks after implementation. Validation: `scripts/benchmark.sh` and documentation review.
- [x] Add deterministic asset and threat-intelligence MCP fixtures plus a real-model routing evaluation. Validation: fixed routing evaluation report.
