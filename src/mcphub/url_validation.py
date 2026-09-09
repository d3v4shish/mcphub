"""The single trust boundary for MCP endpoint URLs."""

from ipaddress import ip_address
from urllib.parse import unquote, urlsplit, urlunsplit


def normalize_mcp_url(value: str) -> str:
    """Accept only a canonical loopback Streamable HTTP endpoint.

    Redirects are disabled in ``MCPClient``. Consequently a URL validated here
    cannot become a remote request through a redirect response.
    """

    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or "%" in parsed.netloc
    ):
        raise ValueError("mcp_url must be a plain local http URL")
    host = parsed.hostname.lower()
    try:
        address = ip_address(host)
        is_loopback = address.is_loopback and getattr(address, "ipv4_mapped", None) is None
    except ValueError:
        is_loopback = host == "localhost"
    if not is_loopback:
        raise ValueError("mcp_url host must be loopback-only")
    if "%" in parsed.path or unquote(parsed.path) != parsed.path:
        raise ValueError("mcp_url path must not be encoded")
    path = parsed.path.rstrip("/") or "/mcp"
    if path != "/mcp":
        raise ValueError("mcp_url path must be /mcp")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))
