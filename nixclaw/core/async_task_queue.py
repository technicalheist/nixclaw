"""Async task queue for background task execution.

Supports:
- Fire-and-forget task submission (returns task_id immediately)
- Status polling by task_id
- Webhook callbacks on completion
- Telegram notifications on status changes
- Concurrent task execution with limits
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from nixclaw.config import get_settings
from nixclaw.core.task_manager import TaskManager
from nixclaw.logger import get_logger
from nixclaw.storage.models import Task, TaskStatus, TaskType

logger = get_logger(__name__)


class AsyncTaskQueue:
    """Background task execution queue.

    Tasks are submitted and run asynchronously. Callers get a task_id
    immediately and can poll for status or register callbacks.
    """

    _instance: AsyncTaskQueue | None = None

    def __init__(self) -> None:
        settings = get_settings()
        self._max_concurrent = settings.agent.max_concurrent_agents
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._task_manager = TaskManager(persist=True)
        self._running: dict[str, asyncio.Task] = {}
        self._results: dict[str, str] = {}
        self._callbacks: dict[str, str] = {}  # task_id -> webhook_url

    @classmethod
    def get_instance(cls) -> AsyncTaskQueue:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    async def submit(
        self,
        task_description: str,
        priority: str = "normal",
        agent_profiles: list[str] | None = None,
        callback_url: str | None = None,
    ) -> str:
        """Submit a task for background execution. Returns task_id immediately."""
        priority_int = {"high": 1, "normal": 5, "low": 9}.get(priority, 5)

        task = self._task_manager.create_task(
            title=task_description[:100],
            description=task_description,
            type=TaskType.GENERAL,
            priority=priority_int,
        )

        if callback_url:
            self._callbacks[task.id] = callback_url

        # Launch background execution
        bg_task = asyncio.create_task(
            self._execute(task.id, task_description, agent_profiles)
        )
        self._running[task.id] = bg_task

        logger.info("Task queued: %s (id=%s)", task.title, task.id)
        return task.id

    async def _execute(
        self,
        task_id: str,
        description: str,
        agent_profiles: list[str] | None,
    ) -> None:
        """Execute a task with concurrency limiting and notifications."""
        async with self._semaphore:
            self._task_manager.update_status(task_id, TaskStatus.IN_PROGRESS)
            task = self._task_manager.get_task(task_id)

            # Send Telegram notification
            await self._notify_started(task)

            try:
                from nixclaw.agents.orchestrator import Orchestrator

                orchestrator = Orchestrator()
                try:
                    if agent_profiles:
                        result = await orchestrator.run_with_team(description, agent_profiles)
                    else:
                        result = await orchestrator.run(description)

                    self._results[task_id] = result
                    self._task_manager.update_status(task_id, TaskStatus.COMPLETED)
                    self._task_manager.set_result(task_id, result)

                    await self._notify_completed(task, result)
                    await self._send_webhook(task_id, "completed", result)

                    logger.info("Background task completed: %s", task_id)
                finally:
                    await orchestrator.close()

            except Exception as e:
                error_msg = str(e)
                self._task_manager.set_error(task_id, error_msg)
                self._results[task_id] = f"Error: {error_msg}"

                await self._notify_failed(task, error_msg)
                await self._send_webhook(task_id, "failed", error_msg)

                logger.exception("Background task failed: %s", task_id)
            finally:
                self._running.pop(task_id, None)

    def get_task_info(self, task_id: str) -> dict[str, Any] | None:
        """Get task status and info."""
        task = self._task_manager.get_task(task_id)
        if not task:
            return None

        info = {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

        if task.status == TaskStatus.COMPLETED:
            info["result"] = self._results.get(task_id, task.result)
        elif task.status == TaskStatus.FAILED:
            info["error"] = task.error

        return info

    def get_result(self, task_id: str) -> str | None:
        """Get the result of a completed task."""
        return self._results.get(task_id)

    def get_summary(self) -> dict[str, int]:
        return self._task_manager.get_summary()

    def get_all_tasks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in self._task_manager.get_all_tasks()
        ]

    async def cancel(self, task_id: str) -> bool:
        """Cancel a running task."""
        bg_task = self._running.get(task_id)
        if bg_task and not bg_task.done():
            bg_task.cancel()
            self._task_manager.update_status(task_id, TaskStatus.FAILED)
            self._task_manager.set_error(task_id, "Cancelled by user")
            self._running.pop(task_id, None)
            logger.info("Task cancelled: %s", task_id)
            return True
        return False

    async def _notify_started(self, task: Task | None) -> None:
        if not task:
            return
        try:
            from nixclaw.integrations.telegram_bot import get_notifier
            notifier = get_notifier()
            await notifier.notify_task_started(task.id, task.title)
        except Exception:
            pass

    async def _notify_completed(self, task: Task | None, result: str) -> None:
        if not task:
            return
        try:
            from nixclaw.integrations.telegram_bot import get_notifier
            notifier = get_notifier()
            await notifier.notify_task_completed(task.id, task.title, result[:500])
        except Exception:
            pass

    async def _notify_failed(self, task: Task | None, error: str) -> None:
        if not task:
            return
        try:
            from nixclaw.integrations.telegram_bot import get_notifier
            notifier = get_notifier()
            await notifier.notify_task_failed(task.id, task.title, error)
        except Exception:
            pass

    async def _send_webhook(self, task_id: str, status: str, data: str) -> None:
        url = self._callbacks.get(task_id)
        if not url:
            return
        try:
            from nixclaw.integrations.webhooks import WebhookManager
            wh = WebhookManager()
            await wh.notify(task_id, {"status": status, "result": data[:2000]})
        except Exception as e:
            logger.warning("Webhook callback failed for %s: %s", task_id, e)


def get_task_queue() -> AsyncTaskQueue:
    """Get the singleton task queue."""
    return AsyncTaskQueue.get_instance()
