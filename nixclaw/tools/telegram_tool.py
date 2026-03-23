"""Telegram tools for agent use - human-in-the-loop via Telegram.

These tools are registered with agents to enable them to request
human input and send notifications through Telegram.
"""
from __future__ import annotations

from nixclaw.integrations.telegram_bot import get_notifier
from nixclaw.logger import get_logger

logger = get_logger(__name__)


async def send_telegram_notification(message: str) -> str:
    """Send a notification message to Telegram."""
    notifier = get_notifier()
    sent = await notifier.send_message(message)
    if sent:
        return "Notification sent successfully"
    return "Telegram not configured or message not sent"


async def wait_for_human_input(
    prompt: str, timeout: int = 300, expected_format: str = ""
) -> str:
    """Wait for user input from Telegram with timeout.

    Args:
        prompt: What to ask the user.
        timeout: Seconds to wait before timing out.
        expected_format: Guidance on expected input format.

    Returns:
        The user's response, or a timeout message.
    """
    notifier = get_notifier()
    full_prompt = prompt
    if expected_format:
        full_prompt += f"\n(Expected format: {expected_format})"

    response = await notifier.wait_for_input(full_prompt, timeout)
    if response is None:
        return f"No response received within {timeout}s (Telegram may not be configured)"
    return response
