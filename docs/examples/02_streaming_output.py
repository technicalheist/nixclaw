"""
Example 02: Streaming Output — See agent reasoning in real-time.

CLI equivalent:
    nixclaw "Analyze the project structure"

This example uses run_stream() to print agent output as it happens.
"""
import asyncio
from nixclaw import Orchestrator


async def main():
    orchestrator = Orchestrator()

    try:
        # run_stream() prints agent output to the console in real-time
        # via AutoGen's Console helper
        result = await orchestrator.run_stream(
            "Read the pyproject.toml and summarize what this project does"
        )
        print("\n--- Final Result ---")
        print(result)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
