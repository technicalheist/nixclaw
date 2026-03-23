"""
Example 05: Custom Tools — Register your own tools with agents.

NixClaw agents can use any Python function as a tool. Just define
an async function with type hints and pass it to the agent.
"""
import asyncio
import json
from datetime import datetime

from nixclaw.agents.base_agent import ManagedAgent, create_model_client


# Define custom tools as async functions with type hints and docstrings.
# The docstring becomes the tool description for the LLM.

async def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A math expression like '2 + 3 * 4' or 'sqrt(16)'.
    """
    import math
    # Only allow safe math operations
    allowed = {
        k: v for k, v in math.__dict__.items()
        if not k.startswith("_")
    }
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})

    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


async def lookup_data(key: str) -> str:
    """Look up data from our internal database.

    Args:
        key: The data key to look up (e.g. 'server_count', 'uptime', 'version').
    """
    # Simulated database
    data = {
        "server_count": "42 servers across 3 regions",
        "uptime": "99.97% over the last 30 days",
        "version": "NixClaw v0.1.0",
        "team_size": "5 engineers",
    }
    return data.get(key, f"No data found for key: {key}")


async def main():
    # Create an agent with custom tools
    agent = ManagedAgent(
        name="custom_agent",
        system_message=(
            "You are a helpful assistant with access to custom tools. "
            "Use them to answer questions accurately."
        ),
        tools=[get_current_time, calculate, lookup_data],
        profile="custom",
        description="Agent with custom tools",
    )

    try:
        result = await agent.run(
            "What time is it? Also, what's the square root of 144? "
            "And how many servers do we have?"
        )
        print(agent.get_result_text(result))
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
