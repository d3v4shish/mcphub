"""Exercise the standard MCP endpoint without the central API."""

import asyncio
import json
import os

from mcphub.mcp_client import MCPClient


async def main() -> None:
    client = MCPClient(os.environ.get("MCP_URL", "http://127.0.0.1:9015/mcp"), os.environ["MCP_SHARED_KEY"])
    print(json.dumps(await client.list_tools(), indent=2))
    print(json.dumps(await client.call_tool("summarize_firewall_logs", {"protocol": "TCP", "action": "BLOCK", "group_by": "action"}), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
