"""Compatibility entry point for the production MCP firewall server."""

from firewall_agent.mcp_server import app, run

if __name__ == "__main__":
    run()
