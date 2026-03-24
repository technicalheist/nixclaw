from __future__ import annotations

import asyncio
from typing import Any

from nixagent import Agent

from nixclaw.agents.base_agent import ManagedAgent, create_model_client
from nixclaw.agents.agent_factory import AgentFactory
from nixclaw.agents.agent_profiles import ALL_TOOLS, get_profile, list_profiles
from nixclaw.config import get_settings
from nixclaw.core.task_manager import TaskManager
from nixclaw.integrations.openai_client import configure_llm
from nixclaw.integrations.telegram_log import get_log_bot
from nixclaw.logger import get_logger
from nixclaw.storage.models import Task, TaskStatus, TaskType

logger = get_logger(__name__)

ORCHESTRATOR_SYSTEM_MESSAGE = """You are the Orchestrator Agent — the primary task coordinator of a multi-agent AI system.

You HAVE the following tools available to you (use them via function calling):

**Delegation tool:**
- `delegate_to_agent(agent_profile, task, context, priority)` — Delegate a subtask to a specialist agent. You MUST use this tool to delegate. Do NOT say you don't have it — it is registered and available.

**File tools:**
- `read_file(filepath)` — Read file contents
- `write_file(filepath, content)` — Write/create files
- `delete_file(filepath)` — Delete a file

**Directory tools:**
- `list_files(directory, recursive)` — List directory contents
- `list_files_by_pattern(directory, pattern, recursive)` — Find files by pattern

**Search tools:**
- `search_file_contents(directory, pattern)` — Search inside files

**Shell tool:**
- `execute_shell_command(command)` — Execute shell commands safely

Available specialist agent profiles for delegation:
{profiles}

Your workflow:
1. Analyze the task complexity
2. For simple tasks: use your tools directly (file ops, shell, search)
3. For complex tasks: delegate to specialists using `delegate_to_agent`
4. Aggregate results and provide a clear response
5. Say "TASK_COMPLETE" when done

IMPORTANT: Never claim you don't have a tool. All tools listed above are available to you via function calling.
"""

# OpenAI-style tool definition for the delegation tool
_DELEGATE_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "delegate_to_agent",
        "description": (
            "Delegate a subtask to a specialist agent. "
            "Use this to break down complex tasks into specialised work."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_profile": {
                    "type": "string",
                    "description": (
                        "Agent specialization, e.g. 'CodeGenerator', 'Analyzer', "
                        "'Researcher', 'SystemAdmin', 'Debugger'."
                    ),
                },
                "task": {
                    "type": "string",
                    "description": "Description of the task to delegate.",
                },
                "context": {
                    "type": "string",
                    "description": "Relevant context for the task.",
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level: 'high', 'normal', or 'low'.",
                    "enum": ["high", "normal", "low"],
                },
            },
            "required": ["agent_profile", "task"],
        },
    },
}


def _delegate_to_agent_sync(
    agent_profile: str,
    task: str,
    context: str = "",
    priority: str = "normal",
) -> str:
    """Synchronous delegation wrapper for use inside nixagent's tool loop.

    nixagent calls tools synchronously; this function creates a fresh event loop
    so that the async AgentFactory can still be used correctly from a thread.
    """
    from nixclaw.agents.agent_factory import AgentFactory

    factory = AgentFactory.get_instance()
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            factory.create_and_run(
                profile_name=agent_profile,
                task=task,
                context=context,
                priority=priority,
            )
        )
    finally:
        loop.close()


class Orchestrator:
    """Main orchestrator that breaks down tasks, delegates to specialists, and aggregates results.

    Uses nixagent's Agent with tool-based delegation to specialist agents
    created on-demand via AgentFactory.

    All task lifecycle events are mirrored to the Telegram log bot (if configured).
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        configure_llm(self._settings)
        self._factory = AgentFactory.get_instance()
        self._task_manager = TaskManager()
        self._log_bot = get_log_bot()

        profiles_desc = "\n".join(
            f"- **{name}**: {get_profile(name).description}" for name in list_profiles()
        )

        self._agent = Agent(
            name="orchestrator",
            system_prompt=ORCHESTRATOR_SYSTEM_MESSAGE.format(profiles=profiles_desc),
            provider=self._settings.llm.provider,
            custom_tools={"delegate_to_agent": _delegate_to_agent_sync},
            custom_tool_defs=[_DELEGATE_TOOL_DEF],
            use_builtin_tools=True,
            verbose=False,
        )

        logger.info("Orchestrator initialized with %d profiles", len(list_profiles()))

    async def run(self, task_description: str) -> str:
        """Execute a task: analyze, break down, delegate, and return results."""
        root_task = self._task_manager.create_task(
            title=task_description[:100],
            description=task_description,
            type=TaskType.GENERAL,
        )
        self._task_manager.update_status(root_task.id, TaskStatus.IN_PROGRESS)

        logger.info("Orchestrator processing task: %s (id=%s)", root_task.title, root_task.id)
        self._log_bot.task_started(root_task.id, root_task.title)

        try:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, self._agent.run, task_description)
            text = text or "(no output)"

            self._task_manager.update_status(root_task.id, TaskStatus.COMPLETED)
            root_task.result = text
            logger.info("Task completed: %s", root_task.id)

            self._log_bot.task_completed(root_task.id, root_task.title, text)
            return text

        except Exception as e:
            self._task_manager.update_status(root_task.id, TaskStatus.FAILED)
            root_task.error = str(e)
            logger.exception("Task failed: %s", root_task.id)

            self._log_bot.task_failed(root_task.id, root_task.title, str(e))
            raise

    async def run_stream(self, task_description: str) -> str:
        """Execute a task with streaming output collection."""
        root_task = self._task_manager.create_task(
            title=task_description[:100],
            description=task_description,
            type=TaskType.GENERAL,
        )
        self._task_manager.update_status(root_task.id, TaskStatus.IN_PROGRESS)

        logger.info("Orchestrator processing task (stream): %s", root_task.title)
        self._log_bot.task_started(root_task.id, root_task.title)

        try:
            def _collect_stream() -> str:
                parts: list[str] = []
                for chunk in self._agent.run(task_description, stream=True):
                    parts.append(chunk)
                return "".join(parts)

            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, _collect_stream)
            text = text or "(no output)"

            self._task_manager.update_status(root_task.id, TaskStatus.COMPLETED)
            root_task.result = text

            self._log_bot.task_completed(root_task.id, root_task.title, text)
            return text

        except Exception as e:
            self._task_manager.update_status(root_task.id, TaskStatus.FAILED)
            root_task.error = str(e)

            self._log_bot.task_failed(root_task.id, root_task.title, str(e))
            raise

    async def run_with_team(self, task_description: str, agent_profiles: list[str]) -> str:
        """Run a task using a team of specialist agents as registered collaborators."""
        configure_llm(self._settings)

        profiles_desc = "\n".join(
            f"- **{name}**: {get_profile(name).description}" for name in list_profiles()
        )

        # Fresh agent per team run to avoid cross-run message contamination
        team_agent = Agent(
            name="orchestrator",
            system_prompt=ORCHESTRATOR_SYSTEM_MESSAGE.format(profiles=profiles_desc),
            provider=self._settings.llm.provider,
            custom_tools={"delegate_to_agent": _delegate_to_agent_sync},
            custom_tool_defs=[_DELEGATE_TOOL_DEF],
            use_builtin_tools=True,
            verbose=False,
        )

        created_agents: list[ManagedAgent] = []
        for profile_name in agent_profiles:
            managed = await self._factory.create_agent(profile_name)
            team_agent.register_collaborator(managed.agent, max_iterations=15)
            created_agents.append(managed)
            self._log_bot.agent_event(managed.name, f"Created ({profile_name})")

        collaborator_names = list(team_agent.agents_in_network.keys())
        logger.info(
            "Running team task with %d specialist agents: %s",
            len(collaborator_names),
            collaborator_names,
        )
        self._log_bot.log("TEAM", f"Started with agents: {', '.join(collaborator_names)}")

        try:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, team_agent.run, task_description)
            text = text or "(no output)"

            self._log_bot.log("TEAM", f"Completed: {text[:500]}")
            return text
        except Exception as e:
            self._log_bot.log("TEAM", f"Failed: {e}")
            raise
        finally:
            for managed in created_agents:
                await self._factory.release_agent(managed.metadata.id)

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get current status of a task."""
        task = self._task_manager.get_task(task_id)
        if task:
            return task.model_dump()
        return None

    async def close(self) -> None:
        """Clean up orchestrator resources."""
        await self._factory.cleanup_all()
        logger.info("Orchestrator shut down")

