# TODO

- [x] Package application with locked dependencies; contract: a clean checkout builds with `uv`. Validation: `scripts/build.sh`.
- [x] Implement authenticated v1 registry, persistence, MCP discovery, and agent invocation. Validation: API/integration tests.
- [x] Replace raw firewall SQL with read-only typed MCP tools. Validation: in-process MCP tests and fixed fixture results.
- [x] Provide deterministic build, run, test, benchmark, and demonstration scripts. Validation: scripts exit successfully on a configured local machine.
- [x] Record measured benchmark results and current bottlenecks after implementation. Validation: `scripts/benchmark.sh` and documentation review.
- [x] Add deterministic asset and threat-intelligence MCP fixtures plus a real-model routing evaluation. Validation: fixed routing evaluation report.

## MCPHub protocol and routing hardening

- [x] Upgrade to the current MCP Python SDK client with centralized protocol negotiation and bounded transport/tool-call timeouts. Contract: no hub-owned protocol version, session ID, or initialized notification; SDK negotiates current MCP with legacy fallback. Validation: protocol-client unit tests and a live local MCP v2 probe.
- [x] Namespace exposed LLM tool IDs and keep an explicit exposed-ID-to-server/native-tool mapping. Contract: servers exposing the same native name remain independently callable and cannot overwrite metadata. Validation: duplicate-tool routing tests.
- [x] Enforce agent → server → native-tool policy both on configuration and execution. Contract: unknown, fabricated, stale, and unauthorized selections fail deterministically. Validation: policy-denial tests.
- [x] Rename the runtime package from `firewall_agent` to `mcphub` and keep firewall services as examples. Contract: generic hub imports and commands no longer use firewall-specific names. Validation: build and tests from a clean environment.
- [x] Centralize strict loopback URL validation and document disabled redirects. Contract: no URL parsing or redirect path may bypass local-only MCP policy. Validation: SSRF regression tests.
- [ ] Defer lifecycle-state expansion, malformed-server fixtures, evaluation/scaling benchmarks, candidate pre-routing, and external-project examples to later commits. Validation: tracked as explicit follow-up work rather than implied completion.
