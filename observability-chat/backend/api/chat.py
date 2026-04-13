from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agent.loop import run_agent_loop

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> StreamingResponse:
    mcp_manager = request.app.state.mcp_manager
    conversation_store = request.app.state.conversation_store
    conversation = conversation_store.get(body.session_id)

    return StreamingResponse(
        run_agent_loop(body.message, conversation, mcp_manager),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
