from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone

from nixclaw.config import get_settings
from nixclaw.logger import get_logger
from nixclaw.storage.models import Task, TaskStatus, TaskType

logger = get_logger(__name__)


class TaskManager:
    """Task tracking with in-memory state and optional database persistence.

    Tracks all tasks in a flat dict keyed by task ID.
    Supports hierarchical task trees via parent_task_id references.
    When persistence is enabled, tasks are saved to SQLite via a
    dedicated background thread to avoid async event loop issues.
    """

    def __init__(self, persist: bool | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        settings = get_settings()
        self._persist = persist if persist is not None else settings.system.task_persistence_enabled
        self._db_initialized = False
        self._db_lock = threading.Lock()

    def _save_task_sync(self, task: Task) -> None:
        """Persist a task to the database in a background thread."""
        if not self._persist:
            return

        def _do_save() -> None:
            try:
                import asyncio as _aio
                loop = _aio.new_event_loop()
                loop.run_until_complete(self._save_task_async(task))
                loop.close()
            except Exception as e:
                logger.warning("Failed to persist task %s: %s", task.id, e)

        thread = threading.Thread(target=_do_save, daemon=True)
        thread.start()

    async def _save_task_async(self, task: Task) -> None:
        """Actual async save — runs in its own event loop via background thread."""
        with self._db_lock:
            if not self._db_initialized:
                try:
                    from nixclaw.storage.database import Database
                    db = Database.get_instance()
                    await db.init_tables()
                    self._db_initialized = True
                except Exception as e:
                    logger.warning("Database init failed, disabling persistence: %s", e)
                    self._persist = False
                    return

        from nixclaw.storage.database import Database
        from nixclaw.storage.repository import TaskRepository
        db = Database.get_instance()
        async with db.session() as session:
            repo = TaskRepository(session)
            await repo.save(task)

    def create_task(
        self,
        title: str,
        description: str = "",
        type: TaskType = TaskType.GENERAL,
        parent_task_id: str | None = None,
        priority: int = 5,
        required_tools: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> Task:
        """Create and register a new task."""
        task = Task(
            title=title,
            description=description,
            type=type,
            parent_task_id=parent_task_id,
            priority=priority,
            required_tools=required_tools or [],
            dependencies=dependencies or [],
        )
        self._tasks[task.id] = task

        if parent_task_id and parent_task_id in self._tasks:
            self._tasks[parent_task_id].subtasks.append(task)

        logger.info("Created task: %s (id=%s, parent=%s)", title, task.id, parent_task_id)
        self._save_task_sync(task)
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        task = self._tasks.get(task_id)
        if not task:
            logger.warning("Task not found: %s", task_id)
            return
        task.status = status
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
        logger.debug("Task %s status -> %s", task_id, status.value)
        self._save_task_sync(task)

    def assign_agent(self, task_id: str, agent_id: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.assigned_agent_id = agent_id
            logger.debug("Task %s assigned to agent %s", task_id, agent_id)

    def set_result(self, task_id: str, result: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.result = result
            self._save_task_sync(task)

    def set_error(self, task_id: str, error: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.error = error
            task.status = TaskStatus.FAILED
            self._save_task_sync(task)

    def get_pending_tasks(self) -> list[Task]:
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        return sorted(pending, key=lambda t: t.priority)

    def get_runnable_tasks(self) -> list[Task]:
        completed_ids = {
            t.id for t in self._tasks.values() if t.status == TaskStatus.COMPLETED
        }
        runnable = []
        for task in self.get_pending_tasks():
            if all(dep_id in completed_ids for dep_id in task.dependencies):
                runnable.append(task)
        return runnable

    def get_subtasks(self, parent_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.parent_task_id == parent_id]

    def get_all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for task in self._tasks.values():
            status = task.status.value
            summary[status] = summary.get(status, 0) + 1
        return summary

    async def load_from_db(self) -> int:
        """Load all tasks from database into memory. Returns count loaded."""
        if not self._persist:
            return 0
        try:
            from nixclaw.storage.database import Database
            from nixclaw.storage.repository import TaskRepository
            db = Database.get_instance()
            await db.init_tables()
            self._db_initialized = True
            async with db.session() as session:
                repo = TaskRepository(session)
                tasks = await repo.get_all()
                for task in tasks:
                    self._tasks[task.id] = task
                logger.info("Loaded %d tasks from database", len(tasks))
                return len(tasks)
        except Exception as e:
            logger.warning("Failed to load tasks from database: %s", e)
            return 0
