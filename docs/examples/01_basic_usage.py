"""
Example 01: Basic Usage — One-shot task via CLI and library.

CLI equivalent:
    nixclaw "List all Python files in the current directory"

This example shows how to run a single task programmatically.
"""
import asyncio
from nixclaw import Orchestrator


async def main():
    # Create the orchestrator (reads config from .env automatically)
    orchestrator = Orchestrator()

    try:
        # Run a simple task — the orchestrator will use its tools directly
        result = await orchestrator.run(
            "List all Python files in the current directory and count them"
        )
        print("Result:")
        print(result)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
