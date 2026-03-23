"""NixClaw - Multi-Agent AI System Entry Point

Usage as CLI:
    nixclaw "Your task description here"
    nixclaw --interactive
    nixclaw --verbose "Task with full debug output"
    nixclaw --team CodeGenerator,Analyzer "Complex task description"
    nixclaw --serve                          # Start REST API server
    nixclaw --telegram                       # Start Telegram bot
    python -m nixclaw "Your task description here"

Usage as library:
    from nixclaw import Orchestrator
    orchestrator = Orchestrator()
    result = await orchestrator.run("Your task")
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from nixclaw.config import get_settings
from nixclaw.logger import get_logger, setup_logging, is_verbose

logger = get_logger(__name__)


async def run_task(task: str, team_profiles: list[str] | None = None, stream: bool = True) -> str:
    """Run a single task through the orchestrator."""
    from nixclaw.agents.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    try:
        if team_profiles:
            result = await orchestrator.run_with_team(task, team_profiles)
        elif stream and is_verbose():
            result = await orchestrator.run_stream(task)
        else:
            # Non-verbose: use run() which doesn't print AutoGen internals
            result = await orchestrator.run(task)
        return result
    finally:
        await orchestrator.close()


async def interactive_mode() -> None:
    """Run in interactive mode - accepts tasks from stdin."""
    from nixclaw.agents.orchestrator import Orchestrator

    print("NixClaw - Multi-Agent AI System")
    print("=" * 40)
    verbose = is_verbose()
    if verbose:
        print("Verbose mode ON")
    print("Type your task and press Enter. Type 'quit' to exit.\n")

    orchestrator = Orchestrator()
    try:
        while True:
            try:
                task = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nShutting down...")
                break

            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                print("Shutting down...")
                break

            try:
                if verbose:
                    result = await orchestrator.run_stream(task)
                else:
                    result = await orchestrator.run(task)
                print(f"\n{result}\n")
            except Exception as e:
                logger.exception("Task failed")
                print(f"\nError: {e}\n")
    finally:
        await orchestrator.close()


def serve_api(host: str = "", port: int = 0) -> None:
    """Start the FastAPI REST API server."""
    import uvicorn
    from nixclaw.api.app import app

    settings = get_settings()
    host = host or settings.system.api_host
    port = port or settings.system.api_port

    logger.info("Starting NixClaw API on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


def run_telegram_bot() -> None:
    """Start the Telegram bot in polling mode."""
    from nixclaw.integrations.telegram_bot import create_bot_application

    app = create_bot_application()
    if app is None:
        print("Error: Telegram bot not configured. Set TELEGRAM_BOT_TOKEN in .env")
        sys.exit(1)

    logger.info("Starting NixClaw Telegram bot")
    print("NixClaw Telegram bot running. Press Ctrl+C to stop.")
    app.run_polling()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NixClaw - Multi-Agent AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  nixclaw 'Analyze the project structure'\n"
            "  nixclaw --interactive\n"
            "  nixclaw --verbose 'Task with debug output'\n"
            "  nixclaw --team CodeGenerator,Analyzer 'Build a REST API'\n"
            "  nixclaw --serve\n"
            "  nixclaw --telegram\n"
        ),
    )
    parser.add_argument("task", nargs="?", help="Task description to execute")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed agent output, tool calls, and debug logs",
    )
    parser.add_argument(
        "--team", "-t",
        type=str,
        default="",
        help="Comma-separated agent profiles for team execution (e.g. CodeGenerator,Analyzer)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start REST API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="API server port (default: from config)",
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Start Telegram bot in polling mode",
    )

    args = parser.parse_args()

    # Initialize logging with verbose flag
    setup_logging(verbose=args.verbose)

    if args.serve:
        serve_api(port=args.port)
    elif args.telegram:
        run_telegram_bot()
    elif args.interactive:
        asyncio.run(interactive_mode())
    elif args.task:
        team_profiles = [p.strip() for p in args.team.split(",") if p.strip()] if args.team else None
        result = asyncio.run(run_task(args.task, team_profiles, stream=not args.no_stream))
        print(result)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
