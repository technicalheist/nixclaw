"""
Register bot commands with Telegram so they appear in the command menu.

Run this once after creating your bot:
    python docs/examples/telegram/01_register_commands.py
"""
import asyncio

from telegram import Bot, BotCommand
from nixclaw.config import get_settings


async def register_primary_bot():
    """Register commands for the primary bot."""
    settings = get_settings()
    token = settings.telegram.bot_token

    if not token or token == "your_bot_token_here":
        print("Primary bot token not configured in .env")
        return

    bot = Bot(token=token)
    commands = [
        BotCommand("task", "Submit a new task"),
        BotCommand("status", "Check task status"),
        BotCommand("agents", "Show active agents"),
        BotCommand("help", "Show help message"),
        BotCommand("start", "Start the bot"),
    ]
    await bot.set_my_commands(commands)
    me = await bot.get_me()
    print(f"Primary bot commands registered: @{me.username}")


async def register_log_bot():
    """Register commands for the log bot (optional, it's mostly passive)."""
    settings = get_settings()
    token = settings.telegram.bot_token_log

    if not token or token in ("", "your_log_bot_token_here"):
        print("Log bot token not configured in .env")
        return

    bot = Bot(token=token)
    commands = [
        BotCommand("start", "Start receiving logs"),
    ]
    await bot.set_my_commands(commands)
    me = await bot.get_me()
    print(f"Log bot commands registered: @{me.username}")


async def main():
    await register_primary_bot()
    await register_log_bot()
    print("\nDone! Open your bots in Telegram and type '/' to see the command menu.")


if __name__ == "__main__":
    asyncio.run(main())
