"""
Example 04: Team Mode — Multiple agents collaborating via SelectorGroupChat.

CLI equivalent:
    nixclaw --team CodeGenerator,Analyzer,Debugger "Build and review a REST API"

The orchestrator creates a team of specialists. An LLM selects which
agent speaks next based on the conversation context.
"""
import asyncio
from nixclaw import Orchestrator


async def main():
    orchestrator = Orchestrator()

    try:
        # Create a team with specific agent profiles
        # The LLM will decide which agent speaks at each step
        result = await orchestrator.run_with_team(
            task_description=(
                "Create a Python function that reads a CSV file and returns "
                "statistics (mean, median, mode) for each numeric column. "
                "Then review the code for potential issues and suggest improvements."
            ),
            agent_profiles=["CodeGenerator", "Analyzer"],
        )
        print("Team result:")
        print(result)
    finally:
        await orchestrator.close()


async def three_agent_team():
    """Use three agents: coder writes, analyzer reviews, debugger fixes."""
    orchestrator = Orchestrator()

    try:
        result = await orchestrator.run_with_team(
            task_description=(
                "Write a Python script that monitors disk usage and sends "
                "an alert if any partition exceeds 80% capacity. "
                "Review it for edge cases and fix any issues found."
            ),
            agent_profiles=["CodeGenerator", "Analyzer", "Debugger"],
        )
        print(result)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
