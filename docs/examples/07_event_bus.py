"""
Example 07: Event Bus — Decouple components with async pub/sub.

The EventBus allows components to communicate without direct references.
Subscribe to events and get notified when they're published.
"""
import asyncio
from typing import Any

from nixclaw import EventBus
from nixclaw.core.event_bus import (
    TASK_STARTED,
    TASK_COMPLETED,
    TASK_FAILED,
    SYSTEM_ALERT,
)


# Define event handlers
async def on_task_started(data: dict[str, Any]) -> None:
    print(f"[Handler] Task started: {data.get('title', 'unknown')}")


async def on_task_completed(data: dict[str, Any]) -> None:
    print(f"[Handler] Task completed: {data.get('task_id')} - {data.get('result', '')[:50]}")


async def on_task_failed(data: dict[str, Any]) -> None:
    print(f"[Handler] Task FAILED: {data.get('task_id')} - {data.get('error')}")


async def on_alert(data: dict[str, Any]) -> None:
    print(f"[ALERT] {data.get('message')}")


async def main():
    bus = EventBus.get_instance()

    # Subscribe handlers to events
    bus.subscribe(TASK_STARTED, on_task_started)
    bus.subscribe(TASK_COMPLETED, on_task_completed)
    bus.subscribe(TASK_FAILED, on_task_failed)
    bus.subscribe(SYSTEM_ALERT, on_alert)

    # Publish events (simulating what the orchestrator does)
    await bus.publish(TASK_STARTED, {"title": "Analyze codebase", "task_id": "abc123"})
    await bus.publish(TASK_COMPLETED, {"task_id": "abc123", "result": "Found 42 files"})
    await bus.publish(SYSTEM_ALERT, {"message": "Memory usage at 85%"})
    await bus.publish(TASK_FAILED, {"task_id": "def456", "error": "LLM timeout"})

    # Unsubscribe
    bus.unsubscribe(TASK_STARTED, on_task_started)

    # This won't trigger the handler anymore
    await bus.publish(TASK_STARTED, {"title": "This won't print"})

    EventBus.reset()


if __name__ == "__main__":
    asyncio.run(main())
