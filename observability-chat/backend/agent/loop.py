import logging
from collections.abc import AsyncGenerator

from backend.agent.conversation import ConversationHistory
from backend.config import settings
from backend.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


async def run_agent_loop(
    user_message: str,
    conversation: ConversationHistory,
    mcp_manager: MCPManager,
) -> AsyncGenerator[str, None]:
    """Run the agent loop, yielding SSE events.

    Dispatches to the configured LLM provider.

    Events emitted:
    - tool_call_start: {name, arguments}  — agent is invoking a tool
    - tool_call_end:   {name, result}     — tool returned a result
    - token:           {content}          — streamed text token
    - done:            {}                 — agent finished
    - error:           {message}          — something went wrong
    """
    model = settings.anthropic_model if settings.llm_provider == "anthropic" else settings.openai_model
    logger.info("LLM provider: %s, model: %s", settings.llm_provider, model)

    if settings.llm_provider == "anthropic":
        from backend.agent.providers.anthropic import run_anthropic_loop

        async for event in run_anthropic_loop(user_message, conversation, mcp_manager):
            yield event
    else:
        from backend.agent.providers.openai import run_openai_loop

        async for event in run_openai_loop(user_message, conversation, mcp_manager):
            yield event
