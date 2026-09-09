"""MCP v2 client wrapper with centralized protocol and transport controls."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Implementation


class MCPProtocolError(RuntimeError):
    pass


class MCPClient:
    """Use the official client so it negotiates current MCP and legacy fallback."""

    def __init__(
        self,
        url: str,
        shared_key: str,
        *,
        connect_timeout_seconds: float = 3,
        request_timeout_seconds: float = 20,
        tool_call_timeout_seconds: float = 20,
        max_response_bytes: int = 262_144,
    ):
        self.url = url
        self.shared_key = shared_key
        self.connect_timeout_seconds = connect_timeout_seconds
        self.request_timeout_seconds = request_timeout_seconds
        self.tool_call_timeout_seconds = tool_call_timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.protocol_version: str | None = None

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[Client]:
        timeout = httpx2.Timeout(
            connect=self.connect_timeout_seconds,
            read=self.request_timeout_seconds,
            write=self.request_timeout_seconds,
            pool=self.connect_timeout_seconds,
        )
        try:
            async with httpx2.AsyncClient(
                headers={"Authorization": f"Bearer {self.shared_key}"},
                timeout=timeout,
                follow_redirects=False,
                trust_env=False,
            ) as http_client:
                transport = streamable_http_client(self.url, http_client=http_client)
                async with Client(
                    transport,
                    client_info=Implementation(name="mcphub", version="1.0.0"),
                    read_timeout_seconds=self.request_timeout_seconds,
                ) as client:
                    self.protocol_version = getattr(client, "protocol_version", None)
                    yield client
        except TimeoutError as error:
            raise MCPProtocolError("MCP request timed out") from error
        except MCPProtocolError:
            raise
        except Exception as error:
            raise MCPProtocolError(f"MCP protocol error: {type(error).__name__}") from error

    async def list_tools(self) -> list[dict[str, Any]]:
        try:
            async with asyncio.timeout(self.request_timeout_seconds):
                async with self._client() as client:
                    tools: list[dict[str, Any]] = []
                    cursor: str | None = None
                    while True:
                        result = await client.list_tools(cursor=cursor, cache_mode="bypass")
                        tools.extend(tool.model_dump(by_alias=True, mode="json") for tool in result.tools)
                        cursor = result.next_cursor
                        if cursor is None:
                            return tools
        except TimeoutError as error:
            raise MCPProtocolError("MCP discovery timed out") from error

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            async with asyncio.timeout(self.tool_call_timeout_seconds):
                async with self._client() as client:
                    result = await client.call_tool(
                        name, arguments, read_timeout_seconds=self.tool_call_timeout_seconds
                    )
        except TimeoutError as error:
            raise MCPProtocolError("MCP tool call timed out") from error
        if result.is_error:
            raise MCPProtocolError("MCP tool returned an error")
        payload = result.structured_content
        if payload is None:
            content = [item.model_dump(by_alias=True, mode="json") for item in result.content]
            text = "".join(item.get("text", "") for item in content if item.get("type") == "text")
            try:
                payload = json.loads(text)
            except (TypeError, json.JSONDecodeError):
                payload = text
        try:
            encoded = json.dumps(payload, separators=(",", ":")).encode()
        except (TypeError, ValueError) as error:
            raise MCPProtocolError("MCP tool response is not JSON serializable") from error
        if len(encoded) > self.max_response_bytes:
            raise MCPProtocolError("MCP tool response exceeds configured size limit")
        return payload
