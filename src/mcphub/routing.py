"""Explicit translation between model-visible and native MCP tool identities."""

from dataclasses import dataclass
from typing import Any


class ToolRegistrationError(ValueError):
    pass


@dataclass(frozen=True)
class RoutedTool:
    exposed_name: str
    server_name: str
    native_name: str
    definition: dict[str, Any]


def exposed_tool_name(server_name: str, native_name: str) -> str:
    """Return the stable tool identity exposed to the LLM."""

    return f"{server_name}__{native_name}"


def validate_manifest(server_name: str, definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reject malformed and duplicate native tools before persisting a manifest."""

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for definition in definitions:
        if not isinstance(definition, dict) or not isinstance(definition.get("name"), str):
            raise ToolRegistrationError(f"{server_name} returned a malformed tool definition")
        native_name = definition["name"]
        if not native_name:
            raise ToolRegistrationError(f"{server_name} returned an empty tool name")
        if native_name in seen:
            raise ToolRegistrationError(f"{server_name} returned duplicate tool name: {native_name}")
        seen.add(native_name)
        normalized.append(definition)
    return normalized


def route_tools(
    server_name: str, definitions: list[dict[str, Any]], allowed_native_names: set[str]
) -> list[RoutedTool]:
    """Create collision-safe routes for the tools an agent is allowed to use."""

    routes: list[RoutedTool] = []
    exposed: set[str] = set()
    for definition in validate_manifest(server_name, definitions):
        native_name = definition["name"]
        if native_name not in allowed_native_names:
            continue
        exposed_name = exposed_tool_name(server_name, native_name)
        if exposed_name in exposed:
            raise ToolRegistrationError(f"duplicate exposed tool name: {exposed_name}")
        exposed.add(exposed_name)
        routes.append(RoutedTool(exposed_name, server_name, native_name, definition))
    return routes


def model_tool(route: RoutedTool) -> dict[str, Any]:
    """Copy an MCP schema and replace only its model-visible name."""

    function = dict(route.definition)
    function["name"] = route.exposed_name
    return {"type": "function", "function": function}
