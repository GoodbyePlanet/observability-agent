from dataclasses import dataclass, field
from typing import Any

Message = dict[str, Any]


@dataclass
class ConversationHistory:
    """In-memory conversation history for a single session."""

    messages: list[Message] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_call_message(self, tool_calls: list[dict], content: str = "") -> None:
        msg: Message = {"role": "assistant", "tool_calls": tool_calls}
        if content:
            msg["content"] = content
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self.messages.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )

    def get_messages(self) -> list[Message]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()


class ConversationStore:
    """Manages multiple conversation sessions (keyed by session ID)."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationHistory] = {}

    def get(self, session_id: str) -> ConversationHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationHistory()
        return self._sessions[session_id]

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
