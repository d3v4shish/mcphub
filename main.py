"""Compatibility ASGI entry point. Use `mcphub` for normal operation."""

from mcphub.central import app

__all__ = ["app"]
