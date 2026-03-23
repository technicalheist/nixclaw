# Telegram Examples

NixClaw supports two Telegram bots:

| Bot | Env Variable | Purpose |
|-----|-------------|---------|
| **Primary Bot** | `TELEGRAM_BOT_TOKEN` | User interaction — submit tasks, check status, receive notifications |
| **Log Bot** | `TELEGRAM_BOT_TOKEN_LOG` | Logging — mirrors all output from CLI, API, and Telegram |

## Setup

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram and create two bots
2. Get your user ID from [@userinfobot](https://t.me/userinfobot)
3. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_primary_bot_token
   TELEGRAM_BOT_TOKEN_LOG=your_log_bot_token
   TELEGRAM_USER_IDS=your_user_id
   ```
4. Start a chat with both bots (press Start)
5. Register commands: `python docs/examples/telegram/01_register_commands.py`
6. Start the bot: `nixclaw --telegram`

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show available commands |
| `/task <description>` | Submit a new task |
| `/status [task_id]` | Check task status or queue summary |
| `/agents` | Show active agents |
