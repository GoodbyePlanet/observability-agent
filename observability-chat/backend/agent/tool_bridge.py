from mcp.types import Tool


def mcp_tools_to_openai_functions(
    tools: list[tuple[str, Tool]],
) -> list[dict]:
    """Convert MCP tools to OpenAI function-calling tool definitions.

    Each tool is namespaced as {server}__{tool_name} to avoid collisions
    when multiple MCP servers expose tools with the same name.
    """
    return [_convert_one(server_name, tool) for server_name, tool in tools]


def _convert_one(server_name: str, tool: Tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": f"{server_name}__{tool.name}",
            "description": f"[{server_name}] {tool.description or ''}",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }


def parse_namespaced_tool(namespaced_name: str) -> tuple[str, str]:
    """Parse a namespaced tool name back into (server_name, tool_name)."""
    server_name, _, tool_name = namespaced_name.partition("__")
    if not tool_name:
        raise ValueError(
            f"Invalid namespaced tool name '{namespaced_name}': expected 'server__tool'"
        )
    return server_name, tool_name
