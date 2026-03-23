#!/usr/bin/env bash
# Example: Start the Telegram bot
# Requires TELEGRAM_BOT_TOKEN and TELEGRAM_USER_IDS in .env

# Start the bot (runs in foreground, Ctrl+C to stop)
nixclaw --telegram

# The bot responds to these commands in Telegram:
#   /start  — Welcome message
#   /help   — Show available commands
#   /task <description> — Submit a task
#   /status [task_id]   — Check task status or queue summary
#   /agents — Show active agents
