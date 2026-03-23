from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Awaitable

from nixclaw.logger import get_logger

logger = get_logger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    """Simple async event bus for decoupled component communication.

    Components publish events by topic. Subscribers receive events
    asynchronously. Used for task updates, agent status changes,
    and notification triggers (e.g., Telegram alerts).
    """

    _instance: EventBus | None = None

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    @classmethod
    def get_instance(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed to '%s': %s", event_type, handler.__name__)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Publish an event to all subscribers."""
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return

        event_data = data or {}
        event_data["event_type"] = event_type

        logger.debug("Publishing '%s' to %d handlers", event_type, len(handlers))

        tasks = [handler(event_data) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Event handler error for '%s': %s",
                    event_type,
                    result,
                )


# Standard event types
TASK_STARTED = "task_started"
TASK_PROGRESS = "task_progress"
TASK_COMPLETED = "task_completed"
TASK_FAILED = "task_failed"
COMMAND_ALERT = "command_alert"
HUMAN_INPUT_NEEDED = "human_input_needed"
SYSTEM_ALERT = "system_alert"
AGENT_CREATED = "agent_created"
AGENT_TERMINATED = "agent_terminated"
