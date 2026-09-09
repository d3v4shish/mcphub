"""Compatibility entry point for the production MCP firewall server."""

from mcphub.mcp_server import app, run

__all__ = ["app", "run"]

if __name__ == "__main__":
    run()
