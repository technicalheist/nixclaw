from __future__ import annotations

import json
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console

from nixclaw.agents.base_agent import ManagedAgent, create_model_client
from nixclaw.agents.agent_factory import AgentFactory
from nixclaw.agents.agent_profiles import ALL_TOOLS, get_profile, list_profiles
from nixclaw.config import get_settings
from nixclaw.core.task_manager import TaskManager
from nixclaw.integrations.telegram_log import get_log_bot
from nixclaw.logger import get_logger
from nixclaw.storage.models import Task, TaskStatus, TaskType
from nixclaw.tools.agent_tool import delegate_to_agent

logger = get_logger(__name__)

ORCHESTRATOR_SYSTEM_MESSAGE = """You are the Orchestrator Agent — the primary task coordinator of a multi-agent AI system.

You HAVE the following tools available to you (use them via function calling):

**Delegation tool:**
- `delegate_to_agent(agent_profile, task, context, priority)` — Delegate a subtask to a specialist agent. You MUST use this tool to delegate. Do NOT say you don't have it — it is registered and available.

**File tools:**
- `read_file(file_path, start_line, end_line)` — Read file contents
- `write_file(file_path, content, append)` — Write/create files
- `delete_file(file_path)` — Delete a file

**Directory tools:**
- `list_dir(directory, recursive, file_type)` — List directory contents
- `create_dir(directory)` — Create directories

**Search tools:**
- `search_files(directory, pattern, recursive, max_results)` — Find files by pattern
- `search_content(directory, query, file_pattern, case_sensitive)` — Search inside files

**Shell tool:**
- `execute_shell_command(command, working_dir, timeout, env_vars)` — Execute shell commands safely

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


class Orchestrator:
    """Main orchestrator that breaks down tasks, delegates to specialists, and aggregates results.

    Uses AutoGen's AssistantAgent with tool-based delegation to specialist agents
    created on-demand via AgentFactory.

    All task lifecycle events are mirrored to the Telegram log bot (if configured).
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = create_model_client(self._settings)
        self._factory = AgentFactory.get_instance()
        self._task_manager = TaskManager()
        self._log_bot = get_log_bot()

        profiles_desc = "\n".join(
            f"- **{name}**: {get_profile(name).description}" for name in list_profiles()
        )

        self._agent = AssistantAgent(
            name="orchestrator",
            model_client=self._client,
            tools=[delegate_to_agent, *ALL_TOOLS],
            system_message=ORCHESTRATOR_SYSTEM_MESSAGE.format(profiles=profiles_desc),
            description="Primary task coordinator that breaks down and delegates complex tasks",
            reflect_on_tool_use=self._settings.agent.enable_reflection,
            model_client_stream=self._settings.agent.streaming_enabled,
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
            result = await self._agent.run(task=task_description)
            text = self._extract_result(result)

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
        """Execute a task with streaming console output."""
        root_task = self._task_manager.create_task(
            title=task_description[:100],
            description=task_description,
            type=TaskType.GENERAL,
        )
        self._task_manager.update_status(root_task.id, TaskStatus.IN_PROGRESS)

        logger.info("Orchestrator processing task (stream): %s", root_task.title)
        self._log_bot.task_started(root_task.id, root_task.title)

        try:
            result = await Console(self._agent.run_stream(task=task_description))
            text = self._extract_result(result)
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
        """Run a task using a SelectorGroupChat team with specified agent profiles."""
        agents = [self._agent]

        created_agents: list[ManagedAgent] = []
        for profile_name in agent_profiles:
            managed = await self._factory.create_agent(profile_name)
            agents.append(managed.agent)
            created_agents.append(managed)

            self._log_bot.agent_event(managed.name, f"Created ({profile_name})")

        termination = MaxMessageTermination(
            max_messages=self._settings.system.max_run_iterations
        ) | TextMentionTermination(text="TASK_COMPLETE")

        team = SelectorGroupChat(
            participants=agents,
            model_client=self._client,
            termination_condition=termination,
        )

        agent_names = [a.name for a in agents]
        logger.info("Running team task with %d agents: %s", len(agents), agent_names)
        self._log_bot.log("TEAM", f"Started with agents: {', '.join(agent_names)}")

        try:
            result = await Console(team.run_stream(task=task_description))
            text = self._extract_result(result)

            self._log_bot.log("TEAM", f"Completed: {text[:500]}")
            return text
        except Exception as e:
            self._log_bot.log("TEAM", f"Failed: {e}")
            raise
        finally:
            for managed in created_agents:
                await self._factory.release_agent(managed.metadata.id)

    def _extract_result(self, result: TaskResult) -> str:
        if result.messages:
            last = result.messages[-1]
            if hasattr(last, "to_text"):
                return last.to_text()
            return str(last)
        return "(no output)"

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get current status of a task."""
        task = self._task_manager.get_task(task_id)
        if task:
            return task.model_dump()
        return None

    async def close(self) -> None:
        """Clean up orchestrator resources."""
        await self._client.close()
        await self._factory.cleanup_all()
        logger.info("Orchestrator shut down")
