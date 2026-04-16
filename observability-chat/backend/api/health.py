from fastapi import APIRouter, Request

from backend.config import settings

router = APIRouter()


@router.get("/api/health")
async def health(request: Request) -> dict:
    mcp_manager = request.app.state.mcp_manager
    servers = mcp_manager.get_server_names()
    model = (
        settings.anthropic_model
        if settings.llm_provider == "anthropic"
        else settings.openai_model
    )
    return {
        "status": "healthy",
        "mcp_servers": {name: "connected" for name in servers},
        "model": model,
    }
