"""NixClaw - Multi-Agent AI System built on AutoGen.

Usage as a library:
    from nixclaw import Orchestrator, AgentFactory, ManagedAgent

    orchestrator = Orchestrator()
    result = await orchestrator.run("Your task here")

Usage as CLI:
    nixclaw "Your task here"
    nixclaw --interactive
    python -m nixclaw "Your task here"
"""

__version__ = "0.2.2"

from nixclaw.agents.orchestrator import Orchestrator
from nixclaw.agents.agent_factory import AgentFactory
from nixclaw.agents.base_agent import ManagedAgent, create_model_client
from nixclaw.agents.agent_profiles import get_profile, list_profiles
from nixclaw.core.task_manager import TaskManager
from nixclaw.core.context_manager import ContextManager
from nixclaw.core.event_bus import EventBus
from nixclaw.core.async_task_queue import AsyncTaskQueue, get_task_queue
from nixclaw.config import get_settings

__all__ = [
    "Orchestrator",
    "AgentFactory",
    "ManagedAgent",
    "create_model_client",
    "get_profile",
    "list_profiles",
    "TaskManager",
    "ContextManager",
    "EventBus",
    "AsyncTaskQueue",
    "get_task_queue",
    "get_settings",
]
