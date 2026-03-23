"""Telegram bot integration for human-in-the-loop and status notifications.

Supports:
- Sending task status updates (started, completed, failed)
- Receiving commands (/task, /status, /agents)
- Waiting for human input with timeout (ask-and-wait pattern)
- Rate limiting to avoid flooding
"""
from __future__ import annotations

import asyncio
import time
from collections import deque

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)

try:
    from telegram import Bot, Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )

    _HAS_TELEGRAM = True
except ImportError:
    _HAS_TELEGRAM = False
    logger.debug("python-telegram-bot not installed. Install with: pip install nixclaw[telegram]")


class TelegramNotifier:
    """Sends task status updates and alerts to Telegram.

    Also supports waiting for human input via a simple ask-and-wait pattern:
    the bot sends a prompt and waits for the next message from a whitelisted user.
    """

    def __init__(self) -> None:
        self._settings = get_settings().telegram
        self._token = self._settings.bot_token
        self._user_ids = self._settings.user_ids
        self._rate_limit = self._settings.message_rate_limit
        self._enabled = (
            _HAS_TELEGRAM
            and bool(self._token)
            and self._token != "your_bot_token_here"
        )

        # Rate limiting: track timestamps of recent sends
        self._send_times: deque[float] = deque(maxlen=self._rate_limit)

        # Human input: futures waiting for a response, keyed by user_id
        self._pending_input: dict[str, asyncio.Future[str]] = {}

        self._bot: Bot | None = None
        if self._enabled:
            self._bot = Bot(token=self._token)

        if not self._enabled:
            logger.info("Telegram notifier disabled (no valid bot token or library missing)")
        else:
            logger.info("Telegram notifier enabled for %d user(s)", len(self._user_ids))

    def _check_rate_limit(self) -> bool:
        """Return True if we're within rate limits."""
        now = time.monotonic()
        while self._send_times and now - self._send_times[0] > 60:
            self._send_times.popleft()
        return len(self._send_times) < self._rate_limit

    async def send_message(self, text: str, user_id: str | None = None) -> bool:
        """Send a message to a specific user or all whitelisted users."""
        if not self._enabled or not self._bot:
            logger.debug("Telegram disabled, skipping: %.80s", text)
            return False

        if not self._check_rate_limit():
            logger.warning("Telegram rate limit exceeded, dropping message")
            return False

        targets = [user_id] if user_id else self._user_ids
        sent = False

        for uid in targets:
            try:
                await self._bot.send_message(
                    chat_id=int(uid),
                    text=text[:4096],
                    parse_mode="HTML",
                )
                self._send_times.append(time.monotonic())
                sent = True
                logger.debug("Telegram message sent to %s", uid)
            except Exception as e:
                logger.error("Failed to send Telegram message to %s: %s", uid, e)

        return sent

    async def notify_task_started(self, task_id: str, title: str) -> None:
        await self.send_message(
            f"<b>Task Started</b>\n<b>Title:</b> {title}\n<b>ID:</b> <code>{task_id}</code>"
        )

    async def notify_task_completed(self, task_id: str, title: str, summary: str) -> None:
        await self.send_message(
            f"<b>Task Completed</b>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>ID:</b> <code>{task_id}</code>\n\n"
            f"<pre>{summary[:3000]}</pre>"
        )

    async def notify_task_failed(self, task_id: str, title: str, error: str) -> None:
        await self.send_message(
            f"<b>Task Failed</b>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>ID:</b> <code>{task_id}</code>\n"
            f"<b>Error:</b> {error[:500]}"
        )

    async def notify_alert(self, message: str) -> None:
        await self.send_message(f"<b>Alert:</b> {message}")

    async def wait_for_input(self, prompt: str, timeout: int = 300) -> str | None:
        """Send a prompt and wait for a reply from any whitelisted user."""
        if not self._enabled or not self._bot:
            logger.debug("Telegram disabled, cannot wait for input")
            return None

        await self.send_message(f"<b>Input Needed:</b>\n{prompt}")

        loop = asyncio.get_event_loop()
        future: asyncio.Future[str] = loop.create_future()

        for uid in self._user_ids:
            self._pending_input[uid] = future

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.info("Telegram input timed out after %ds", timeout)
            await self.send_message("<i>Input request timed out.</i>")
            return None
        finally:
            for uid in self._user_ids:
                self._pending_input.pop(uid, None)

    def resolve_input(self, user_id: str, text: str) -> bool:
        """Called when a message arrives from a user. Resolves pending input futures."""
        future = self._pending_input.pop(user_id, None)
        if future and not future.done():
            future.set_result(text)
            for uid in list(self._pending_input.keys()):
                if self._pending_input.get(uid) is future:
                    del self._pending_input[uid]
            return True
        return False

    @property
    def is_enabled(self) -> bool:
        return self._enabled


# ── Singleton ────────────────────────────────────────────────────────────────


_notifier_instance: TelegramNotifier | None = None


def get_notifier() -> TelegramNotifier:
    """Get the singleton TelegramNotifier instance."""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance


# ── Bot Command Handlers ────────────────────────────────────────────────────


async def _start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "NixClaw Agent Bot\n\n"
        "Commands:\n"
        "/task <description> - Submit a new task\n"
        "/status [task_id] - Check task status\n"
        "/agents - Show active agents\n"
        "/help - Show this help message"
    )


async def _help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _start_command(update, context)


async def _task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /task <task description>")
        return

    task_description = " ".join(context.args)
    await update.message.reply_text(f"Submitting task: {task_description}\nPlease wait...")

    try:
        from nixclaw.core.async_task_queue import get_task_queue

        queue = get_task_queue()
        task_id = await queue.submit(task_description)
        await update.message.reply_text(
            f"Task submitted!\nID: {task_id}\nUse /status {task_id} to check progress."
        )
    except Exception as e:
        await update.message.reply_text(f"Error submitting task: {e}")


async def _status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        from nixclaw.core.async_task_queue import get_task_queue

        queue = get_task_queue()

        if context.args:
            task_id = context.args[0]
            info = queue.get_task_info(task_id)
            if info:
                await update.message.reply_text(
                    f"Task: {info['title']}\nStatus: {info['status']}\nID: {task_id}"
                )
            else:
                await update.message.reply_text(f"Task not found: {task_id}")
        else:
            summary = queue.get_summary()
            text = "Task Queue Summary:\n"
            for status, count in summary.items():
                text += f"  {status}: {count}\n"
            await update.message.reply_text(text or "No tasks.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def _agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from nixclaw.agents.agent_factory import AgentFactory

    factory = AgentFactory.get_instance()
    status = factory.get_status()
    text = f"Agents: {status['total']} total\n"
    for s, count in status.get("by_status", {}).items():
        text += f"  {s}: {count}\n"
    await update.message.reply_text(text)


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    notifier = get_notifier()

    if notifier.resolve_input(user_id, update.message.text):
        await update.message.reply_text("Input received, processing...")
        return

    await update.message.reply_text(
        "Use /task <description> to submit a task, or /help for commands."
    )


def create_bot_application() -> Application | None:
    """Create and configure the Telegram bot application for polling."""
    if not _HAS_TELEGRAM:
        logger.warning("python-telegram-bot not installed")
        return None

    settings = get_settings().telegram
    token = settings.bot_token
    if not token or token == "your_bot_token_here":
        logger.info("Telegram bot token not configured")
        return None

    user_ids = [int(uid) for uid in settings.user_ids if uid.strip()]
    app = Application.builder().token(token).build()

    user_filter = filters.User(user_id=user_ids) if user_ids else filters.ALL

    app.add_handler(CommandHandler("start", _start_command, filters=user_filter))
    app.add_handler(CommandHandler("help", _help_command, filters=user_filter))
    app.add_handler(CommandHandler("task", _task_command, filters=user_filter))
    app.add_handler(CommandHandler("status", _status_command, filters=user_filter))
    app.add_handler(CommandHandler("agents", _agents_command, filters=user_filter))
    app.add_handler(MessageHandler(user_filter & filters.TEXT & ~filters.COMMAND, _handle_message))

    logger.info("Telegram bot application created (whitelisted users: %s)", user_ids)
    return app
