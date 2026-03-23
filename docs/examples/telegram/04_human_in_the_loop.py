"""
Human-in-the-loop: Ask a question via Telegram and wait for a response.

IMPORTANT: The Telegram bot must be running for this to work.
    Terminal 1: nixclaw --telegram
    Terminal 2: python docs/examples/telegram/04_human_in_the_loop.py

The bot sends a prompt to your Telegram chat and waits for your reply.
"""
import asyncio

from nixclaw.integrations.telegram_bot import get_notifier


async def approval_workflow():
    """Ask for user approval before proceeding with a critical operation."""
    notifier = get_notifier()

    if not notifier.is_enabled:
        print("Telegram bot not configured")
        return

    # Ask for approval
    response = await notifier.wait_for_input(
        "A database migration is ready to run.\n\n"
        "This will:\n"
        "- Add 'email_verified' column to users table\n"
        "- Backfill existing users with email_verified=false\n\n"
        "Proceed? (yes/no)",
        timeout=120,
    )

    if response is None:
        print("No response received (timeout)")
        return

    if response.lower().strip() in ("yes", "y"):
        print("User approved! Running migration...")
        await notifier.send_message("Migration started...")
        # ... run migration here ...
        await notifier.send_message("Migration completed successfully!")
    else:
        print(f"User declined: {response}")
        await notifier.send_message("Migration cancelled.")


async def input_collection():
    """Collect structured input from the user."""
    notifier = get_notifier()

    if not notifier.is_enabled:
        print("Telegram bot not configured")
        return

    # Ask for a value
    response = await notifier.wait_for_input(
        "What priority should the next batch job run at?\n"
        "Options: high, normal, low",
        timeout=60,
    )

    if response:
        priority = response.strip().lower()
        if priority in ("high", "normal", "low"):
            print(f"Running batch job with priority: {priority}")
            await notifier.send_message(f"Batch job started with priority: {priority}")
        else:
            print(f"Invalid priority: {response}")
            await notifier.send_message(f"Invalid priority '{response}'. Using 'normal'.")
    else:
        print("No response, using default priority")


if __name__ == "__main__":
    print("Make sure the Telegram bot is running: nixclaw --telegram")
    print("Then check your Telegram for the prompt.\n")
    asyncio.run(approval_workflow())
