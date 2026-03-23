from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from nixclaw.agents.base_agent import ManagedAgent, create_model_client
from nixclaw.agents.agent_profiles import get_profile
from nixclaw.config import get_settings
from nixclaw.logger import get_logger
from nixclaw.storage.models import AgentStatus

logger = get_logger(__name__)


class AgentFactory:
    """Creates, tracks, and manages agent instances.

    Implements the Agent Factory pattern: agents are created on-demand
    from profiles, tracked for lifecycle management, and cleaned up
    when no longer needed.
    """

    _instance: AgentFactory | None = None

    def __init__(self) -> None:
        self._agents: dict[str, ManagedAgent] = {}
        self._lock = asyncio.Lock()
        self._counter: int = 0

    @classmethod
    def get_instance(cls) -> AgentFactory:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def _next_name(self, base: str) -> str:
        self._counter += 1
        return f"{base}_{self._counter}"

    async def create_agent(
        self,
        profile_name: str,
        custom_system_message: str | None = None,
    ) -> ManagedAgent:
        """Create a new agent from a profile template."""
        settings = get_settings()

        # Enforce concurrency limit
        active = sum(
            1
            for a in self._agents.values()
            if a.metadata.status in (AgentStatus.IDLE, AgentStatus.BUSY)
        )
        if active >= settings.agent.max_concurrent_agents:
            raise RuntimeError(
                f"Max concurrent agents reached ({settings.agent.max_concurrent_agents}). "
                "Wait for existing agents to complete."
            )

        profile = get_profile(profile_name)
        name = self._next_name(profile.name)
        system_msg = custom_system_message or profile.system_message

        agent = ManagedAgent(
            name=name,
            system_message=system_msg,
            tools=profile.tools,
            profile=profile_name,
            description=profile.description,
        )

        async with self._lock:
            self._agents[agent.metadata.id] = agent

        logger.info(
            "Factory created agent: name=%s profile=%s id=%s (active=%d)",
            name,
            profile_name,
            agent.metadata.id,
            active + 1,
        )
        return agent

    async def create_and_run(
        self,
        profile_name: str,
        task: str,
        context: str = "",
        priority: str = "normal",
    ) -> str:
        """Create a specialist agent, run a task, and return the text result."""
        agent = await self.create_agent(profile_name)

        full_task = task
        if context:
            full_task = f"Context:\n{context}\n\nTask:\n{task}"

        try:
            result = await agent.run(task=full_task)
            text = agent.get_result_text(result)
            logger.info(
                "Agent '%s' completed task (profile=%s): %.100s...",
                agent.name,
                profile_name,
                text,
            )
            return text or "(no output from agent)"
        except Exception as e:
            logger.exception("Agent '%s' failed task: %s", agent.name, e)
            return f"Agent error ({profile_name}): {e}"
        finally:
            await self.release_agent(agent.metadata.id)

    async def get_agent(self, agent_id: str) -> ManagedAgent | None:
        return self._agents.get(agent_id)

    async def release_agent(self, agent_id: str) -> None:
        """Release an agent and clean up resources."""
        async with self._lock:
            agent = self._agents.pop(agent_id, None)
        if agent:
            await agent.close()
            logger.info("Released agent: %s (id=%s)", agent.name, agent_id)

    async def find_idle_agent(self, profile_name: str) -> ManagedAgent | None:
        """Find an existing idle agent matching the profile."""
        for agent in self._agents.values():
            if (
                agent.metadata.profile == profile_name
                and agent.metadata.status == AgentStatus.IDLE
            ):
                return agent
        return None

    async def cleanup_all(self) -> None:
        """Terminate and clean up all agents."""
        async with self._lock:
            agents = list(self._agents.values())
            self._agents.clear()
        for agent in agents:
            await agent.close()
        logger.info("Cleaned up %d agents", len(agents))

    def get_status(self) -> dict:
        """Get a summary of all agent states."""
        summary: dict[str, int] = {}
        for agent in self._agents.values():
            status = agent.metadata.status.value
            summary[status] = summary.get(status, 0) + 1
        return {
            "total": len(self._agents),
            "by_status": summary,
        }
