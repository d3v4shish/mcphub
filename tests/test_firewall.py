from pathlib import Path

import pytest

from firewall_agent.firewall import FirewallFilters, FirewallRepository

FIXTURE = Path(__file__).parents[1] / "mcp_servers" / "firewall_logs.db"


def test_summary_is_deterministic_and_read_only():
    repository = FirewallRepository(FIXTURE)
    result = repository.summarize(FirewallFilters(protocol="TCP", action="BLOCK"), "action")
    assert result["filters"] == {"protocol": "TCP", "action": "BLOCK"}
    assert result["groups"] == [{"group_value": "BLOCK", "event_count": 1824, "bytes_transferred": 15043041}]


def test_search_is_bounded():
    repository = FirewallRepository(FIXTURE)
    result = repository.search(FirewallFilters(protocol="TCP"), limit=1000)
    assert result["limit"] == 100
    assert result["returned"] == 100


def test_invalid_filter_and_grouping_are_rejected():
    with pytest.raises(ValueError):
        FirewallFilters(protocol="DROP")
    repository = FirewallRepository(FIXTURE)
    with pytest.raises(ValueError):
        repository.summarize(FirewallFilters(), "timestamp")  # type: ignore[arg-type]
