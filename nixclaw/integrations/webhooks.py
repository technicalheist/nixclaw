"""Webhook callback handling for task completion notifications."""
from __future__ import annotations

import json

from nixclaw.logger import get_logger

logger = get_logger(__name__)

try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


class WebhookManager:
    """Manages webhook registrations and sends HTTP POST callbacks on task events."""

    def __init__(self) -> None:
        self._callbacks: dict[str, str] = {}  # task_id -> callback_url

    def register(self, task_id: str, callback_url: str) -> None:
        """Register a webhook URL for a task's completion callback."""
        self._callbacks[task_id] = callback_url
        logger.info("Registered webhook for task %s: %s", task_id, callback_url)

    async def notify(self, task_id: str, payload: dict) -> bool:
        """Send a webhook POST callback for a task. Returns True if sent successfully."""
        url = self._callbacks.get(task_id)
        if not url:
            return False

        if not _HAS_HTTPX:
            logger.warning("httpx not installed, cannot send webhook")
            return False

        payload["task_id"] = task_id

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code < 400:
                    logger.info("Webhook sent: %s -> %s (status=%d)", task_id, url, response.status_code)
                    return True
                else:
                    logger.warning(
                        "Webhook failed: %s -> %s (status=%d)",
                        task_id, url, response.status_code,
                    )
                    return False
        except Exception as e:
            logger.error("Webhook error for %s -> %s: %s", task_id, url, e)
            return False
