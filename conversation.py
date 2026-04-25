from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    code: Optional[str] = None
    result_summary: Optional[str] = None
    had_error: bool = False


class ConversationManager:
    def __init__(self, max_history: int = 20):
        self.history: List[Message] = []
        self.max_history = max_history

    def add_user(self, content: str) -> None:
        self.history.append(Message(role="user", content=content))

    def add_assistant(
        self,
        content: str,
        code: str = "",
        result_summary: str = "",
        had_error: bool = False,
    ) -> None:
        self.history.append(
            Message(
                role="assistant",
                content=content,
                code=code,
                result_summary=result_summary,
                had_error=had_error,
            )
        )

    def get_claude_messages(self) -> List[dict]:
        """Return last N messages formatted for the Claude API."""
        window = self.history[-self.max_history :]
        return [{"role": m.role, "content": m.content} for m in window]

    def get_context_summary(self) -> str:
        """Return a brief plain-text summary of recent exchanges for prompts."""
        if not self.history:
            return ""
        recent = self.history[-6:]
        lines = []
        for m in recent:
            if m.role == "user":
                lines.append(f"User asked: {m.content}")
            elif m.result_summary:
                lines.append(f"Result: {m.result_summary}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.history.clear()

    def __len__(self) -> int:
        return len(self.history)
