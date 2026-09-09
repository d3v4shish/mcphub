"""Small, standards-based MCP Streamable HTTP client for the central service.

The server is produced by the official MCP Python SDK. This client intentionally uses
the protocol's JSON-RPC messages so the central service has no dependency on an agent
framework and can set its local authentication header explicitly.
"""

import json
from itertools import count
from typing import Any

import httpx


class MCPProtocolError(RuntimeError):
    pass


def _decode_response(response: httpx.Response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line.removeprefix("data:").strip())
    raise MCPProtocolError("MCP server returned neither JSON nor SSE JSON")


class MCPClient:
    def __init__(self, url: str, shared_key: str):
        self.url = url
        self.shared_key = shared_key
        self._ids = count(1)

    async def _post(self, client: httpx.AsyncClient, message: dict[str, Any], session_id: str | None):
        headers = {
            "Authorization": f"Bearer {self.shared_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        response = await client.post(self.url, headers=headers, json=message)
        if response.status_code >= 400:
            raise MCPProtocolError(f"MCP request failed with HTTP {response.status_code}")
        if response.status_code == 202:
            return {}, response.headers.get("Mcp-Session-Id")
        return _decode_response(response), response.headers.get("Mcp-Session-Id")

    async def _session(self, operation: str, arguments: dict[str, Any] | None = None) -> Any:
        timeout = httpx.Timeout(connect=3, read=20, write=5, pool=3)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            init_id = next(self._ids)
            initialize, session_id = await self._post(
                client,
                {
                    "jsonrpc": "2.0",
                    "id": init_id,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "firewall-central", "version": "1.0.0"},
                    },
                },
                None,
            )
            if "error" in initialize:
                raise MCPProtocolError(str(initialize["error"]))
            await self._post(
                client,
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                session_id,
            )
            request, _ = await self._post(
                client,
                {"jsonrpc": "2.0", "id": next(self._ids), "method": operation, "params": arguments or {}},
                session_id,
            )
        if "error" in request:
            raise MCPProtocolError(str(request["error"]))
        return request.get("result")

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._session("tools/list")
        tools = result.get("tools") if isinstance(result, dict) else None
        if not isinstance(tools, list):
            raise MCPProtocolError("MCP tools/list response has no tools array")
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        result = await self._session("tools/call", {"name": name, "arguments": arguments})
        if not isinstance(result, dict):
            raise MCPProtocolError("MCP tools/call response is invalid")
        if result.get("isError"):
            raise MCPProtocolError(str(result.get("content", "tool failed")))
        content = result.get("content", [])
        text = "".join(item.get("text", "") for item in content if item.get("type") == "text")
        try:
            return json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return text
