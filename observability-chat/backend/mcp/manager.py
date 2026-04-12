import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Tool

from backend.config import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPConnection:
    """A single connection to an MCP server."""

    def __init__(self, name: str, session: ClientSession, tools: list[Tool]):
        self.name = name
        self.session = session
        self.tools = tools


class MCPManager:
    """Manages connections to multiple MCP servers."""

    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._connections: dict[str, MCPConnection] = {}

    async def connect(self, server: MCPServerConfig) -> None:
        """Connect to a single MCP server and discover its tools."""
        logger.info("Connecting to MCP server '%s' at %s", server.name, server.url)
        try:
            read_stream, write_stream, _ = await self._exit_stack.enter_async_context(
                streamable_http_client(server.url)
            )
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

            result = await session.list_tools()
            self._connections[server.name] = MCPConnection(
                name=server.name, session=session, tools=result.tools
            )
            tool_names = [t.name for t in result.tools]
            logger.info(
                "Connected to '%s': discovered %d tools: %s",
                server.name,
                len(result.tools),
                tool_names,
            )
        except Exception:
            logger.exception("Failed to connect to MCP server '%s'", server.name)
            raise

    async def connect_all(self, servers: list[MCPServerConfig]) -> None:
        """Connect to all configured MCP servers."""
        for server in servers:
            await self.connect(server)

    async def close(self) -> None:
        """Close all MCP connections."""
        logger.info("Closing all MCP connections")
        await self._exit_stack.aclose()
        self._connections.clear()

    def get_all_tools(self) -> list[tuple[str, Tool]]:
        """Return all tools from all servers as (server_name, tool) tuples."""
        tools: list[tuple[str, Tool]] = []
        for conn in self._connections.values():
            for tool in conn.tools:
                tools.append((conn.name, tool))
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Call a tool on a specific MCP server."""
        conn = self._connections.get(server_name)
        if conn is None:
            raise ValueError(f"No connection to MCP server '{server_name}'")
        return await conn.session.call_tool(tool_name, arguments)

    def get_server_names(self) -> list[str]:
        """Return names of all connected servers."""
        return list(self._connections.keys())

    def is_connected(self, server_name: str) -> bool:
        """Check if a specific server is connected."""
        return server_name in self._connections
