"""
Send detailed logs to the secondary log bot.

The log bot uses the `requests` package in a background thread,
so it never blocks your main application. It automatically batches
rapid messages to avoid Telegram rate limits.
"""
import time

from nixclaw.integrations.telegram_log import get_log_bot


def main():
    bot = get_log_bot()

    if not bot.is_enabled:
        print("Log bot not configured. Set TELEGRAM_BOT_TOKEN_LOG in .env")
        return

    # Tagged log messages
    bot.log("INFO", "Application started")
    bot.log("DEBUG", "Configuration loaded from .env")
    bot.log("WARNING", "Redis not available, using in-memory cache")

    # Task lifecycle events
    bot.task_started("task_001", "Build REST API")
    bot.task_output("task_001", (
        "Step 1: Creating data models...\n"
        "Step 2: Writing API routes...\n"
        "Step 3: Adding authentication...\n"
        "Step 4: Writing tests..."
    ))
    bot.task_completed("task_001", "Build REST API", "API created with 5 endpoints, all tests passing")

    # Agent events
    bot.agent_event("code_generator_1", "Generated 150 lines of Python code")
    bot.agent_event("analyzer_1", "Code review: 2 issues found\n- Missing input validation\n- No rate limiting")

    # Error logging
    bot.task_failed("task_002", "Database migration", "IntegrityError: duplicate key in users table")

    # Wait for background thread to send
    time.sleep(5)
    print("Log messages sent! Check your log bot in Telegram.")


if __name__ == "__main__":
    main()
