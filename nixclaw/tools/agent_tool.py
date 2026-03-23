from __future__ import annotations

from nixclaw.logger import get_logger

logger = get_logger(__name__)


async def delegate_to_agent(
    agent_profile: str,
    task: str,
    context: str = "",
    priority: str = "normal",
) -> str:
    """Delegate a subtask to a specialized agent.

    Args:
        agent_profile: Agent specialization (e.g. 'CodeGenerator', 'Analyzer', 'Researcher').
        task: Description of the task to delegate.
        context: Relevant context for the task.
        priority: Priority level - 'high', 'normal', or 'low'.

    Returns:
        Result from the delegated agent.
    """
    # Import here to avoid circular imports
    from nixclaw.agents.agent_factory import AgentFactory

    factory = AgentFactory.get_instance()
    result = await factory.create_and_run(
        profile_name=agent_profile,
        task=task,
        context=context,
        priority=priority,
    )
    return result
