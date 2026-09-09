from contextlib import asynccontextmanager

import pytest

from mcphub import mcp_client


class FakeHTTPClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


class FakeTool:
    def model_dump(self, **_):
        return {"name": "search", "description": "Search", "inputSchema": {"type": "object"}}


class FakeResult:
    tools = [FakeTool()]
    next_cursor = None


def test_uses_sdk_negotiation_with_current_metadata_and_no_redirects(monkeypatch):
    captured = {}

    @asynccontextmanager
    async def fake_transport(url, *, http_client):
        captured["url"] = url
        captured["http_client"] = http_client
        yield "transport"

    class FakeClient:
        def __init__(self, transport, **kwargs):
            captured["transport"] = transport
            captured["client_kwargs"] = kwargs
            self.transport = transport
            self.protocol_version = "2026-07-28"

        async def __aenter__(self):
            await self.transport.__aenter__()
            return self

        async def __aexit__(self, *_):
            await self.transport.__aexit__(None, None, None)
            return False

        async def list_tools(self, **_):
            return FakeResult()

    monkeypatch.setattr(mcp_client.httpx2, "AsyncClient", FakeHTTPClient)
    monkeypatch.setattr(mcp_client, "streamable_http_client", fake_transport)
    monkeypatch.setattr(mcp_client, "Client", FakeClient)
    client = mcp_client.MCPClient("http://127.0.0.1:9015/mcp", "secret")
    assert asyncio_run(client.list_tools()) == [{"name": "search", "description": "Search", "inputSchema": {"type": "object"}}]
    assert client.protocol_version == "2026-07-28"
    assert captured["http_client"].kwargs["follow_redirects"] is False
    assert captured["http_client"].kwargs["headers"] == {"Authorization": "Bearer secret"}
    assert "protocol_version" not in captured["client_kwargs"]


def asyncio_run(awaitable):
    import asyncio

    return asyncio.run(awaitable)


def test_protocol_negotiation_failure_is_a_clean_error(monkeypatch):
    @asynccontextmanager
    async def fake_transport(_url, *, http_client):
        yield "transport"

    class IncompatibleClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            raise RuntimeError("server protocol is incompatible")

        async def __aexit__(self, *_):
            return False

    monkeypatch.setattr(mcp_client, "Client", IncompatibleClient)
    monkeypatch.setattr(mcp_client, "streamable_http_client", fake_transport)
    with pytest.raises(mcp_client.MCPProtocolError, match="MCP protocol error"):
        asyncio_run(mcp_client.MCPClient("http://127.0.0.1:9015/mcp", "secret").list_tools())
