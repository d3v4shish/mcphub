import hmac
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from .firewall import Action, FirewallFilters, FirewallRepository, GroupBy, Protocol
from .settings import get_settings

settings = get_settings()
repository = FirewallRepository(settings.firewall_database_path)
mcp = FastMCP("Firewall analytics", instructions="Read-only firewall log analytics.")


@mcp.tool()
def search_firewall_logs(
    start_at: str | None = None,
    end_at: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    protocol: Protocol | None = None,
    action: Action | None = None,
    dst_port: int | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """Return a bounded page of read-only firewall events."""
    filters = FirewallFilters.model_validate(locals() | {"limit": None, "offset": None})
    return repository.search(filters, limit=limit, offset=offset)


@mcp.tool()
def summarize_firewall_logs(
    start_at: str | None = None,
    end_at: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    protocol: Protocol | None = None,
    action: Action | None = None,
    dst_port: int | None = None,
    group_by: GroupBy = "action",
) -> dict[str, Any]:
    """Summarize read-only firewall events by an allowlisted field."""
    filters = FirewallFilters.model_validate(locals() | {"group_by": None})
    return repository.summarize(filters, group_by=group_by)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_request):
    try:
        repository.search(FirewallFilters(), limit=1)
    except Exception as error:
        return JSONResponse({"status": "error", "detail": str(error)}, status_code=503)
    return JSONResponse({"status": "ok"})


class MCPAuthApp:
    """Keep health public while requiring the local shared key for MCP traffic."""

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


app = MCPAuthApp(mcp.streamable_http_app())


def run() -> None:
    uvicorn.run(app, host=settings.app_host, port=settings.mcp_port, log_level=settings.log_level.lower())
