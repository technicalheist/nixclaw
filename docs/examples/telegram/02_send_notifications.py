"""
Send notifications via the primary Telegram bot from your code.

Use this in your own scripts to notify yourself about task progress,
errors, or anything else.
"""
import asyncio

from nixclaw.integrations.telegram_bot import get_notifier


async def main():
    notifier = get_notifier()

    if not notifier.is_enabled:
        print("Telegram bot not configured. Set TELEGRAM_BOT_TOKEN in .env")
        return

    # Simple text message
    await notifier.send_message("Hello from NixClaw!")

    # Task notifications
    await notifier.notify_task_started("demo_001", "Analyze project")
    await notifier.notify_task_completed(
        "demo_001",
        "Analyze project",
        "Found 42 Python files across 6 modules.\n"
        "Total lines: 5,946\n"
        "Test coverage: 97 tests passing",
    )

    # Error notification
    await notifier.notify_task_failed(
        "demo_002",
        "Deploy to production",
        "ConnectionError: Could not reach deployment server",
    )

    # Generic alert
    await notifier.notify_alert("Disk usage at 92% on /dev/sda1")

    print("All notifications sent! Check your Telegram bot.")


if __name__ == "__main__":
    asyncio.run(main())
