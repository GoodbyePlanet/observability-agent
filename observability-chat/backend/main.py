import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.conversation import ConversationStore
from backend.api.chat import router as chat_router
from backend.api.health import router as health_router
from backend.api.mcp_routes import router as mcp_router
from backend.config import settings
from backend.mcp.manager import MCPManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_manager = MCPManager()
    try:
        await mcp_manager.connect_all(settings.mcp_servers)
        app.state.mcp_manager = mcp_manager
        app.state.conversation_store = ConversationStore()
        logger.info("Observability Chat backend started")
        yield
    finally:
        await mcp_manager.close()
        logger.info("Observability Chat backend stopped")


app = FastAPI(title="Observability Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(mcp_router)
app.include_router(chat_router)
