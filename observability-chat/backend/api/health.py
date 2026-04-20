import asyncio

from fastapi import APIRouter, Request

from backend.config import settings

router = APIRouter()


@router.get("/api/health")
async def health(request: Request) -> dict:
    mcp_manager = request.app.state.mcp_manager

    configured = {s.name: s.url for s in settings.mcp_servers}
    connected_names = mcp_manager.get_server_names()

    ping_results = dict(
        zip(
            connected_names,
            await asyncio.gather(
                *(mcp_manager.ping(name) for name in connected_names)
            ),
        )
    )

    servers = {}
    for name, url in configured.items():
        if name not in connected_names:
            status = "disconnected"
        elif ping_results[name]:
            status = "healthy"
        else:
            status = "unhealthy"

        entry = {"status": status, "url": url}
        conn = mcp_manager._connections.get(name)
        if conn:
            entry["tools"] = len(conn.tools)
        servers[name] = entry

    all_healthy = all(s["status"] == "healthy" for s in servers.values())
    model = (
        settings.anthropic_model
        if settings.llm_provider == "anthropic"
        else settings.openai_model
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "llm": {"provider": settings.llm_provider, "model": model},
        "mcp_servers": servers,
    }
