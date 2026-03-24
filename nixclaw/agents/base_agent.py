from __future__ import annotations

import asyncio
from typing import Any, Callable, Sequence

from nixagent import Agent

from nixclaw.config import Settings, get_settings
from nixclaw.integrations.openai_client import configure_llm
from nixclaw.logger import get_logger
from nixclaw.storage.models import AgentMetadata, AgentStatus

logger = get_logger(__name__)


def create_model_client(settings: Settings | None = None) -> None:
    """Configure the LLM environment for nixagent. Kept for backwards compatibility."""
    configure_llm(settings)
    return None


class ManagedAgent:
    """Wraps a nixagent Agent with lifecycle tracking and metadata."""

    def __init__(
        self,
        name: str,
        system_message: str,
        tools: Sequence[Callable[..., Any]] | None = None,
        profile: str = "general",
        description: str = "",
        model_client: None = None,
    ) -> None:
        settings = get_settings()
        configure_llm(settings)

        self.metadata = AgentMetadata(
            profile=profile,
            tools_available=[getattr(t, "__name__", str(t)) for t in (tools or [])],
        )

        # nixagent's built-in tools cover all file/dir/search/shell operations
        self.agent = Agent(
            name=name,
            system_prompt=system_message,
            provider=settings.llm.provider,
            use_builtin_tools=True,
            verbose=False,
        )

        logger.info("Created agent '%s' (profile=%s, id=%s)", name, profile, self.metadata.id)

    @property
    def name(self) -> str:
        return self.agent.name

    async def run(self, task: str) -> str:
        """Run a task and return the result text."""
        self.metadata.status = AgentStatus.BUSY
        logger.info("Agent '%s' starting task: %.100s...", self.name, task)
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self.agent.run, task)
            self.metadata.status = AgentStatus.IDLE
            return result or ""
        except Exception:
            self.metadata.status = AgentStatus.FAILED
            self.metadata.error_count += 1
            raise

    async def run_stream(self, task: str) -> str:
        """Run a task with streaming and return the collected output."""
        self.metadata.status = AgentStatus.BUSY
        logger.info("Agent '%s' starting streamed task: %.100s...", self.name, task)
        try:
            def _collect() -> str:
                parts: list[str] = []
                for chunk in self.agent.run(task, stream=True):
                    parts.append(chunk)
                return "".join(parts)

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, _collect)
            self.metadata.status = AgentStatus.IDLE
            return result
        except Exception:
            self.metadata.status = AgentStatus.FAILED
            self.metadata.error_count += 1
            raise

    async def close(self) -> None:
        """Clean up resources."""
        self.metadata.status = AgentStatus.TERMINATED
        logger.info("Agent '%s' closed", self.name)

    def get_result_text(self, result: str) -> str:
        """Return result text (kept for API compatibility)."""
        return result or ""
