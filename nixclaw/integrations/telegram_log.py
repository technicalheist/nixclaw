"""Secondary Telegram bot for logging — mirrors all output to a dedicated log channel.

Uses the `requests` package (synchronous) in a background thread to avoid
blocking the main async loop. This bot captures everything the user sees
in terminal or primary Telegram bot:
- Task started / completed / failed
- Agent output and tool call results
- Orchestrator decisions
- Errors and warnings

Configure via TELEGRAM_BOT_TOKEN_LOG and TELEGRAM_USER_IDS in .env.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Any

import requests

from nixclaw.config import get_settings

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
_MAX_MESSAGE_LEN = 4096


class TelegramLogBot:
    """Sends log messages to a dedicated Telegram bot using `requests`.

    Runs sends in a background thread to never block the caller.
    Buffers rapid messages and batches them to respect rate limits.
    """

    _instance: TelegramLogBot | None = None

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.telegram.bot_token_log
        self._user_ids = settings.telegram.user_ids
        self._enabled = bool(self._token and self._token not in ("", "your_log_bot_token_here"))

        self._url = _TELEGRAM_API.format(token=self._token) if self._enabled else ""

        # Background queue
        self._queue: deque[str] = deque(maxlen=500)
        self._lock = threading.Lock()
        self._running = False

        if self._enabled:
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    @classmethod
    def get_instance(cls) -> TelegramLogBot:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def send(self, message: str) -> None:
        """Queue a message for sending. Non-blocking."""
        if not self._enabled:
            return
        with self._lock:
            self._queue.append(message)

    def log(self, tag: str, message: str) -> None:
        """Send a tagged log message."""
        self.send(f"<b>[{tag}]</b>\n{message}")

    def task_started(self, task_id: str, title: str) -> None:
        self.send(
            f"<b>[TASK STARTED]</b>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>ID:</b> <code>{task_id}</code>"
        )

    def task_output(self, task_id: str, output: str) -> None:
        # Truncate long output but keep it readable
        if len(output) > 3500:
            output = output[:3500] + "\n... (truncated)"
        self.send(
            f"<b>[TASK OUTPUT]</b>\n"
            f"<b>ID:</b> <code>{task_id}</code>\n"
            f"<pre>{self._escape_html(output)}</pre>"
        )

    def task_completed(self, task_id: str, title: str, result: str) -> None:
        if len(result) > 3000:
            result = result[:3000] + "\n... (truncated)"
        self.send(
            f"<b>[TASK COMPLETED]</b>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>ID:</b> <code>{task_id}</code>\n"
            f"<pre>{self._escape_html(result)}</pre>"
        )

    def task_failed(self, task_id: str, title: str, error: str) -> None:
        self.send(
            f"<b>[TASK FAILED]</b>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>ID:</b> <code>{task_id}</code>\n"
            f"<b>Error:</b> {self._escape_html(error[:1000])}"
        )

    def agent_event(self, agent_name: str, event: str) -> None:
        self.send(
            f"<b>[AGENT]</b> {agent_name}\n{self._escape_html(event[:3000])}"
        )

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _worker(self) -> None:
        """Background thread that drains the queue, batching rapid messages."""
        while self._running:
            # Collect all queued messages
            batch: list[str] = []
            with self._lock:
                while self._queue and len(batch) < 20:
                    batch.append(self._queue.popleft())

            if batch:
                # Combine small messages into a single Telegram message
                combined = ""
                for msg in batch:
                    candidate = (combined + "\n\n" + msg).strip() if combined else msg
                    if len(candidate) > _MAX_MESSAGE_LEN - 50:
                        # Send what we have, start new message
                        self._send_sync(combined)
                        combined = msg
                        time.sleep(1)  # 1 sec between sends to respect rate limits
                    else:
                        combined = candidate
                if combined:
                    self._send_sync(combined)
                time.sleep(1)  # Wait after each batch
            else:
                time.sleep(0.5)

    def _send_sync(self, text: str) -> None:
        """Send a single message to all whitelisted users via requests."""
        # Truncate to Telegram's limit
        if len(text) > _MAX_MESSAGE_LEN:
            text = text[:_MAX_MESSAGE_LEN - 20] + "\n... (truncated)"

        for uid in self._user_ids:
            try:
                requests.post(
                    self._url,
                    json={
                        "chat_id": int(uid),
                        "text": text,
                        "parse_mode": "HTML",
                    },
                    timeout=10,
                )
            except Exception:
                pass  # Log bot should never crash the main app

    def shutdown(self) -> None:
        """Drain remaining messages and stop the worker."""
        self._running = False
        # Drain remaining
        while self._queue:
            msg = self._queue.popleft()
            self._send_sync(msg)

    @property
    def is_enabled(self) -> bool:
        return self._enabled


# ── Logging Handler ──────────────────────────────────────────────────────────


class TelegramLogHandler(logging.Handler):
    """Python logging handler that forwards log records to the Telegram log bot.

    Attach to any logger to mirror its output to Telegram.
    Only forwards WARNING+ by default (configurable via setLevel).
    """

    def __init__(self, level: int = logging.WARNING) -> None:
        super().__init__(level)
        self._bot = TelegramLogBot.get_instance()

    def emit(self, record: logging.LogRecord) -> None:
        if not self._bot.is_enabled:
            return
        try:
            msg = self.format(record)
            tag = record.levelname
            self._bot.log(tag, msg[:3000])
        except Exception:
            pass


def get_log_bot() -> TelegramLogBot:
    """Get the singleton log bot instance."""
    return TelegramLogBot.get_instance()
