"""Fixed-input local benchmark; results vary by machine and are not pass/fail tests."""

from statistics import median
from time import perf_counter

from firewall_agent.firewall import FirewallFilters, FirewallRepository
from firewall_agent.settings import get_settings

repository = FirewallRepository(get_settings().firewall_database_path)
samples = []
for _ in range(100):
    started = perf_counter()
    result = repository.summarize(FirewallFilters(protocol="TCP", action="BLOCK"), "action")
    assert result["groups"][0]["event_count"] == 1824
    samples.append((perf_counter() - started) * 1000)
print(f"fixed TCP/BLOCK summary: runs=100 median_ms={median(samples):.3f} min_ms={min(samples):.3f}")
