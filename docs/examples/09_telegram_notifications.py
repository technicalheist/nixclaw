"""
Example 09: Telegram Notifications — Send updates from your code.

This example shows how to use both Telegram bots:
- Primary bot: for user-facing notifications
- Log bot: for detailed logging/debugging

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_USER_IDS in .env.
Optionally TELEGRAM_BOT_TOKEN_LOG for the log bot.
"""
import asyncio

from nixclaw.integrations.telegram_bot import get_notifier
from nixclaw.integrations.telegram_log import get_log_bot


async def primary_bot_example():
    """Send notifications via the primary Telegram bot."""
    notifier = get_notifier()

    if not notifier.is_enabled:
        print("Primary Telegram bot not configured. Set TELEGRAM_BOT_TOKEN in .env")
        return

    # Simple message
    await notifier.send_message("Hello from NixClaw!")

    # Task lifecycle notifications
    await notifier.notify_task_started("task_001", "Analyze codebase")
    await notifier.notify_task_completed(
        "task_001", "Analyze codebase", "Found 42 Python files across 6 modules"
    )

    # Alert
    await notifier.notify_alert("Disk usage at 90%!")

    print("Primary bot messages sent!")


async def log_bot_example():
    """Send logs via the secondary log bot (uses requests, non-blocking)."""
    log_bot = get_log_bot()

    if not log_bot.is_enabled:
        print("Log bot not configured. Set TELEGRAM_BOT_TOKEN_LOG in .env")
        return

    # Tagged log messages
    log_bot.log("INFO", "Application started successfully")
    log_bot.log("DEBUG", "Loading configuration from .env")

    # Task lifecycle
    log_bot.task_started("task_001", "Build REST API")
    log_bot.task_output("task_001", "Step 1: Creating models...\nStep 2: Writing routes...")
    log_bot.task_completed("task_001", "Build REST API", "API created with 5 endpoints")

    # Agent events
    log_bot.agent_event("code_generator_1", "Generated 150 lines of Python code")
    log_bot.agent_event("analyzer_1", "Found 3 potential issues in the code")

    # Wait for background thread to send
    import time
    time.sleep(3)

    print("Log bot messages sent!")


async def human_in_the_loop_example():
    """Ask for user input via Telegram and wait for a response."""
    notifier = get_notifier()

    if not notifier.is_enabled:
        print("Telegram bot not configured")
        return

    # This sends a prompt to Telegram and waits for the user to reply
    # Requires the Telegram bot to be running (nixclaw --telegram)
    response = await notifier.wait_for_input(
        "Should I proceed with the database migration? (yes/no)",
        timeout=60,  # Wait 60 seconds for a response
    )

    if response:
        print(f"User responded: {response}")
    else:
        print("No response received (timeout or bot not running)")


if __name__ == "__main__":
    asyncio.run(primary_bot_example())
    asyncio.run(log_bot_example())
    # asyncio.run(human_in_the_loop_example())  # Uncomment to test
