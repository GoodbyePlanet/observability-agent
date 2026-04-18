from __future__ import annotations

import argparse
import logging

from mcp.server.fastmcp import FastMCP

from server.config import settings
from server.store.qdrant import QdrantStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "code-search",
    description="Semantic code search across microservices codebases. "
    "Supports Java, Python, and TypeScript/React.",
)

_store: QdrantStore | None = None


def get_store() -> QdrantStore:
    if _store is None:
        raise RuntimeError("Store not initialized")
    return _store


def register_tools() -> None:
    from server.tools.search import register_search_tools
    from server.tools.index import register_index_tools
    from server.tools.admin import register_admin_tools

    register_search_tools(mcp)
    register_index_tools(mcp)
    register_admin_tools(mcp)


async def startup() -> None:
    global _store
    logger.info("Starting code-search MCP server...")
    _store = QdrantStore()
    await _store.ensure_collection()
    logger.info("Qdrant collection ready.")

    logger.info("Ready. Use the `reindex` MCP tool to index services.")


async def shutdown() -> None:
    if _store:
        await _store.close()
    logger.info("code-search MCP server stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Search MCP Server")
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse", "stdio"],
        default=settings.mcp_transport,
    )
    args = parser.parse_args()

    register_tools()

    if args.transport == "stdio":
        async def run_stdio():
            await startup()
            try:
                await mcp.run_stdio_async()
            finally:
                await shutdown()

        asyncio.run(run_stdio())
    else:
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount

        async def lifespan(app):
            await startup()
            yield
            await shutdown()

        transport = "streamable-http" if args.transport == "streamable-http" else "sse"
        app = mcp.get_asgi_app()

        # Wrap in Starlette for lifespan support
        starlette_app = Starlette(
            lifespan=lifespan,
            routes=[Mount("/", app=app)],
        )

        uvicorn.run(
            starlette_app,
            host=settings.mcp_host,
            port=settings.mcp_port,
            log_level="info",
        )


if __name__ == "__main__":
    main()
