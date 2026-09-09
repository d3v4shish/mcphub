"""Run five fixed real-model routing checks against the local multi-MCP stack."""

import json
import os

import httpx


def request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    response = httpx.request(
        method, url, headers={"Authorization": f"Bearer {token}"}, json=body, timeout=120
    )
    response.raise_for_status()
    return response.json()


def contains_expected(answer: str, expected: str) -> bool:
    """Treat comma-separated numeric formatting as equivalent for deterministic facts."""
    return expected.lower().replace(",", "") in answer.lower().replace(",", "")


def main() -> None:
    base = os.environ.get("CENTRAL_URL", "http://127.0.0.1:8015")
    app_key, mcp_key = os.environ["APP_API_KEY"], os.environ["MCP_SHARED_KEY"]
    services = [
        ("fw_mcp", "http://127.0.0.1:9015/mcp"),
        ("asset_mcp", "http://127.0.0.1:9016/mcp"),
        ("threat_mcp", "http://127.0.0.1:9017/mcp"),
    ]
    for name, url in services:
        request("POST", f"{base}/v1/mcp-servers", mcp_key, {"name": name, "mcp_url": url})
    allowed = {
        "fw_mcp": ["search_firewall_logs", "summarize_firewall_logs"],
        "asset_mcp": ["lookup_asset", "find_assets_by_owner"],
        "threat_mcp": ["lookup_ip_reputation", "list_high_risk_indicators"],
    }
    request(
        "PUT",
        f"{base}/v1/agents/security-analyst",
        app_key,
        {
            "description": "Routes security questions to the correct read-only MCP tool.",
            "mcp_servers": list(allowed),
            "allowed_tools": allowed,
        },
    )
    cases = [
        ("Use summarize_firewall_logs with protocol TCP, action BLOCK, group_by action. Report the count.", "summarize_firewall_logs", "1824"),
        ("Use lookup_asset for 192.168.1.10. Report its owner.", "lookup_asset", "payments"),
        ("Use find_assets_by_owner for Analytics. Report the hostname.", "find_assets_by_owner", "analytics-worker"),
        ("Use lookup_ip_reputation for 203.0.113.10. Report its reputation.", "lookup_ip_reputation", "malicious"),
        ("Use list_high_risk_indicators with min_confidence 90. Report 198.51.100.99 if present.", "list_high_risk_indicators", "198.51.100.99"),
    ]
    results = []
    for prompt, expected_tool, expected_text in cases:
        result = request("POST", f"{base}/v1/agents/security-analyst:invoke", app_key, {"message": prompt})
        selected = [call["name"] for call in result["tool_calls"]]
        correct = selected == [expected_tool] and contains_expected(result["answer"], expected_text)
        results.append({"expected_tool": expected_tool, "selected_tools": selected, "correct": correct, "answer": result["answer"]})
    print(json.dumps({"correct": sum(row["correct"] for row in results), "total": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
