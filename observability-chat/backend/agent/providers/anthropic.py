import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from anthropic import AsyncAnthropic

from backend.agent.conversation import ConversationHistory, Message
from backend.agent.system_prompt import SYSTEM_PROMPT
from backend.agent.tool_bridge import (
    mcp_tools_to_anthropic_tools,
    parse_namespaced_tool,
)
from backend.config import settings
from backend.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


def _sse_event(event: str, data: Any) -> str:
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


def _to_anthropic_messages(messages: list[Message]) -> list[dict]:
    """Convert generic conversation messages to Anthropic API format.

    Anthropic requires:
    - System prompt passed separately (not as a message)
    - Tool use blocks inside assistant content arrays
    - Tool results inside user messages as tool_result content blocks
    - Strict user/assistant alternation
    """
    result: list[dict] = []

    for msg in messages:
        role = msg["role"]

        if role == "user":
            result.append({"role": "user", "content": msg["content"]})

        elif role == "assistant":
            if "tool_calls" in msg:
                content_blocks: list[dict] = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    func = tc["function"]
                    try:
                        tool_input = (
                            json.loads(func["arguments"])
                            if isinstance(func["arguments"], str)
                            else func["arguments"]
                        )
                    except json.JSONDecodeError:
                        tool_input = {}
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": func["name"],
                            "input": tool_input,
                        }
                    )
                result.append({"role": "assistant", "content": content_blocks})
            else:
                result.append(
                    {"role": "assistant", "content": msg.get("content", "")}
                )

        elif role == "tool":
            # Anthropic expects tool results inside user messages.
            # Group consecutive tool results into one user message.
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": msg["tool_call_id"],
                "content": msg["content"],
            }
            if (
                result
                and result[-1]["role"] == "user"
                and isinstance(result[-1]["content"], list)
            ):
                result[-1]["content"].append(tool_result_block)
            else:
                result.append({"role": "user", "content": [tool_result_block]})

    return result


async def run_anthropic_loop(
    user_message: str,
    conversation: ConversationHistory,
    mcp_manager: MCPManager,
) -> AsyncGenerator[str, None]:
    """Run the agent loop using Anthropic, yielding SSE events."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)

    conversation.add_user_message(user_message)

    tools = mcp_tools_to_anthropic_tools(mcp_manager.get_all_tools())

    for iteration in range(settings.max_agent_iterations):
        logger.info("Agent iteration %d (Anthropic)", iteration + 1)

        messages = _to_anthropic_messages(conversation.get_messages())

        create_kwargs: dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }
        if tools:
            create_kwargs["tools"] = tools

        try:
            async with client.messages.stream(**create_kwargs) as stream:
                async for event in stream:
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        yield _sse_event("token", {"content": event.delta.text})

                response = await stream.get_final_message()
        except Exception as e:
            logger.exception("Anthropic API error")
            yield _sse_event("error", {"message": str(e)})
            return

        # Separate text and tool_use blocks from the response
        collected_content = ""
        tool_use_blocks = []
        for block in response.content:
            if block.type == "text":
                collected_content += block.text
            elif block.type == "tool_use":
                tool_use_blocks.append(block)

        # No tool calls — we're done
        if not tool_use_blocks:
            conversation.add_assistant_message(collected_content)
            yield _sse_event("done", {})
            return

        # Store assistant message with tool calls (in generic format)
        tool_calls_list = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.input),
                },
            }
            for tc in tool_use_blocks
        ]
        conversation.add_tool_call_message(tool_calls_list, content=collected_content)

        # Execute each tool call
        for tc in tool_use_blocks:
            func_name = tc.name
            arguments = tc.input

            yield _sse_event(
                "tool_call_start",
                {"name": func_name, "arguments": arguments},
            )

            try:
                server_name, tool_name = parse_namespaced_tool(func_name)
                result = await mcp_manager.call_tool(
                    server_name, tool_name, arguments
                )
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

            conversation.add_tool_result(tc.id, result_text)

        continue

    fallback = "I've reached the maximum number of tool calls. Here's what I have so far."
    conversation.add_assistant_message(fallback)
    yield _sse_event("token", {"content": fallback})
    yield _sse_event("done", {})
