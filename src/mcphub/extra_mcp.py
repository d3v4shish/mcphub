"""Deterministic asset and threat-intelligence MCP fixtures for routing evaluation."""

import hmac
from typing import Literal

import uvicorn
from mcp.server.mcpserver import MCPServer
from starlette.responses import JSONResponse

from .settings import get_settings

settings = get_settings()
ASSETS = {
    "192.168.1.10": {"hostname": "payments-api", "owner": "Payments", "criticality": "high"},
    "192.168.1.20": {"hostname": "analytics-worker", "owner": "Analytics", "criticality": "medium"},
    "192.168.1.30": {"hostname": "engineering-laptop", "owner": "Engineering", "criticality": "low"},
}
THREATS = {
    "203.0.113.10": {"reputation": "malicious", "confidence": 95, "category": "credential-theft"},
    "198.51.100.25": {"reputation": "suspicious", "confidence": 72, "category": "scanner"},
    "198.51.100.99": {"reputation": "malicious", "confidence": 91, "category": "botnet"},
}

asset_mcp = MCPServer("Asset inventory", instructions="Read-only local asset inventory.")
threat_mcp = MCPServer("Threat intelligence", instructions="Read-only local threat intelligence.")


@asset_mcp.custom_route("/healthz", methods=["GET"])
async def asset_healthz(_request):
    return JSONResponse({"status": "ok"})


@threat_mcp.custom_route("/healthz", methods=["GET"])
async def threat_healthz(_request):
    return JSONResponse({"status": "ok"})


@asset_mcp.tool()
def lookup_asset(ip: str) -> dict:
    """Return owner, hostname, and criticality for one private asset IP."""
    return {"ip": ip, **ASSETS.get(ip, {"status": "not_found"})}


@asset_mcp.tool()
def find_assets_by_owner(owner: Literal["Payments", "Analytics", "Engineering"]) -> dict:
    """Return every asset owned by Payments, Analytics, or Engineering."""
    matches = [{"ip": ip, **asset} for ip, asset in ASSETS.items() if asset["owner"] == owner]
    return {"owner": owner, "assets": matches, "count": len(matches)}


@threat_mcp.tool()
def lookup_ip_reputation(ip: str) -> dict:
    """Return deterministic reputation, confidence, and category for a public IP."""
    return {"ip": ip, **THREATS.get(ip, {"status": "not_found"})}


@threat_mcp.tool()
def list_high_risk_indicators(min_confidence: int = 90) -> dict:
    """List indicators at or above min_confidence (0 through 100)."""
    bounded = min(max(min_confidence, 0), 100)
    indicators = [{"ip": ip, **record} for ip, record in THREATS.items() if record["confidence"] >= bounded]
    return {"min_confidence": bounded, "indicators": indicators, "count": len(indicators)}


class MCPAuthApp:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") == "/mcp":
            headers = {key.decode().lower(): value.decode() for key, value in scope["headers"]}
            token = headers.get("authorization", "").removeprefix("Bearer ")
            if not hmac.compare_digest(token, settings.mcp_shared_key):
                response = JSONResponse({"error": "unauthorized"}, status_code=401)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


asset_app = MCPAuthApp(asset_mcp.streamable_http_app())
threat_app = MCPAuthApp(threat_mcp.streamable_http_app())


def run_asset() -> None:
    uvicorn.run(asset_app, host=settings.app_host, port=settings.asset_mcp_port, log_level=settings.log_level.lower())


def run_threat() -> None:
    uvicorn.run(threat_app, host=settings.app_host, port=settings.threat_mcp_port, log_level=settings.log_level.lower())
