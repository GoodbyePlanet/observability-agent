import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from backend.agent.conversation import ConversationHistory
from backend.agent.system_prompt import SYSTEM_PROMPT
from backend.agent.tool_bridge import (
    mcp_tools_to_openai_functions,
    parse_namespaced_tool,
)
from backend.config import settings
from backend.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


def _sse_event(event: str, data: Any) -> str:
    """Format a server-sent event."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


async def run_agent_loop(
    user_message: str,
    conversation: ConversationHistory,
    mcp_manager: MCPManager,
) -> AsyncGenerator[str, None]:
    """Run the agent loop, yielding SSE events.

    Events emitted:
    - tool_call_start: {name, arguments}  — agent is invoking a tool
    - tool_call_end:   {name, result}     — tool returned a result
    - token:           {content}          — streamed text token
    - done:            {}                 — agent finished
    - error:           {message}          — something went wrong
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    conversation.add_user_message(user_message)

    tools = mcp_tools_to_openai_functions(mcp_manager.get_all_tools())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation.get_messages()

    for iteration in range(settings.max_agent_iterations):
        logger.info("Agent iteration %d", iteration + 1)

        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=tools if tools else None,
                stream=True,
            )
        except Exception as e:
            logger.exception("OpenAI API error")
            yield _sse_event("error", {"message": str(e)})
            return

        # Accumulate the streamed response
        collected_content = ""
        collected_tool_calls: dict[int, dict] = {}

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # Stream text tokens
            if delta.content:
                collected_content += delta.content
                yield _sse_event("token", {"content": delta.content})

            # Accumulate tool calls (they arrive in pieces)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in collected_tool_calls:
                        collected_tool_calls[idx] = {
                            "id": "",
                            "function": {"name": "", "arguments": ""},
                        }
                    entry = collected_tool_calls[idx]
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            entry["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            entry["function"]["arguments"] += tc.function.arguments

        # If the model produced text with no tool calls, we're done
        if collected_content and not collected_tool_calls:
            conversation.add_assistant_message(collected_content)
            yield _sse_event("done", {})
            return

        # If there are tool calls, execute them
        if collected_tool_calls:
            tool_calls_list = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": tc["function"],
                }
                for tc in collected_tool_calls.values()
            ]

            conversation.add_tool_call_message(tool_calls_list)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation.get_messages()

            for tc in tool_calls_list:
                func_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]

                try:
                    arguments = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    arguments = {}

                yield _sse_event(
                    "tool_call_start",
                    {"name": func_name, "arguments": arguments},
                )

                try:
                    server_name, tool_name = parse_namespaced_tool(func_name)
                    result = await mcp_manager.call_tool(
                        server_name, tool_name, arguments
                    )
                    # MCP result content is a list of content blocks
                    result_text = "\n".join(
                        block.text
                        for block in result.content
                        if hasattr(block, "text")
                    )
                except Exception as e:
                    logger.exception("Tool call failed: %s", func_name)
                    result_text = f"Error: {e}"

                yield _sse_event(
                    "tool_call_end",
                    {"name": func_name, "result": result_text[:2000]},
                )

                conversation.add_tool_result(tc["id"], result_text)
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation.get_messages()

            # Continue the loop — OpenAI will see the tool results
            continue

        # Edge case: no content and no tool calls (e.g. refusal)
        conversation.add_assistant_message(collected_content or "")
        yield _sse_event("done", {})
        return

    # Exhausted max iterations
    fallback = "I've reached the maximum number of tool calls. Here's what I have so far."
    conversation.add_assistant_message(fallback)
    yield _sse_event("token", {"content": fallback})
    yield _sse_event("done", {})
