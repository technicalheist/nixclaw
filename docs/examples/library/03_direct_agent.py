"""
Example 03: Direct Agent Control — Create and use agents directly.

Instead of using the Orchestrator, create specific agent types
from the factory and run tasks on them directly.
"""
import asyncio
from nixclaw import AgentFactory


async def main():
    factory = AgentFactory.get_instance()

    # Create a CodeGenerator agent
    agent = await factory.create_agent("CodeGenerator")

    try:
        # Run a coding task
        result = await agent.run(
            "Write a Python function that checks if a string is a palindrome. "
            "Include type hints and a few test cases."
        )
        print("Agent output:")
        print(agent.get_result_text(result))
    finally:
        await factory.cleanup_all()


async def multiple_agents():
    """Create multiple agents for different tasks."""
    factory = AgentFactory.get_instance()

    # Create different specialists
    coder = await factory.create_agent("CodeGenerator")
    analyzer = await factory.create_agent("Analyzer")

    try:
        # Run tasks in parallel
        code_task = coder.run("Write a simple calculator class in Python")
        analysis_task = analyzer.run("What are the best practices for Python error handling?")

        code_result, analysis_result = await asyncio.gather(code_task, analysis_task)

        print("=== Code Generator Output ===")
        print(coder.get_result_text(code_result))
        print("\n=== Analyzer Output ===")
        print(analyzer.get_result_text(analysis_result))
    finally:
        await factory.cleanup_all()


if __name__ == "__main__":
    # Run single agent example
    asyncio.run(main())

    # Or run multiple agents:
    # asyncio.run(multiple_agents())
