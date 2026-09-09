"""Compatibility ASGI entry point. Use `firewall-central` for normal operation."""

from firewall_agent.central import app

__all__ = ["app"]
