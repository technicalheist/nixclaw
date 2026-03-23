from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)


class ContextEntry(BaseModel):
    """A single context item with source and content."""

    source: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    token_estimate: int = 0


class ContextManager:
    """Manages shared context across agents with a sliding window and token budget.

    Stores context entries in a deque, pruning oldest entries when the
    token budget is exceeded.
    """

    def __init__(self, max_tokens: int = 0) -> None:
        settings = get_settings()
        self._max_tokens = max_tokens or settings.agent.memory_context_limit
        self._entries: deque[ContextEntry] = deque()
        self._total_tokens = 0

    def add(self, source: str, content: str) -> None:
        """Add a context entry, pruning old entries if budget is exceeded."""
        # Rough estimate: ~4 chars per token
        token_est = len(content) // 4
        entry = ContextEntry(source=source, content=content, token_estimate=token_est)

        self._entries.append(entry)
        self._total_tokens += token_est

        # Prune oldest entries to stay within budget
        while self._total_tokens > self._max_tokens and self._entries:
            removed = self._entries.popleft()
            self._total_tokens -= removed.token_estimate
            logger.debug("Pruned context entry from %s (%d tokens)", removed.source, removed.token_estimate)

    def get_context(self, max_entries: int = 0) -> str:
        """Get formatted context string, optionally limited to last N entries."""
        entries = list(self._entries)
        if max_entries > 0:
            entries = entries[-max_entries:]

        if not entries:
            return ""

        parts = []
        for e in entries:
            parts.append(f"[{e.source}] {e.content}")
        return "\n\n".join(parts)

    def get_context_for_agent(self, agent_name: str, max_entries: int = 10) -> str:
        """Get context relevant to a specific agent (entries from other sources)."""
        entries = [e for e in self._entries if e.source != agent_name]
        if max_entries > 0:
            entries = entries[-max_entries:]
        if not entries:
            return ""
        return "\n\n".join(f"[{e.source}] {e.content}" for e in entries)

    def clear(self) -> None:
        self._entries.clear()
        self._total_tokens = 0

    @property
    def token_usage(self) -> int:
        return self._total_tokens

    @property
    def entry_count(self) -> int:
        return len(self._entries)
