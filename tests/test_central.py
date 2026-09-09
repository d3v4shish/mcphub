from pathlib import Path

from fastapi.testclient import TestClient

from firewall_agent import central
from firewall_agent.settings import Settings

TOOLS = [
    {
        "name": "summarize_firewall_logs",
        "description": "Summarize logs",
        "inputSchema": {"type": "object", "properties": {"protocol": {"type": "string"}}},
    },
    {"name": "search_firewall_logs", "description": "Search logs", "inputSchema": {"type": "object"}},
]


def make_client(tmp_path: Path, monkeypatch):
    async def list_tools(_self):
        return TOOLS

    monkeypatch.setattr(central.MCPClient, "list_tools", list_tools)
    app = central.create_app(
        Settings(
            app_api_key="app-key",
            mcp_shared_key="mcp-key",
            central_database_path=tmp_path / "registry.db",
            firewall_database_path=tmp_path / "unused.db",
        )
    )
    return TestClient(app)


def test_registration_and_explicit_tool_allowlist(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        service = {"Authorization": "Bearer mcp-key"}
        user = {"Authorization": "Bearer app-key"}
        response = client.post(
            "/v1/mcp-servers",
            headers=service,
            json={"name": "fw_mcp", "mcp_url": "http://127.0.0.1:9015/mcp"},
        )
        assert response.status_code == 201
        response = client.put(
            "/v1/agents/firewall-analyst",
            headers=user,
            json={
                "description": "Read-only analyst",
                "mcp_servers": ["fw_mcp"],
                "allowed_tools": {"fw_mcp": ["summarize_firewall_logs"]},
            },
        )
        assert response.status_code == 201
        assert client.get("/v1/agents", headers=user).json()[0]["name"] == "firewall-analyst"


def test_rejects_nonlocal_mcp_url(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/v1/mcp-servers",
            headers={"Authorization": "Bearer mcp-key"},
            json={"name": "unsafe", "mcp_url": "http://example.com/mcp"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "http_422"


def test_agent_invocation_uses_only_allowlisted_tool(tmp_path, monkeypatch):
    calls = []

    async def fake_ollama(_settings, messages, _tools):
        if any(message["role"] == "tool" for message in messages):
            return {"message": {"role": "assistant", "content": "There were 1824 blocked TCP events."}}
        return {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "summarize_firewall_logs",
                            "arguments": {"protocol": "TCP", "action": "BLOCK", "group_by": "action"},
                        }
                    }
                ],
            }
        }

    async def call_tool(_self, name, arguments):
        calls.append((name, arguments))
        return {"groups": [{"group_value": "BLOCK", "event_count": 1824}]}

    monkeypatch.setattr(central, "call_ollama", fake_ollama)
    monkeypatch.setattr(central.MCPClient, "call_tool", call_tool)
    with make_client(tmp_path, monkeypatch) as client:
        service = {"Authorization": "Bearer mcp-key"}
        user = {"Authorization": "Bearer app-key"}
        client.post(
            "/v1/mcp-servers", headers=service, json={"name": "fw_mcp", "mcp_url": "http://localhost:9015/mcp"}
        )
        client.put(
            "/v1/agents/a",
            headers=user,
            json={"description": "x", "mcp_servers": ["fw_mcp"], "allowed_tools": {"fw_mcp": ["summarize_firewall_logs"]}},
        )
        response = client.post("/v1/agents/a:invoke", headers=user, json={"message": "Count blocked TCP"})
        assert response.status_code == 200
        assert response.json()["tool_calls"] == [{"name": "summarize_firewall_logs", "status": "ok"}]
        assert calls[0][0] == "summarize_firewall_logs"
