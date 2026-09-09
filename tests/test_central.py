from pathlib import Path

from fastapi.testclient import TestClient

from mcphub import central
from mcphub.settings import Settings

FIREWALL_TOOLS = [
    {"name": "summarize_firewall_logs", "description": "Summarize firewall logs", "inputSchema": {"type": "object"}},
    {"name": "search_firewall_logs", "description": "Search firewall logs", "inputSchema": {"type": "object"}},
]
GITHUB_TOOLS = [{"name": "search", "description": "Search GitHub", "inputSchema": {"type": "object"}}]
JIRA_TOOLS = [{"name": "search", "description": "Search Jira", "inputSchema": {"type": "object"}}]


def make_client(tmp_path: Path, monkeypatch, manifests: dict[str, list[dict]] | None = None):
    manifests = manifests or {}

    async def list_tools(mcp_client):
        return manifests.get(mcp_client.url, FIREWALL_TOOLS)

    monkeypatch.setattr(central.MCPClient, "list_tools", list_tools)
    return TestClient(
        central.create_app(
            Settings(
                app_api_key="app-key", mcp_shared_key="mcp-key", central_database_path=tmp_path / "registry.db"
            )
        )
    )


def register(client, name, port):
    return client.post(
        "/v1/mcp-servers",
        headers={"Authorization": "Bearer mcp-key"},
        json={"name": name, "mcp_url": f"http://127.0.0.1:{port}/mcp"},
    )


def configure(client, name, allowed_tools):
    return client.put(
        f"/v1/agents/{name}",
        headers={"Authorization": "Bearer app-key"},
        json={"description": "deterministic test agent", "mcp_servers": list(allowed_tools), "allowed_tools": allowed_tools},
    )


def test_registration_and_explicit_tool_allowlist(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = register(client, "fw_mcp", 9015)
        assert response.status_code == 201
        assert response.json()["exposed_tools"] == ["fw_mcp__summarize_firewall_logs", "fw_mcp__search_firewall_logs"]
        assert configure(client, "firewall-analyst", {"fw_mcp": ["summarize_firewall_logs"]}).status_code == 201
        assert client.get("/v1/agents", headers={"Authorization": "Bearer app-key"}).json()[0]["name"] == "firewall-analyst"


def test_rejects_nonlocal_mcp_url(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/v1/mcp-servers",
            headers={"Authorization": "Bearer mcp-key"},
            json={"name": "unsafe", "mcp_url": "http://example.com/mcp"},
        )
        assert response.status_code == 422


def test_same_native_tool_name_is_namespaced_and_independently_callable(tmp_path, monkeypatch):
    manifests = {"http://127.0.0.1:9015/mcp": GITHUB_TOOLS, "http://127.0.0.1:9016/mcp": JIRA_TOOLS}
    calls, schemas = [], []

    async def fake_ollama(_settings, messages, tools):
        schemas.append(tools)
        if any(message["role"] == "tool" for message in messages):
            return {"message": {"role": "assistant", "content": "Both searches completed."}}
        return {"message": {"role": "assistant", "tool_calls": [
            {"function": {"name": "github__search", "arguments": {"q": "MCP"}}},
            {"function": {"name": "jira__search", "arguments": {"q": "MCP"}}},
        ]}}

    async def call_tool(mcp_client, name, arguments):
        calls.append((mcp_client.url, name, arguments))
        return {"server": mcp_client.url, "native_name": name}

    monkeypatch.setattr(central, "call_ollama", fake_ollama)
    monkeypatch.setattr(central.MCPClient, "call_tool", call_tool)
    with make_client(tmp_path, monkeypatch, manifests) as client:
        assert register(client, "github", 9015).status_code == 201
        assert register(client, "jira", 9016).status_code == 201
        assert configure(client, "analyst", {"github": ["search"], "jira": ["search"]}).status_code == 201
        response = client.post("/v1/agents/analyst:invoke", headers={"Authorization": "Bearer app-key"}, json={"message": "search"})
        assert response.status_code == 200
        assert [tool["function"]["name"] for tool in schemas[0]] == ["github__search", "jira__search"]
        assert [tool["function"]["description"] for tool in schemas[0]] == ["Search GitHub", "Search Jira"]
        assert calls == [("http://127.0.0.1:9015/mcp", "search", {"q": "MCP"}), ("http://127.0.0.1:9016/mcp", "search", {"q": "MCP"})]
        assert [call["name"] for call in response.json()["tool_calls"]] == ["github__search", "jira__search"]


def test_policy_denies_unknown_server_and_unknown_tool_during_configuration(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        assert register(client, "github", 9015).status_code == 201
        assert configure(client, "unknown-server", {"jira": ["search"]}).status_code == 404
        assert configure(client, "unknown-tool", {"github": ["not_a_tool"]}).status_code == 422


def test_policy_denies_model_call_to_unallowed_server_tool(tmp_path, monkeypatch):
    manifests = {"http://127.0.0.1:9015/mcp": GITHUB_TOOLS, "http://127.0.0.1:9016/mcp": JIRA_TOOLS}

    async def fake_ollama(_settings, _messages, _tools):
        return {"message": {"role": "assistant", "tool_calls": [{"function": {"name": "jira__search", "arguments": {}}}]}}

    monkeypatch.setattr(central, "call_ollama", fake_ollama)
    with make_client(tmp_path, monkeypatch, manifests) as client:
        assert register(client, "github", 9015).status_code == 201
        assert register(client, "jira", 9016).status_code == 201
        assert configure(client, "github-only", {"github": ["search"]}).status_code == 201
        response = client.post("/v1/agents/github-only:invoke", headers={"Authorization": "Bearer app-key"}, json={"message": "search"})
        assert response.status_code == 502
        assert "unapproved" in response.json()["error"]["message"]


def test_policy_denies_fabricated_tool_and_stale_manifest(tmp_path, monkeypatch):
    manifests = {"http://127.0.0.1:9015/mcp": GITHUB_TOOLS}

    async def fabricated(_settings, _messages, _tools):
        return {"message": {"role": "assistant", "tool_calls": [{"function": {"name": "github__made_up", "arguments": {}}}]}}

    monkeypatch.setattr(central, "call_ollama", fabricated)
    with make_client(tmp_path, monkeypatch, manifests) as client:
        assert register(client, "github", 9015).status_code == 201
        assert configure(client, "analyst", {"github": ["search"]}).status_code == 201
        assert client.post("/v1/agents/analyst:invoke", headers={"Authorization": "Bearer app-key"}, json={"message": "search"}).status_code == 502
        manifests["http://127.0.0.1:9015/mcp"] = [{"name": "issues", "description": "Issues", "inputSchema": {"type": "object"}}]
        assert register(client, "github", 9015).status_code == 200
        response = client.post("/v1/agents/analyst:invoke", headers={"Authorization": "Bearer app-key"}, json={"message": "search"})
        assert response.status_code == 409
        assert "revalidation" in response.json()["error"]["message"]


def test_registration_rejects_duplicate_native_tools(tmp_path, monkeypatch):
    duplicate = [{"name": "search", "inputSchema": {}}, {"name": "search", "inputSchema": {}}]
    with make_client(tmp_path, monkeypatch, {"http://127.0.0.1:9015/mcp": duplicate}) as client:
        response = register(client, "github", 9015)
        assert response.status_code == 502
        assert "duplicate tool" in response.json()["error"]["message"]
