from firewall_agent.extra_mcp import (
    find_assets_by_owner,
    list_high_risk_indicators,
    lookup_asset,
    lookup_ip_reputation,
)


def test_asset_fixture_contracts():
    assert lookup_asset("192.168.1.10")["owner"] == "Payments"
    matches = find_assets_by_owner("Analytics")
    assert matches["count"] == 1
    assert matches["assets"][0]["hostname"] == "analytics-worker"


def test_threat_fixture_contracts():
    assert lookup_ip_reputation("203.0.113.10")["reputation"] == "malicious"
    indicators = list_high_risk_indicators(90)
    assert {row["ip"] for row in indicators["indicators"]} == {"203.0.113.10", "198.51.100.99"}
