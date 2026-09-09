import pytest

from mcphub.url_validation import normalize_mcp_url


@pytest.mark.parametrize("url", ["http://localhost/mcp", "http://127.0.0.1:9015/mcp", "http://[::1]:9015/mcp"])
def test_accepts_only_canonical_loopback_mcp_urls(url):
    assert normalize_mcp_url(url).endswith("/mcp")


@pytest.mark.parametrize("url", ["http://localhost.evil.com/mcp", "http://127.0.0.1.evil.com/mcp", "http://user@127.0.0.1/mcp", "http://127.0.0.1/mcp?target=example.com", "http://127.0.0.1/%6dcp", "http://2130706433/mcp", "http://127.1/mcp", "http://[::ffff:127.0.0.1]/mcp", "https://127.0.0.1/mcp", "http://127.0.0.1/not-mcp"])
def test_rejects_ssrf_bypass_urls(url):
    with pytest.raises(ValueError):
        normalize_mcp_url(url)
