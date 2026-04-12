from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/health")
async def health(request: Request) -> dict:
    mcp_manager = request.app.state.mcp_manager
    servers = mcp_manager.get_server_names()
    return {
        "status": "healthy",
        "mcp_servers": {name: "connected" for name in servers},
    }
