from __future__ import annotations

from typing import Any, Callable, Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.ui import Console
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from nixclaw.config import Settings, get_settings
from nixclaw.logger import get_logger
from nixclaw.storage.models import AgentMetadata, AgentStatus

logger = get_logger(__name__)


def create_model_client(settings: Settings | None = None) -> OpenAIChatCompletionClient:
    """Create an OpenAI-compatible model client from configuration."""
    settings = settings or get_settings()
    llm = settings.llm
    return OpenAIChatCompletionClient(
        model=llm.model,
        api_key=llm.api_key,
        base_url=llm.base_url,
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            family="unknown",
            structured_output=True,
        ),
    )


class ManagedAgent:
    """Wraps an AutoGen AssistantAgent with lifecycle tracking and metadata."""

    def __init__(
        self,
        name: str,
        system_message: str,
        tools: Sequence[Callable[..., Any]] | None = None,
        profile: str = "general",
        description: str = "",
        model_client: OpenAIChatCompletionClient | None = None,
    ) -> None:
        settings = get_settings()
        self._client = model_client or create_model_client(settings)

        self.metadata = AgentMetadata(
            profile=profile,
            tools_available=[getattr(t, "__name__", str(t)) for t in (tools or [])],
        )

        self.agent = AssistantAgent(
            name=name,
            model_client=self._client,
            tools=list(tools) if tools else [],
            system_message=system_message,
            description=description or f"{profile} agent",
            reflect_on_tool_use=settings.agent.enable_reflection,
            model_client_stream=settings.agent.streaming_enabled,
        )

        logger.info("Created agent '%s' (profile=%s, id=%s)", name, profile, self.metadata.id)

    @property
    def name(self) -> str:
        return self.agent.name

    async def run(self, task: str) -> TaskResult:
        """Run a task and return the result."""
        self.metadata.status = AgentStatus.BUSY
        logger.info("Agent '%s' starting task: %.100s...", self.name, task)
        try:
            result = await self.agent.run(task=task)
            self.metadata.status = AgentStatus.IDLE
            return result
        except Exception:
            self.metadata.status = AgentStatus.FAILED
            self.metadata.error_count += 1
            raise

    async def run_stream(self, task: str) -> TaskResult:
        """Run a task with streaming console output."""
        self.metadata.status = AgentStatus.BUSY
        logger.info("Agent '%s' starting streamed task: %.100s...", self.name, task)
        try:
            result = await Console(self.agent.run_stream(task=task))
            self.metadata.status = AgentStatus.IDLE
            return result
        except Exception:
            self.metadata.status = AgentStatus.FAILED
            self.metadata.error_count += 1
            raise

    async def close(self) -> None:
        """Clean up resources."""
        self.metadata.status = AgentStatus.TERMINATED
        await self._client.close()
        logger.info("Agent '%s' closed", self.name)

    def get_result_text(self, result: TaskResult) -> str:
        """Extract text from a TaskResult."""
        if result.messages:
            last = result.messages[-1]
            if hasattr(last, "to_text"):
                return last.to_text()
            return str(last)
        return ""
