"""Agent/server/native-tool policy validation."""

from typing import Any


class PolicyError(ValueError):
    pass


def manifest_tool_names(manifest: list[dict[str, Any]]) -> set[str]:
    return {tool["name"] for tool in manifest if isinstance(tool.get("name"), str)}


def validate_allowed_tools(server_name: str, selected: set[str], manifest: list[dict[str, Any]]) -> None:
    missing = selected - manifest_tool_names(manifest)
    if missing:
        raise PolicyError(f"Policy names tools absent from {server_name}: {sorted(missing)}")
